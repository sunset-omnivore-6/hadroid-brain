import streamlit as st
from datetime import date, timedelta
from components.github_storage import ensure_data_loaded, save_and_sync
from components.data_helpers import new_id, today, is_this_week
from components.theme import page_header, coloured_divider, TILE_COLOURS, BG_SECONDARY
from components.charts import plot_chartership_radar

COLOUR = TILE_COLOURS["work"]

PRIORITY_COLOURS = {"high": "#E63946", "medium": "#F4A261", "low": "#2A9D8F"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def main():
    ensure_data_loaded()
    data = st.session_state["user_data"]
    work = data.get("work", {})

    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("\u2190 Back to Home", key="back_work"):
        st.switch_page("pages/home.py")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(page_header("Work", COLOUR), unsafe_allow_html=True)
    st.markdown(coloured_divider(COLOUR), unsafe_allow_html=True)

    tab_kanban, tab_priority, tab_calendar, tab_learning, tab_charter = st.tabs(
        ["Kanban", "Priority List", "Calendar", "Learning", "Chartership"]
    )

    with tab_kanban:
        _render_kanban(data, work)
    with tab_priority:
        _render_priority(data, work)
    with tab_calendar:
        _render_calendar(work)
    with tab_learning:
        _render_learning(data, work)
    with tab_charter:
        _render_chartership(data, work)


# --- ADD TASK FORM ---
def _add_task_form(data, key_prefix="kanban"):
    with st.form(f"add_task_{key_prefix}", clear_on_submit=True):
        st.markdown("**Add New Task**")
        title = st.text_input("Title", key=f"task_title_{key_prefix}", placeholder="What needs to be done?")
        cols = st.columns(3)
        with cols[0]:
            priority = st.selectbox("Priority", ["high", "medium", "low"], index=1, key=f"task_pri_{key_prefix}")
        with cols[1]:
            deadline = st.date_input("Deadline (optional)", value=None, key=f"task_dead_{key_prefix}")
        with cols[2]:
            tags_str = st.text_input("Tags (comma-separated)", key=f"task_tags_{key_prefix}", placeholder="e.g. chartership")
        description = st.text_area("Description (optional)", key=f"task_desc_{key_prefix}", height=80)

        if st.form_submit_button("Add Task", use_container_width=True, type="primary"):
            if not title.strip():
                st.error("Please enter a task title.")
            else:
                task = {
                    "id": new_id(),
                    "title": title.strip(),
                    "description": description,
                    "priority": priority,
                    "deadline": deadline.isoformat() if deadline else None,
                    "status": "to_do",
                    "tags": [t.strip() for t in tags_str.split(",") if t.strip()],
                    "created": today(),
                }
                data["work"]["tasks"].append(task)
                if save_and_sync():
                    st.success("Task added!")
                    st.rerun()


def _task_card(task, show_move=True, data=None):
    pri_col = PRIORITY_COLOURS.get(task.get("priority", "medium"), "#888")
    overdue = False
    if task.get("deadline") and task.get("status") != "done":
        overdue = date.fromisoformat(task["deadline"]) < date.today()

    border = f"border-left: 4px solid {pri_col};"
    bg = "#3a1a1a" if overdue else BG_SECONDARY
    st.markdown(
        f'<div style="background:{bg};{border}border-radius:6px;padding:12px;margin-bottom:8px;">'
        f'<strong style="font-size:15px;">{task.get("title", "")}</strong>'
        f'{"<br><span style=color:#E63946;font-size:12px;>OVERDUE</span>" if overdue else ""}'
        f'{"<br><span style=font-size:12px;color:#aaa;>Due: " + task.get("deadline", "") + "</span>" if task.get("deadline") else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if show_move and data is not None:
        statuses = ["to_do", "in_progress", "done"]
        current_idx = statuses.index(task.get("status", "to_do")) if task.get("status") in statuses else 0
        move_cols = st.columns(3)

        with move_cols[0]:
            if current_idx > 0:
                if st.button("\u2190", key=f"move_left_{task['id']}", help="Move left"):
                    task["status"] = statuses[current_idx - 1]
                    save_and_sync()
                    st.rerun()
        with move_cols[1]:
            if st.button("\U0001F5D1", key=f"del_task_{task['id']}", help="Delete"):
                data["work"]["tasks"] = [t for t in data["work"]["tasks"] if t["id"] != task["id"]]
                save_and_sync()
                st.rerun()
        with move_cols[2]:
            if current_idx < len(statuses) - 1:
                if st.button("\u2192", key=f"move_right_{task['id']}", help="Move right"):
                    task["status"] = statuses[current_idx + 1]
                    save_and_sync()
                    st.rerun()


# --- KANBAN ---
def _render_kanban(data, work):
    tasks = work.get("tasks", [])

    col_todo, col_prog, col_done = st.columns(3, gap="medium")

    with col_todo:
        st.markdown(f'<h3 style="color:{COLOUR};">To Do</h3>', unsafe_allow_html=True)
        for t in [t for t in tasks if t.get("status") == "to_do"]:
            _task_card(t, show_move=True, data=data)

    with col_prog:
        st.markdown(f'<h3 style="color:{COLOUR};">In Progress</h3>', unsafe_allow_html=True)
        for t in [t for t in tasks if t.get("status") == "in_progress"]:
            _task_card(t, show_move=True, data=data)

    with col_done:
        st.markdown(f'<h3 style="color:{COLOUR};">Done</h3>', unsafe_allow_html=True)
        for t in [t for t in tasks if t.get("status") == "done"]:
            _task_card(t, show_move=True, data=data)

    st.markdown("---")
    _add_task_form(data, "kanban")


# --- PRIORITY LIST ---
def _render_priority(data, work):
    tasks = [t for t in work.get("tasks", []) if t.get("status") != "done"]

    if not tasks:
        st.info("No open tasks. Add one from the Kanban tab!")
        return

    sorted_tasks = sorted(tasks, key=lambda t: (
        PRIORITY_ORDER.get(t.get("priority", "medium"), 1),
        t.get("deadline") or "9999-12-31",
    ))

    for task in sorted_tasks:
        pri_col = PRIORITY_COLOURS.get(task.get("priority", "medium"), "#888")
        cols = st.columns([0.3, 3, 1, 1, 0.5])

        with cols[0]:
            st.markdown(
                f'<div style="background:{pri_col};width:12px;height:12px;border-radius:50%;margin-top:8px;"></div>',
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.markdown(f"**{task.get('title', '')}**")
        with cols[2]:
            st.caption(task.get("deadline") or "No deadline")
        with cols[3]:
            st.caption(task.get("status", "to_do").replace("_", " ").title())
        with cols[4]:
            if st.button("\u2713", key=f"done_pri_{task['id']}", help="Mark done"):
                task["status"] = "done"
                save_and_sync()
                st.rerun()


# --- CALENDAR ---
def _render_calendar(work):
    tasks = [t for t in work.get("tasks", []) if t.get("deadline") and t.get("status") != "done"]

    if not tasks:
        st.info("No tasks with deadlines. Add deadlines to see them here!")
        return

    tasks.sort(key=lambda t: t.get("deadline", ""))

    # Group by week
    from collections import defaultdict
    weeks = defaultdict(list)
    for task in tasks:
        d = date.fromisoformat(task["deadline"])
        monday = d - timedelta(days=d.weekday())
        weeks[monday.isoformat()].append(task)

    for week_start, week_tasks in sorted(weeks.items()):
        ws = date.fromisoformat(week_start)
        we = ws + timedelta(days=6)
        is_current = is_this_week(week_start)
        header = f"Week of {ws.strftime('%d %b')} — {we.strftime('%d %b')}"
        if is_current:
            header += " (This Week)"

        with st.expander(header, expanded=is_current):
            for task in week_tasks:
                pri_col = PRIORITY_COLOURS.get(task.get("priority", "medium"), "#888")
                overdue = date.fromisoformat(task["deadline"]) < date.today()
                st.markdown(
                    f'<span style="color:{pri_col};">&#x25CF;</span> '
                    f'**{task.get("title", "")}** — {task.get("deadline", "")}'
                    f'{"  <span style=color:#E63946;>(OVERDUE)</span>" if overdue else ""}',
                    unsafe_allow_html=True,
                )


# --- LEARNING TRACKER ---
def _render_learning(data, work):
    learning = work.get("learning_log", [])

    st.markdown("##### Log Learning Activity")
    with st.form("add_learning", clear_on_submit=True):
        cols = st.columns([2, 1, 1])
        with cols[0]:
            topic = st.text_input("Topic", placeholder="e.g. Python async patterns")
        with cols[1]:
            learn_date = st.date_input("Date", value="today")
        with cols[2]:
            duration = st.number_input("Duration (minutes)", min_value=5, max_value=480, value=30, step=5)

        category = st.selectbox("Category", ["CPD", "Technical Skills", "Soft Skills", "Chartership", "Other"])
        notes = st.text_area("Notes", height=80, placeholder="What did you learn?")
        resource = st.text_input("Resource / Link (optional)", placeholder="URL or book title")

        if st.form_submit_button("Log Activity", use_container_width=True, type="primary"):
            if not topic.strip():
                st.error("Please enter a topic.")
            else:
                entry = {
                    "id": new_id(),
                    "topic": topic.strip(),
                    "date": learn_date.isoformat(),
                    "duration_minutes": int(duration),
                    "category": category.lower().replace(" ", "_"),
                    "notes": notes,
                    "resource": resource,
                }
                data["work"]["learning_log"].append(entry)
                if save_and_sync():
                    st.success("Learning logged!")
                    st.rerun()

    if learning:
        st.markdown("---")
        st.markdown("##### Learning History")
        filter_cat = st.selectbox("Filter by category:", ["All", "CPD", "Technical Skills", "Soft Skills", "Chartership", "Other"], key="learn_filter")

        filtered = learning if filter_cat == "All" else [
            l for l in learning if l.get("category", "").replace("_", " ").title() == filter_cat
        ]
        sorted_learning = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

        total_hours = sum(l.get("duration_minutes", 0) for l in sorted_learning) / 60
        st.metric("Total Hours", f"{total_hours:.1f}h")

        for entry in sorted_learning:
            with st.expander(f"{entry.get('date', '')} — {entry.get('topic', '')}", expanded=False):
                st.markdown(f"**Category:** {entry.get('category', '').replace('_', ' ').title()}")
                st.markdown(f"**Duration:** {entry.get('duration_minutes', 0)} minutes")
                if entry.get("notes"):
                    st.markdown(entry["notes"])
                if entry.get("resource"):
                    st.markdown(f"**Resource:** {entry['resource']}")


# --- CHARTERSHIP ---
def _render_chartership(data, work):
    charter = work.get("chartership", {})
    competencies = charter.get("competencies", [])

    st.markdown("##### CEng Chartership Journey")

    # Radar chart
    fig = plot_chartership_radar(competencies)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    # Overall progress
    if competencies:
        avg = sum(c.get("progress_pct", 0) for c in competencies) / len(competencies)
        st.progress(avg / 100, text=f"Overall Progress: {avg:.0f}%")

    st.markdown("---")

    # Individual competency areas
    for comp in competencies:
        with st.expander(f"{comp.get('name', '')} — {comp.get('progress_pct', 0)}%", expanded=False):
            # Progress slider
            new_pct = st.slider(
                "Progress",
                min_value=0, max_value=100,
                value=comp.get("progress_pct", 0),
                key=f"charter_pct_{comp['id']}",
            )
            if new_pct != comp.get("progress_pct", 0):
                comp["progress_pct"] = new_pct
                save_and_sync()

            # Notes
            notes = st.text_area(
                "Notes / Reflections",
                value=comp.get("notes", ""),
                key=f"charter_notes_{comp['id']}",
                height=80,
            )
            if notes != comp.get("notes", ""):
                comp["notes"] = notes
                save_and_sync()

            # Evidence log
            st.markdown("**Evidence**")
            for ev in comp.get("evidence", []):
                st.markdown(
                    f"- **{ev.get('title', '')}** ({ev.get('date', '')}) — {ev.get('description', '')}"
                )

            # Add evidence
            with st.form(f"add_evidence_{comp['id']}", clear_on_submit=True):
                st.markdown("**Add Evidence**")
                ev_title = st.text_input("Title", key=f"ev_title_{comp['id']}", placeholder="e.g. Led project X")
                ev_desc = st.text_area("Description", key=f"ev_desc_{comp['id']}", height=60)
                ev_date = st.date_input("Date", value="today", key=f"ev_date_{comp['id']}")

                if st.form_submit_button("Add Evidence"):
                    if ev_title.strip():
                        evidence = {
                            "id": new_id(),
                            "title": ev_title.strip(),
                            "description": ev_desc,
                            "date": ev_date.isoformat(),
                        }
                        comp["evidence"].append(evidence)
                        if save_and_sync():
                            st.success("Evidence added!")
                            st.rerun()


main()
