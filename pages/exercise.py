import streamlit as st
from components.github_storage import ensure_data_loaded, save_and_sync
from components.data_helpers import new_id, today
from components.theme import page_header, coloured_divider, TILE_COLOURS
from components.charts import plot_weight_over_time, plot_volume_per_session, plot_workout_frequency

COLOUR = TILE_COLOURS["exercise"]


def main():
    ensure_data_loaded()
    data = st.session_state["user_data"]
    exercise_data = data.get("exercise", {})
    logs = exercise_data.get("logs", [])
    plans = exercise_data.get("workout_plans", [])
    custom_exercises = exercise_data.get("custom_exercises", [])

    # Back button
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("\u2190 Back to Home", key="back_exercise"):
        st.switch_page("pages/home.py")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(page_header("Exercise", COLOUR), unsafe_allow_html=True)
    st.markdown(coloured_divider(COLOUR), unsafe_allow_html=True)

    tab_log, tab_history, tab_plans, tab_charts = st.tabs(["Log Workout", "History", "Plans", "Charts"])

    # --- LOG WORKOUT ---
    with tab_log:
        _render_log_tab(data, logs, plans, custom_exercises)

    # --- HISTORY ---
    with tab_history:
        _render_history_tab(logs, plans)

    # --- PLANS ---
    with tab_plans:
        _render_plans_tab(data, plans, custom_exercises)

    # --- CHARTS ---
    with tab_charts:
        _render_charts_tab(logs)


def _get_all_exercise_names(logs, custom_exercises):
    names = set(custom_exercises)
    for log in logs:
        for ex in log.get("exercises", []):
            names.add(ex.get("name", ""))
    names.discard("")
    return sorted(names)


