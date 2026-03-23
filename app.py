import streamlit as st
from components.theme import get_global_css
from components.github_storage import ensure_data_loaded

st.set_page_config(
    page_title="Harad Life Planner",
    page_icon="\U0001F4CB",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject global CSS
st.html(f"<style>{get_global_css()}</style>")

# Pre-load data
ensure_data_loaded()

# Define pages
home = st.Page("pages/home.py", title="Home", default=True)
exercise = st.Page("pages/exercise.py", title="Exercise", url_path="exercise")
work = st.Page("pages/work.py", title="Work", url_path="work")
projects = st.Page("pages/projects.py", title="Projects", url_path="projects")
reading = st.Page("pages/reading.py", title="Reading", url_path="reading")
custom_tile = st.Page("pages/custom_tile.py", title="Custom", url_path="custom")

# Hidden navigation — tiles ARE the navigation
pg = st.navigation(
    [home, exercise, work, projects, reading, custom_tile],
    position="hidden",
)

pg.run()

# Persistent weekly summary button (renders on every page, CSS makes it fixed position)
from components.weekly_summary import show_weekly_summary

st.markdown('<div class="weekly-summary-trigger">', unsafe_allow_html=True)
if st.button("\U0001F4C5 Weekly Summary", key="weekly_summary_btn"):
    show_weekly_summary()
st.markdown('</div>', unsafe_allow_html=True)
