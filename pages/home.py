import streamlit as st
from components.github_storage import ensure_data_loaded
from components.tile_grid import render_tile_grid
from components.theme import page_header


def main():
    ensure_data_loaded()
    data = st.session_state.get("user_data", {})

    st.markdown(page_header("Life Planner"), unsafe_allow_html=True)
    st.markdown("")

    render_tile_grid(data)


main()
