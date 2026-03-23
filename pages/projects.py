import streamlit as st
from components.github_storage import ensure_data_loaded, save_and_sync
from components.data_helpers import new_id, today
from components.theme import page_header, coloured_divider, TILE_COLOURS, BG_SECONDARY

COLOUR = TILE_COLOURS["projects"]
STATUS_LABELS = {
    "not_started": "Not Started",
    "in_progress": "In Progress",
    "on_hold": "On Hold",
    "complete": "Complete",
}
STATUS_COLOURS = {
    "not_started": "#888",
    "in_progress": "#00B4D8",
    "on_hold": "#F4A261",
    "complete": "#00A86B",
}


def main():
    ensure_data_loaded()
    data = st.session_state["user_data"]
    projects_data = data.get("projects", {})

    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("\u2190 Back to Home", key="back_projects"):
        st.switch_page("pages/home.py")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(page_header("Projects", COLOUR), unsafe_allow_html=True)
    st.markdown(coloured_divider(COLOUR), unsafe_allow_html=True)

    selected = st.session_state.get("selected_project")
    if selected:
        _render_project_detail(data, projects_data, selected)
    else:
        _render_project_list(data, projects_data)


def _calc_progress(project):
    milestones = project.get("milestones", [])
    if not milestones:
        return 0
    done = sum(1 for m in milestones if m.get("done"))
    return done / len(milestones)


