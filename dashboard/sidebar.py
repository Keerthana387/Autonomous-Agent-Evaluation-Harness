from pathlib import Path
import streamlit as st

from harness.db import (
    get_database_names,
    get_database_path,
)

from pathlib import Path

import streamlit as st

from harness.db import (
    get_database_names,
    get_database_path,
)


def render_sidebar():

    st.sidebar.title("🤖 Evaluation Harness")

    database_names = get_database_names()

    if not database_names:
        st.sidebar.error("No databases found.")
        st.stop()

    # --------------------------------------------------
    # Initialize session state
    # --------------------------------------------------

    if "selected_database" not in st.session_state:
        st.session_state.selected_database = get_database_path(
            database_names[0]
        )

    current_name = Path(
        st.session_state.selected_database
    ).name

    if "database_name" not in st.session_state:
        st.session_state.database_name = current_name

    # Keep widget synchronized if the database was changed
    # elsewhere (e.g. Home page after Run Pipeline)

    if st.session_state.database_name != current_name:
        st.session_state.database_name = current_name

    # --------------------------------------------------
    # Callback
    # --------------------------------------------------

    def change_database():
        st.session_state.selected_database = get_database_path(
            st.session_state.database_name
        )

    # --------------------------------------------------
    # Database Selector
    # --------------------------------------------------

    st.sidebar.selectbox(
        "Current Database",
        database_names,
        key="database_name",
        on_change=change_database,
    )

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    st.sidebar.divider()

    st.sidebar.success(
        f"Using\n\n**{st.session_state.database_name}**"
    )