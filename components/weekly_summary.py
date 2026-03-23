import streamlit as st
from components.data_helpers import current_week_range, is_this_week
from components.theme import TILE_COLOURS


@st.dialog("Weekly Summary", width="large")
def show_weekly_summary():
    data = st.session_state.get("user_data", {})
    monday, sunday = current_week_range()

    st.markdown(f"### Week of {monday} to {sunday}")
    st.markdown("---")

    # 3 Editable Focuses
    st.markdown("#### This Week's Focuses")
    focuses = data.get("weekly_focuses", {})

    with st.form("weekly_focuses_form", clear_on_submit=False):
        f1 = st.text_input("Focus 1", value=focuses.get("focus_1", ""), placeholder="What's your main focus?")
        f2 = st.text_input("Focus 2", value=focuses.get("focus_2", ""), placeholder="Second priority...")
        f3 = st.text_input("Focus 3", value=focuses.get("focus_3", ""), placeholder="Third priority...")

        if st.form_submit_button("Save Focuses", use_container_width=True):
            data["weekly_focuses"] = {
                "focus_1": f1,
                "focus_2": f2,
                "focus_3": f3,
                "week_start": monday,
            }
            from components.github_storage import save_and_sync
            if save_and_sync():
                st.success("Focuses saved!")

    st.markdown("---")

    # Gym This Week
    st.markdown("#### Gym This Week")
    from datetime import date, timedelta
    mon = date.fromisoformat(monday)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    logs = data.get("exercise", {}).get("logs", [])
    week_log_dates = {log.get("date") for log in logs if is_this_week(log.get("date"))}

    day_cols = st.columns(7)
    for i, day_col in enumerate(day_cols):
        d = (mon + timedelta(days=i)).isoformat()
        with day_col:
            has_session = d in week_log_dates
            if has_session:
                log_entry = next((l for l in logs if l.get("date") == d), None)
                plan_name = ""
                if log_entry and log_entry.get("plan_id"):
                    plans = data.get("exercise", {}).get("workout_plans", [])
                    plan = next((p for p in plans if p.get("id") == log_entry["plan_id"]), None)
                    if plan:
                        plan_name = plan.get("name", "")
                colour = TILE_COLOURS["exercise"]
                st.markdown(
                    f'<div style="background:{colour};border-radius:6px;padding:8px;text-align:center;color:white;font-size:13px;">'
                    f'<strong>{days[i]}</strong><br>{plan_name or "Workout"}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#2a2a3e;border-radius:6px;padding:8px;text-align:center;color:#666;font-size:13px;">'
                    f'<strong>{days[i]}</strong><br>—</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # Quick Stats
    st.markdown("#### Quick Stats")
    stat_cols = st.columns(4)

    exercise_count = sum(1 for log in logs if is_this_week(log.get("date")))
    stat_cols[0].metric("Workouts", exercise_count)

    tasks = data.get("work", {}).get("tasks", [])
    tasks_due = sum(1 for t in tasks if t.get("status") != "done" and is_this_week(t.get("deadline")))
    stat_cols[1].metric("Tasks Due", tasks_due)

    books = data.get("reading", {}).get("books", [])
    reading_count = sum(1 for b in books if b.get("status") == "reading")
    stat_cols[2].metric("Reading", reading_count)

    projects = data.get("projects", {}).get("items", [])
    active_projects = sum(1 for p in projects if p.get("status") == "in_progress")
    stat_cols[3].metric("Active Projects", active_projects)