def _render_project_list(data, projects_data):
    items = projects_data.get("items", [])
    goals = projects_data.get("goals", [])

    tab_projects, tab_goals = st.tabs(["Projects", "Long-term Goals"])

    with tab_projects:
        # Project cards
        if items:
            for project in items:
                progress = _calc_progress(project)
                status = project.get("status", "not_started")
                status_col = STATUS_COLOURS.get(status, "#888")

                col_main, col_action = st.columns([5, 1])
                with col_main:
                    st.markdown(
                        f'<div style="background:{BG_SECONDARY};border-radius:8px;padding:14px;margin-bottom:8px;'
                        f'border-left:4px solid {COLOUR};">'
                        f'<strong style="font-size:16px;">{project.get("name", "")}</strong>'
                        f'<br><span style="color:{status_col};font-size:13px;">{STATUS_LABELS.get(status, status)}</span>'
                        f' &middot; <span style="font-size:13px;color:#aaa;">{project.get("category", "")}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.progress(progress, text=f"{progress:.0%} complete")

                with col_action:
                    if st.button("Open", key=f"open_proj_{project['id']}", use_container_width=True):
                        st.session_state["selected_project"] = project["id"]
                        st.rerun()
        else:
            st.info("No projects yet. Create one below!")

        st.markdown("---")

        # Add project form
        st.markdown("##### Create New Project")
        with st.form("add_project", clear_on_submit=True):
            name = st.text_input("Project Name", placeholder="e.g. Scottish Lochs App")
            description = st.text_area("Description", height=80)
            cols = st.columns(2)
            with cols[0]:
                category = st.selectbox("Category", ["coding", "learning", "creative", "other"])
            with cols[1]:
                status = st.selectbox("Status", list(STATUS_LABELS.keys()), format_func=lambda x: STATUS_LABELS[x])

            if st.form_submit_button("Create Project", use_container_width=True, type="primary"):
                if not name.strip():
                    st.error("Please enter a project name.")
                else:
                    project = {
                        "id": new_id(),
                        "name": name.strip(),
                        "description": description,
                        "status": status,
                        "category": category,
                        "created": today(),
                        "milestones": [],
                    }
                    data["projects"]["items"].append(project)
                    if save_and_sync():
                        st.success(f"Project '{name}' created!")
                        st.rerun()

    with tab_goals:
        _render_goals(data, projects_data)


def _render_project_detail(data, projects_data, project_id):
    items = projects_data.get("items", [])
    project = next((p for p in items if p.get("id") == project_id), None)

    if not project:
        st.error("Project not found.")
        st.session_state.pop("selected_project", None)
        st.rerun()
        return

    if st.button("\u2190 Back to Projects"):
        st.session_state.pop("selected_project", None)
        st.rerun()

    st.markdown(f"### {project.get('name', '')}")
    st.caption(f"Category: {project.get('category', '')} | Created: {project.get('created', '')}")

    # Status
    new_status = st.selectbox(
        "Status",
        list(STATUS_LABELS.keys()),
        index=list(STATUS_LABELS.keys()).index(project.get("status", "not_started")),
        format_func=lambda x: STATUS_LABELS[x],
        key="proj_status",
    )
    if new_status != project.get("status"):
        project["status"] = new_status
        save_and_sync()

    # Description
    st.markdown("**Description**")
    st.markdown(project.get("description", "") or "_No description_")

    # Progress
    progress = _calc_progress(project)
    st.progress(progress, text=f"{progress:.0%} complete")

    st.markdown("---")

    # Milestones
    st.markdown("##### Milestones")
    milestones = project.get("milestones", [])

    if milestones:
        for ms in milestones:
            cols = st.columns([0.5, 4, 2, 0.5])
            with cols[0]:
                done = st.checkbox("", value=ms.get("done", False), key=f"ms_done_{ms['id']}")
                if done != ms.get("done", False):
                    ms["done"] = done
                    save_and_sync()
                    st.rerun()
            with cols[1]:
                style = "text-decoration: line-through; color: #666;" if ms.get("done") else ""
                st.markdown(f'<span style="{style}">{ms.get("name", "")}</span>', unsafe_allow_html=True)
            with cols[2]:
                if ms.get("target_date"):
                    st.caption(f"Due: {ms['target_date']}")
            with cols[3]:
                if st.button("\U0001F5D1", key=f"del_ms_{ms['id']}"):
                    project["milestones"] = [m for m in milestones if m["id"] != ms["id"]]
                    save_and_sync()
                    st.rerun()
    else:
        st.info("No milestones yet. Add one below.")

    # Add milestone
    with st.form(f"add_milestone_{project_id}", clear_on_submit=True):
        cols = st.columns([3, 1])
        with cols[0]:
            ms_name = st.text_input("Milestone name", placeholder="e.g. Fetch SEPA data")
        with cols[1]:
            ms_date = st.date_input("Target date (optional)", value=None)

        if st.form_submit_button("Add Milestone", use_container_width=True):
            if ms_name.strip():
                milestone = {
                    "id": new_id(),
                    "name": ms_name.strip(),
                    "done": False,
                    "target_date": ms_date.isoformat() if ms_date else None,
                }
                project["milestones"].append(milestone)
                if save_and_sync():
                    st.success("Milestone added!")
                    st.rerun()

    st.markdown("---")

    # Delete project
    if st.button("Delete Project", key=f"del_project_{project_id}", type="secondary"):
        data["projects"]["items"] = [p for p in items if p["id"] != project_id]
        st.session_state.pop("selected_project", None)
        save_and_sync()
        st.rerun()


def _render_goals(data, projects_data):
    goals = projects_data.get("goals", [])
    items = projects_data.get("items", [])

    if goals:
        for goal in goals:
            status_icon = {"active": "\U0001F7E2", "achieved": "\u2705", "paused": "\u23F8\uFE0F"}.get(
                goal.get("status", "active"), ""
            )
            with st.expander(f"{status_icon} {goal.get('name', '')}", expanded=False):
                new_status = st.selectbox(
                    "Status",
                    ["active", "achieved", "paused"],
                    index=["active", "achieved", "paused"].index(goal.get("status", "active")),
                    key=f"goal_status_{goal['id']}",
                )
                if new_status != goal.get("status"):
                    goal["status"] = new_status
                    save_and_sync()

                # Linked projects
                linked_ids = goal.get("linked_project_ids", [])
                linked_names = [p["name"] for p in items if p["id"] in linked_ids]
                if linked_names:
                    st.markdown(f"**Linked projects:** {', '.join(linked_names)}")

                # Link a project
                unlinked = [p for p in items if p["id"] not in linked_ids]
                if unlinked:
                    link_choice = st.selectbox(
                        "Link a project:",
                        ["— None —"] + [p["name"] for p in unlinked],
                        key=f"link_proj_{goal['id']}",
                    )
                    if link_choice != "— None —":
                        proj = next(p for p in unlinked if p["name"] == link_choice)
                        if st.button("Link", key=f"do_link_{goal['id']}"):
                            goal.setdefault("linked_project_ids", []).append(proj["id"])
                            save_and_sync()
                            st.rerun()

                if st.button("Delete Goal", key=f"del_goal_{goal['id']}"):
                    data["projects"]["goals"] = [g for g in goals if g["id"] != goal["id"]]
                    save_and_sync()
                    st.rerun()
    else:
        st.info("No long-term goals yet. Add one below.")

    # Add goal
    with st.form("add_goal", clear_on_submit=True):
        st.markdown("**Add Long-term Goal**")
        goal_name = st.text_input("Goal", placeholder="e.g. Learn Rust")
        if st.form_submit_button("Add Goal", use_container_width=True, type="primary"):
            if goal_name.strip():
                goal = {
                    "id": new_id(),
                    "name": goal_name.strip(),
                    "status": "active",
                    "linked_project_ids": [],
                }
                data["projects"]["goals"].append(goal)
                if save_and_sync():
                    st.success("Goal added!")
                    st.rerun()


main()
