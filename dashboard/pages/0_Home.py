"""
Home page for running benchmark pipelines.
"""

from pathlib import Path

import streamlit as st

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from harness.db import (
    create_database,
    default_database_name,
    get_database_names,
    get_database_path,
)

from run_pipeline import (
    PipelineConfig,
    run_pipeline,
)

from sidebar import render_sidebar

render_sidebar()

# ============================================================
# Page
# ============================================================

st.title("🏠 Benchmark Runner")

st.write(
    """
Run the complete benchmark pipeline from here.

The benchmark consists of:

1. Generate mutated benchmark tasks
2. Execute all benchmark tasks
3. Score every trace
"""
)

st.divider()

# ============================================================
# Provider
# ============================================================

st.subheader("Provider")

provider = st.selectbox(
    "LLM Provider",
    [
        "gemini",
    ],
)

st.divider()

# ============================================================
# Database
# ============================================================

st.subheader("Database")

database_mode = st.radio(
    "Choose database",
    [
        "Use Existing Database",
        "Create New Database",
    ],
)

database_names = get_database_names()

selected_existing = None
new_database_name = None

if database_mode == "Use Existing Database":

    current_name = Path(
        st.session_state.selected_database
    ).name

    index = 0

    if current_name in database_names:
        index = database_names.index(current_name)

    selected_existing = st.selectbox(
        "Database",
        database_names,
        index=index,
    )

else:

    new_database_name = st.text_input(
        "Database Name",
        value=default_database_name(),
    )

st.divider()

# ============================================================
# Run Pipeline
# ============================================================

st.subheader("Run Benchmark")

run = st.button(
    "▶ Run Pipeline",
    type="primary",
    use_container_width=True,
)

if run:

    if database_mode == "Use Existing Database":

        db_path = get_database_path(
            selected_existing,
        )

    else:

        try:

            db_path = create_database(
                new_database_name,
            )

        except FileExistsError:

            st.error(
                "A database with this name already exists."
            )

            st.stop()

    progress = st.progress(0)

    status = st.empty()

    def callback(
        message: str,
        value: float,
    ):

        progress.progress(value)

        status.info(message)

    with st.spinner("Running benchmark..."):

        result = run_pipeline(
            PipelineConfig(
                provider=provider,
                db_path=db_path,
            ),
            progress_callback=callback,
        )

    progress.progress(1.0)

    status.success(
        "Pipeline completed successfully."
    )

    st.session_state.selected_database = db_path

    st.success(
        f"""
Benchmark completed successfully!

Database:
`{db_path.name}`
"""
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Generated",
        result.generated_tasks,
    )

    c2.metric(
        "Executed",
        result.executed_tasks,
    )

    c3.metric(
        "Scored",
        result.scored_tasks,
    )

    c4.metric(
        "Duration",
        f"{result.duration_seconds:.2f}s",
    )

    st.balloons()

    st.rerun()