import streamlit as st
from components.theme import TILE_COLOURS, TILE_ICONS, TEXT_MUTED
from components.data_helpers import is_this_week


def get_tile_snippet(tile_id, data):
    if tile_id == "exercise":
        logs = data.get("exercise", {}).get("logs", [])
        count = sum(1 for log in logs if is_this_week(log.get("date")))
        return f"{count} session{'s' if count != 1 else ''} this week"

    elif tile_id == "projects":
        items = data.get("projects", {}).get("items", [])
        active = sum(1 for p in items if p.get("status") == "in_progress")
        return f"{active} active project{'s' if active != 1 else ''}"

    elif tile_id == "reading":
        books = data.get("reading", {}).get("books", [])
        reading = sum(1 for b in books if b.get("status") == "reading")
        return f"{reading} currently reading"

    elif tile_id == "work":
        tasks = data.get("work", {}).get("tasks", [])
        due = sum(1 for t in tasks if t.get("status") != "done" and is_this_week(t.get("deadline")))
        return f"{due} task{'s' if due != 1 else ''} due this week"

    else:
        return ""


def get_custom_tile_snippet(tile_data):
    tile_type = tile_data.get("type", "checklist")
    if tile_type == "checklist":
        items = tile_data.get("items", [])
        done = sum(1 for i in items if i.get("done"))
        return f"{done}/{len(items)} complete"
    elif tile_type == "journal":
        entries = tile_data.get("entries", [])
        return f"{len(entries)} entries"
    elif tile_type == "tracker":
        entries = tile_data.get("entries", [])
        if entries:
            return f"Latest: {entries[-1].get('value', '—')}"
        return "No entries yet"
    return ""


def render_tile(col, tile_id, label, colour, snippet, page_path, icon=None):
    icon_html = icon if icon else TILE_ICONS.get(tile_id, "")
    with col:
        st.markdown(
            f"""<div class="tile-card" style="background-color: {colour};">
                <div>
                    <div class="tile-icon">{icon_html}</div>
                    <div class="tile-snippet">{snippet}</div>
                </div>
                <div class="tile-label">{label}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button("Open", key=f"open_{tile_id}", use_container_width=True):
            # For custom tiles, set the selected tile ID before navigating
            if tile_id.startswith("custom_"):
                real_id = tile_id[len("custom_"):]
                st.session_state["selected_custom_tile"] = real_id
            st.switch_page(page_path)


def render_tile_grid(data):
    tile_settings = data.get("tile_settings", {})
    order = tile_settings.get("order", ["exercise", "projects", "reading", "work"])
    colours = tile_settings.get("colours", TILE_COLOURS)

    core_tiles = {
        "exercise": ("Exercise", "pages/exercise.py"),
        "projects": ("Projects", "pages/projects.py"),
        "reading": ("Reading", "pages/reading.py"),
        "work": ("Work", "pages/work.py"),
    }

    tiles_to_render = []
    for tile_id in order:
        if tile_id in core_tiles:
            label, page = core_tiles[tile_id]
            colour = colours.get(tile_id, TILE_COLOURS.get(tile_id, "#444"))
            snippet = get_tile_snippet(tile_id, data)
            tiles_to_render.append((tile_id, label, colour, snippet, page, None))

    custom_tiles = data.get("custom_tiles", [])
    for ct in custom_tiles:
        tile_id = f"custom_{ct['id']}"
        snippet = get_custom_tile_snippet(ct)
        tiles_to_render.append(
            (tile_id, ct["name"], ct.get("colour", "#444"), snippet, "pages/custom_tile.py", None)
        )

    # Render in 2-column grid
    for i in range(0, len(tiles_to_render), 2):
        cols = st.columns(2, gap="medium")
        tile = tiles_to_render[i]
        render_tile(cols[0], *tile)
        if i + 1 < len(tiles_to_render):
            tile2 = tiles_to_render[i + 1]
            render_tile(cols[1], *tile2)

    # "Add tile" button
    if len(tiles_to_render) % 2 == 0:
        cols = st.columns(2, gap="medium")
        add_col = cols[0]
    else:
        add_col = cols[1]

    with add_col:
        st.markdown(
            """<div class="tile-add">
                <div class="tile-add-icon">+</div>
                <div class="tile-add-text">Add Tile</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button("Add New Tile", key="add_tile_btn", use_container_width=True):
            st.session_state["show_add_tile"] = True
            st.switch_page("pages/custom_tile.py")
