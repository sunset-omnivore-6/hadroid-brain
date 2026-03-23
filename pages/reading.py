import streamlit as st
from components.github_storage import ensure_data_loaded, save_and_sync
from components.data_helpers import new_id, today
from components.theme import page_header, coloured_divider, TILE_COLOURS, BG_SECONDARY

COLOUR = TILE_COLOURS["reading"]
STAR = "\u2B50"

STATUS_OPTIONS = ["want_to_read", "reading", "finished", "abandoned"]
STATUS_LABELS = {
    "want_to_read": "Want to Read",
    "reading": "Currently Reading",
    "finished": "Finished",
    "abandoned": "Abandoned",
}


def main():
    ensure_data_loaded()
    data = st.session_state["user_data"]
    reading_data = data.get("reading", {})
    books = reading_data.get("books", [])

    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("\u2190 Back to Home", key="back_reading"):
        st.switch_page("pages/home.py")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(page_header("Reading", COLOUR), unsafe_allow_html=True)
    st.markdown(coloured_divider(COLOUR), unsafe_allow_html=True)

    tab_reading, tab_want, tab_finished, tab_ai = st.tabs(
        ["Currently Reading", "Want to Read", "Finished", "AI Recommendations"]
    )

    with tab_reading:
        _render_book_list(data, books, "reading")
    with tab_want:
        _render_book_list(data, books, "want_to_read")
    with tab_finished:
        _render_book_list(data, books, "finished")
    with tab_ai:
        _render_ai_recommendations(data, books)

    st.markdown("---")
    _render_add_book(data)


def _render_book_list(data, books, status):
    filtered = [b for b in books if b.get("status") == status]

    if not filtered:
        label = STATUS_LABELS.get(status, status)
        st.info(f"No books in '{label}'. Add one below!")
        return

    for book in filtered:
        col_main, col_actions = st.columns([5, 1])

        with col_main:
            rating_str = ""
            if book.get("rating"):
                rating_str = f" {STAR * book['rating']}"
            st.markdown(
                f'<div style="background:{BG_SECONDARY};border-radius:8px;padding:14px;margin-bottom:8px;'
                f'border-left:4px solid {COLOUR};">'
                f'<strong style="font-size:16px;">{book.get("title", "")}</strong>{rating_str}'
                f'<br><span style="font-size:13px;color:#aaa;">by {book.get("author", "Unknown")}</span>'
                f'{"<br><span style=font-size:12px;color:#888;>" + book.get("review", "") + "</span>" if book.get("review") else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_actions:
            # Status change
            current_idx = STATUS_OPTIONS.index(book.get("status", "want_to_read"))
            new_status = st.selectbox(
                "Move to",
                STATUS_OPTIONS,
                index=current_idx,
                format_func=lambda x: STATUS_LABELS.get(x, x),
                key=f"book_status_{book['id']}",
                label_visibility="collapsed",
            )
            if new_status != book.get("status"):
                book["status"] = new_status
                if new_status == "finished" and not book.get("date_finished"):
                    book["date_finished"] = today()
                save_and_sync()
                st.rerun()

            if st.button("\U0001F5D1", key=f"del_book_{book['id']}", help="Delete"):
                data["reading"]["books"] = [b for b in books if b["id"] != book["id"]]
                save_and_sync()
                st.rerun()

    # Rating for finished books
    if status == "finished":
        st.markdown("---")
        st.markdown("##### Rate Your Books")
        for book in filtered:
            cols = st.columns([3, 2, 2])
            with cols[0]:
                st.markdown(f"**{book.get('title', '')}**")
            with cols[1]:
                rating = st.slider(
                    "Rating",
                    min_value=0, max_value=5,
                    value=book.get("rating", 0),
                    key=f"rate_{book['id']}",
                    label_visibility="collapsed",
                )
                if rating != book.get("rating", 0):
                    book["rating"] = rating
                    save_and_sync()
            with cols[2]:
                review = st.text_input(
                    "Short review",
                    value=book.get("review", ""),
                    key=f"review_{book['id']}",
                    label_visibility="collapsed",
                    placeholder="Quick thoughts...",
                )
                if review != book.get("review", ""):
                    book["review"] = review
                    save_and_sync()


def _render_add_book(data):
    st.markdown("##### Add a Book")
    with st.form("add_book", clear_on_submit=True):
        cols = st.columns([3, 2, 1])
        with cols[0]:
            title = st.text_input("Title", placeholder="e.g. Thinking, Fast and Slow")
        with cols[1]:
            author = st.text_input("Author", placeholder="e.g. Daniel Kahneman")
        with cols[2]:
            status = st.selectbox("Status", STATUS_OPTIONS, format_func=lambda x: STATUS_LABELS.get(x, x))

        if st.form_submit_button("Add Book", use_container_width=True, type="primary"):
            if not title.strip():
                st.error("Please enter a book title.")
            else:
                book = {
                    "id": new_id(),
                    "title": title.strip(),
                    "author": author.strip(),
                    "status": status,
                    "rating": 0,
                    "review": "",
                    "date_added": today(),
                    "date_finished": None,
                }
                data["reading"]["books"].append(book)
                if save_and_sync():
                    st.success(f"'{title}' added!")
                    st.rerun()


def _build_recommendation_prompt(books):
    lines = ["Here is my reading history:\n"]
    for book in books:
        rating_str = f" (rated {book['rating']}/5)" if book.get("rating") else ""
        status_str = STATUS_LABELS.get(book.get("status", ""), "")
        review_str = f' — "{book["review"]}"' if book.get("review") else ""
        lines.append(f'- "{book.get("title", "")}" by {book.get("author", "Unknown")} [{status_str}]{rating_str}{review_str}')

    lines.append(
        "\n\nBased on my reading history, please suggest 3-5 books I might enjoy. "
        "For each suggestion, provide:\n"
        "1. **Title** and **Author**\n"
        "2. A one-sentence reason why I'd enjoy it based on my reading patterns.\n\n"
        "Format each recommendation on its own line starting with a number."
    )
    return "\n".join(lines)


def _render_ai_recommendations(data, books):
    st.markdown("##### AI Book Recommendations")
    st.caption("Powered by Claude — analyses your reading history to suggest books you'll love.")

    if not books:
        st.info("Add some books to your library first, then get personalised recommendations!")
        return

    if st.button("Get Recommendations", type="primary", use_container_width=True, key="get_recs"):
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            prompt = _build_recommendation_prompt(books)

            with st.spinner("Thinking about what you'd enjoy..."):
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                response = message.content[0].text

            st.session_state["ai_recommendations"] = response
        except KeyError:
            st.error("Anthropic API key not configured. Add ANTHROPIC_API_KEY to your Streamlit secrets.")
        except Exception as e:
            st.error(f"Failed to get recommendations: {e}")

    # Display recommendations
    if "ai_recommendations" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["ai_recommendations"])

        st.markdown("---")
        st.caption("Want to add any of these to your reading list? Use the 'Add a Book' form below.")


main()