def _render_log_tab(data, logs, plans, custom_exercises):
    # Quick-log from recent workouts
    if logs:
        st.markdown("##### Quick Log — Repeat a Recent Workout")
        recent = logs[-3:] if len(logs) >= 3 else logs
        recent_cols = st.columns(len(recent))
        for i, log in enumerate(reversed(recent)):
            with recent_cols[i]:
                ex_names = ", ".join(e.get("name", "") for e in log.get("exercises", [])[:3])
                plan_name = ""
                if log.get("plan_id"):
                    plan = next((p for p in plans if p.get("id") == log["plan_id"]), None)
                    if plan:
                        plan_name = plan.get("name", "")
                label = plan_name or ex_names or "Workout"
                st.markdown(
                    f'<div style="background:{COLOUR};border-radius:6px;padding:10px;color:white;font-size:13px;">'
                    f'<strong>{log.get("date", "")}</strong><br>{label}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Repeat", key=f"repeat_{log.get('id', i)}", use_container_width=True):
                    st.session_state["prefill_exercises"] = log.get("exercises", [])
                    st.session_state["prefill_plan_id"] = log.get("plan_id")
                    st.rerun()

    st.markdown("##### Log New Workout")

    # Pre-fill from plan selection
    selected_plan_id = None
    if plans:
        plan_names = ["— No plan —"] + [p["name"] for p in plans]
        selected_plan_idx = st.selectbox("Use a workout plan:", plan_names, key="log_plan_select")
        if selected_plan_idx != "— No plan —":
            selected_plan = next((p for p in plans if p["name"] == selected_plan_idx), None)
            if selected_plan:
                selected_plan_id = selected_plan["id"]
                if "prefill_exercises" not in st.session_state:
                    st.session_state["prefill_exercises"] = selected_plan.get("exercises", [])

    prefill = st.session_state.pop("prefill_exercises", [])
    prefill_plan_id = st.session_state.pop("prefill_plan_id", selected_plan_id)

    with st.form("log_workout_form", clear_on_submit=True):
        log_date = st.date_input("Date", value="today")

        num_exercises = st.number_input(
            "Number of exercises",
            min_value=1, max_value=20,
            value=max(1, len(prefill)),
        )

        all_exercise_names = _get_all_exercise_names(logs, custom_exercises)
        exercises_logged = []

        for i in range(int(num_exercises)):
            st.markdown(f"**Exercise {i + 1}**")
            cols = st.columns([3, 1, 1, 1])

            default_name = prefill[i].get("name", "") if i < len(prefill) else ""
            default_sets = prefill[i].get("target_sets", prefill[i].get("sets", 3)) if i < len(prefill) else 3
            reps_list = prefill[i].get("reps", prefill[i].get("target_reps", [8])) if i < len(prefill) else [8]
            default_reps = reps_list if isinstance(reps_list, int) else (reps_list[0] if reps_list else 8)
            default_weight = prefill[i].get("weight_kg", prefill[i].get("target_weight_kg", 0)) if i < len(prefill) else 0

            with cols[0]:
                name = st.text_input("Exercise", value=default_name, key=f"ex_name_{i}",
                                     placeholder="e.g. Bench Press")
            with cols[1]:
                sets = st.number_input("Sets", min_value=1, max_value=20, value=int(default_sets), key=f"ex_sets_{i}")
            with cols[2]:
                reps = st.number_input("Reps", min_value=1, max_value=100, value=int(default_reps), key=f"ex_reps_{i}")
            with cols[3]:
                weight = st.number_input("Weight (kg)", min_value=0.0, step=2.5, value=float(default_weight), key=f"ex_weight_{i}")

            notes = st.text_input("Notes (optional)", key=f"ex_notes_{i}", placeholder="How did it feel?")

            exercises_logged.append({
                "name": name,
                "sets": int(sets),
                "reps": [int(reps)] * int(sets),
                "weight_kg": float(weight),
                "notes": notes,
            })

        submitted = st.form_submit_button("Save Workout", use_container_width=True, type="primary")
        if submitted:
            valid_exercises = [e for e in exercises_logged if e["name"].strip()]
            if not valid_exercises:
                st.error("Please enter at least one exercise name.")
            else:
                new_log = {
                    "id": new_id(),
                    "date": log_date.isoformat(),
                    "plan_id": prefill_plan_id,
                    "exercises": valid_exercises,
                }
                data["exercise"]["logs"].append(new_log)
                # Track new exercise names
                for ex in valid_exercises:
                    if ex["name"] not in custom_exercises and ex["name"] not in [n for n in all_exercise_names]:
                        data["exercise"]["custom_exercises"].append(ex["name"])
                if save_and_sync():
                    st.success("Workout saved!")
                    st.rerun()


def _render_history_tab(logs, plans):
    if not logs:
        st.info("No workouts logged yet. Start by logging your first workout!")
        return

    sorted_logs = sorted(logs, key=lambda x: x.get("date", ""), reverse=True)

    for log in sorted_logs:
        plan_name = ""
        if log.get("plan_id"):
            plan = next((p for p in plans if p.get("id") == log["plan_id"]), None)
            if plan:
                plan_name = f" — {plan.get('name', '')}"

        with st.expander(f"{log.get('date', 'Unknown')}{plan_name}", expanded=False):
            for ex in log.get("exercises", []):
                reps = ex.get("reps", [])
                reps_str = " / ".join(str(r) for r in reps) if reps else "—"
                st.markdown(
                    f"**{ex.get('name', '')}** — {ex.get('sets', 0)} sets x {reps_str} reps @ {ex.get('weight_kg', 0)} kg"
                )
                if ex.get("notes"):
                    st.caption(ex["notes"])


def _render_plans_tab(data, plans, custom_exercises):
    st.markdown("##### Your Workout Plans")
    if plans:
        for plan in plans:
            with st.expander(plan["name"], expanded=False):
                for ex in plan.get("exercises", []):
                    st.markdown(
                        f"**{ex.get('name', '')}** — {ex.get('target_sets', 0)} sets x {ex.get('target_reps', 0)} reps @ {ex.get('target_weight_kg', 0)} kg"
                    )
                if st.button("Delete Plan", key=f"del_plan_{plan['id']}"):
                    data["exercise"]["workout_plans"] = [p for p in plans if p["id"] != plan["id"]]
                    if save_and_sync():
                        st.success("Plan deleted.")
                        st.rerun()
    else:
        st.info("No workout plans yet. Create one below.")

    st.markdown("##### Create New Plan")
    with st.form("create_plan_form", clear_on_submit=True):
        plan_name = st.text_input("Plan Name", placeholder="e.g. Push Day")
        num_ex = st.number_input("Number of exercises", min_value=1, max_value=15, value=4)

        plan_exercises = []
        for i in range(int(num_ex)):
            cols = st.columns([3, 1, 1, 1])
            with cols[0]:
                name = st.text_input("Exercise", key=f"plan_ex_name_{i}", placeholder="e.g. Bench Press")
            with cols[1]:
                sets = st.number_input("Sets", min_value=1, max_value=20, value=4, key=f"plan_ex_sets_{i}")
            with cols[2]:
                reps = st.number_input("Reps", min_value=1, max_value=100, value=8, key=f"plan_ex_reps_{i}")
            with cols[3]:
                weight = st.number_input("Weight (kg)", min_value=0.0, step=2.5, value=0.0, key=f"plan_ex_w_{i}")
            plan_exercises.append({
                "name": name,
                "target_sets": int(sets),
                "target_reps": int(reps),
                "target_weight_kg": float(weight),
            })

        if st.form_submit_button("Create Plan", use_container_width=True, type="primary"):
            if not plan_name.strip():
                st.error("Please enter a plan name.")
            else:
                valid = [e for e in plan_exercises if e["name"].strip()]
                if not valid:
                    st.error("Please add at least one exercise.")
                else:
                    new_plan = {
                        "id": new_id(),
                        "name": plan_name.strip(),
                        "exercises": valid,
                    }
                    data["exercise"]["workout_plans"].append(new_plan)
                    if save_and_sync():
                        st.success(f"Plan '{plan_name}' created!")
                        st.rerun()


def _render_charts_tab(logs):
    if not logs:
        st.info("Log some workouts to see your progress charts!")
        return

    # Get all exercise names for filter
    all_names = set()
    for log in logs:
        for ex in log.get("exercises", []):
            all_names.add(ex.get("name", ""))
    all_names.discard("")
    sorted_names = sorted(all_names)

    # Weight over time per exercise
    st.markdown("##### Weight Progression")
    selected_exercise = st.selectbox("Select exercise:", sorted_names, key="chart_exercise")
    if selected_exercise:
        fig = plot_weight_over_time(logs, selected_exercise)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No data for {selected_exercise}.")

    # Volume per session
    st.markdown("##### Volume Per Session")
    fig_vol = plot_volume_per_session(logs)
    if fig_vol:
        st.plotly_chart(fig_vol, use_container_width=True)

    # Frequency per week
    st.markdown("##### Workout Frequency")
    fig_freq = plot_workout_frequency(logs)
    if fig_freq:
        st.plotly_chart(fig_freq, use_container_width=True)


main()
