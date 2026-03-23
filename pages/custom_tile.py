import streamlit as st
from components.github_storage import ensure_data_loaded, save_and_sync
from components.data_helpers import new_id, today
from components.theme import page_header, coloured_divider, BG_SECONDARY, EXTRA_COLOURS
import plotly.graph_objects as go
from components.theme import BG_PRIMARY, TEXT_PRIMARY


def main():
    ensure_data_loaded()
    data = st.session_state["user_data"]
    custom_tiles = data.get("custom_tiles", [])

    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("\u2190 Back to Home", key="back_custom"):
        st.switch_page("pages/home.py")
    st.markdown('</div>', unsafe_allow_html=True)

    # Check if creating a new tile or viewing an existing one
    if st.session_state.get("show_add_tile"):
        _render_create_tile(data)
        return

    tile_id = st.session_state.get("selected_custom_tile")
    if tile_id:
        tile = next((t for t in custom_tiles if t.get("id") == tile_id), None)
        if tile:
            _render_custom_tile(data, tile)
            return

    # If we have custom tiles but none selected, show a picker or go to first
    if custom_tiles:
        st.markdown(page_header("Custom Tiles"), unsafe_allow_html=True)
        for ct in custom_tiles:
            if st.button(f"{ct.get('name', 'Untitled')}", key=f"pick_ct_{ct['id']}", use_container_width=True):
                st.session_state["selected_custom_tile"] = ct["id"]
                st.rerun()
    else:
        _render_create_tile(data)


def _render_create_tile(data):
    st.markdown(page_header("Create New Tile"), unsafe_allow_html=True)

    with st.form("create_custom_tile", clear_on_submit=True):
        name = st.text_input("Tile Name", placeholder="e.g. Habits, Budget, Journal")
        cols = st.columns(2)
        with cols[0]:
            tile_type = st.selectbox("Tile Type", ["checklist", "journal", "tracker"],
                                     format_func=lambda x: {"checklist": "Checklist", "journal": "Journal / Log", "tracker": "Numeric Tracker"}[x])
        with cols[1]:
            colour = st.color_picker("Tile Colour", value=EXTRA_COLOURS[len(data.get("custom_tiles", [])) % len(EXTRA_COLOURS)])

        if st.form_submit_button("Create Tile", use_container_width=True, type="primary"):
            if not name.strip():
                st.error("Please enter a tile name.")
            else:
                tile = {
                    "id": new_id(),
                    "name": name.strip(),
                    "type": tile_type,
                    "colour": colour,
                    "items": [],
                    "entries": [],
                }
                data.setdefault("custom_tiles", []).append(tile)

                # Add to tile_settings.custom
                data.setdefault("tile_settings", {}).setdefault("custom", []).append(tile["id"])

                if save_and_sync():
                    st.session_state.pop("show_add_tile", None)
                    st.session_state["selected_custom_tile"] = tile["id"]
                    st.success(f"Tile '{name}' created!")
                    st.rerun()


def _render_custom_tile(data, tile):
    colour = tile.get("colour", "#444")
    st.markdown(page_header(tile.get("name", "Custom Tile"), colour), unsafe_allow_html=True)
    st.markdown(coloured_divider(colour), unsafe_allow_html=True)

    tile_type = tile.get("type", "checklist")

    if tile_type == "checklist":
        _render_checklist(data, tile)
    elif tile_type == "journal":
        _render_journal(data, tile)
    elif tile_type == "tracker":
        _render_tracker(data, tile)

    st.markdown("---")
    if st.button("Delete This Tile", key=f"del_tile_{tile['id']}", type="secondary"):
        data["custom_tiles"] = [t for t in data.get("custom_tiles", []) if t["id"] != tile["id"]]
        custom_ids = data.get("tile_settings", {}).get("custom", [])
        if tile["id"] in custom_ids:
            custom_ids.remove(tile["id"])
        st.session_state.pop("selected_custom_tile", None)
        save_and_sync()
        st.rerun()


