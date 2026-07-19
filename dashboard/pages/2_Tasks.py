import streamlit as st

from database import (
    get_all_tasks,
    get_mutation_types,
    get_task_summary,
)

st.title("📝 Benchmark Tasks")

tasks = get_all_tasks()

from sidebar import render_sidebar

render_sidebar()

# ----------------------------------------------------
# Filters
# ----------------------------------------------------

left, middle, right = st.columns(3)

status = left.selectbox(
    "Status",
    [
        "All",
        "Passed",
        "Failed",
    ],
)

mutation = middle.selectbox(
    "Mutation",
    [
        "All",
        *get_mutation_types(),
    ],
)

search = right.text_input(
    "Task ID",
)

# ----------------------------------------------------
# Apply filters
# ----------------------------------------------------

filtered = tasks.copy()

if status == "Passed":
    filtered = filtered[
        filtered["passed"] == 1
    ]

elif status == "Failed":
    filtered = filtered[
        filtered["passed"] == 0
    ]

if mutation != "All":
    filtered = filtered[
        filtered["mutation_type"] == mutation
    ]

if search:
    filtered = filtered[
        filtered["task_id"].str.contains(
            search,
            case=False,
        )
    ]

# ----------------------------------------------------
# Table
# ----------------------------------------------------

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ----------------------------------------------------
# Inspector
# ----------------------------------------------------

task_id = st.selectbox(
    "Inspect Task",
    filtered["task_id"].tolist(),
)

summary = get_task_summary(task_id)

if summary:

    st.subheader(task_id)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Passed",
        "✅" if summary["passed"] else "❌",
    )

    c2.metric(
        "Steps",
        summary["num_steps"],
    )

    c3.metric(
        "Tool Calls",
        summary["num_tool_calls"],
    )

    st.write(summary)