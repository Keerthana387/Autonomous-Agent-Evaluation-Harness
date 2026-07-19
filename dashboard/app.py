"""
Autonomous Agent Evaluation Harness Dashboard
"""

from pathlib import Path

import streamlit as st

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from harness.db import (
    get_database_names,
    get_database_path,
)

from sidebar import render_sidebar

render_sidebar()

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Autonomous Agent Evaluation Harness",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Initialize Session State
# --------------------------------------------------

database_names = get_database_names()

if not database_names:

    st.error(
        "No benchmark databases found inside 'databases/'."
    )

    st.stop()

if "selected_database" not in st.session_state:

    st.session_state.selected_database = get_database_path(
        database_names[0]
    )

# --------------------------------------------------
# Main Page
# --------------------------------------------------

st.title("🤖 Autonomous Agent Evaluation Harness")

st.info(
    """
Use the navigation panel to explore benchmark results.

All benchmark execution is available from the **🏠 Home** page.
"""
)

st.markdown(
    """
### Pages

- 🏠 Home
- 📊 Overview
- 📋 Tasks
- 🔍 Trace Viewer
- 📈 Analytics
"""
)