# --- CHECKLIST ---
def _render_checklist(data, tile):
    items = tile.get("items", [])

    if items:
        done_count = sum(1 for i in items if i.get("done"))
        st.progress(done_count / len(items), text=f"{done_count}/{len(items)} complete")

    for item in items:
        cols = st.columns([0.5, 5, 0.5])
        with cols[0]:
            done = st.checkbox("", value=item.get("done", False), key=f"cl_{item['id']}")
            if done != item.get("done", False):
                item["done"] = done
                save_and_sync()
                st.rerun()
        with cols[1]:
            style = "text-decoration: line-through; color: #666;" if item.get("done") else ""
            st.markdown(f'<span style="{style}">{item.get("text", "")}</span>', unsafe_allow_html=True)
        with cols[2]:
            if st.button("\U0001F5D1", key=f"del_cl_{item['id']}"):
                tile["items"] = [i for i in items if i["id"] != item["id"]]
                save_and_sync()
                st.rerun()

    with st.form(f"add_checklist_{tile['id']}", clear_on_submit=True):
        text = st.text_input("New item", placeholder="Add a checklist item...", label_visibility="collapsed")
        if st.form_submit_button("Add", use_container_width=True):
            if text.strip():
                tile.setdefault("items", []).append({
                    "id": new_id(),
                    "text": text.strip(),
                    "done": False,
                })
                save_and_sync()
                st.rerun()


# --- JOURNAL ---
def _render_journal(data, tile):
    entries = tile.get("entries", [])

    with st.form(f"add_journal_{tile['id']}", clear_on_submit=True):
        entry_date = st.date_input("Date", value="today")
        text = st.text_area("Entry", height=120, placeholder="Write your thoughts...")
        if st.form_submit_button("Add Entry", use_container_width=True, type="primary"):
            if text.strip():
                tile.setdefault("entries", []).append({
                    "id": new_id(),
                    "date": entry_date.isoformat(),
                    "text": text.strip(),
                })
                save_and_sync()
                st.rerun()

    if entries:
        st.markdown("---")
        sorted_entries = sorted(entries, key=lambda e: e.get("date", ""), reverse=True)
        for entry in sorted_entries:
            with st.expander(entry.get("date", ""), expanded=False):
                st.markdown(entry.get("text", ""))
                if st.button("Delete", key=f"del_j_{entry['id']}"):
                    tile["entries"] = [e for e in entries if e["id"] != entry["id"]]
                    save_and_sync()
                    st.rerun()


# --- TRACKER ---
def _render_tracker(data, tile):
    entries = tile.get("entries", [])

    with st.form(f"add_tracker_{tile['id']}", clear_on_submit=True):
        cols = st.columns([1, 2])
        with cols[0]:
            track_date = st.date_input("Date", value="today")
        with cols[1]:
            value = st.number_input("Value", step=0.1)
        if st.form_submit_button("Log", use_container_width=True, type="primary"):
            tile.setdefault("entries", []).append({
                "id": new_id(),
                "date": track_date.isoformat(),
                "value": float(value),
            })
            save_and_sync()
            st.rerun()

    if entries:
        sorted_entries = sorted(entries, key=lambda e: e.get("date", ""))
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[e["date"] for e in sorted_entries],
            y=[e["value"] for e in sorted_entries],
            mode="lines+markers",
            line=dict(color=tile.get("colour", "#00B4D8"), width=3),
            marker=dict(size=8),
        ))
        fig.update_layout(
            paper_bgcolor=BG_PRIMARY,
            plot_bgcolor=BG_SECONDARY,
            font=dict(family="Lexend, sans-serif", color=TEXT_PRIMARY, size=13),
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis=dict(gridcolor="#2a2a4e"),
            yaxis=dict(gridcolor="#2a2a4e"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Recent values
        st.markdown("##### Recent Values")
        for entry in reversed(sorted_entries[-10:]):
            st.markdown(f"**{entry.get('date', '')}** — {entry.get('value', '')}")


main()
