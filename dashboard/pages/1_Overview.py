import streamlit as st
import plotly.express as px

from database import (
    database_exists,
    validate_schema,
    get_summary,
    get_recent_tasks,
)

from sidebar import render_sidebar

render_sidebar()

# --------------------------------------------------
# Page Config
# --------------------------------------------------

st.set_page_config(
    page_title="Overview",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Autonomous Agent Evaluation Dashboard")

# --------------------------------------------------
# Database Checks
# --------------------------------------------------

if not database_exists():
    st.error("Benchmark database not found.")
    st.stop()

if not validate_schema():
    st.error("Invalid benchmark database schema.")
    st.stop()

summary = get_summary()

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def success_color(rate: float):

    if rate >= 80:
        return "🟢"

    if rate >= 50:
        return "🟡"

    return "🔴"


status = success_color(summary["success_rate"])

# --------------------------------------------------
# KPI Cards
# --------------------------------------------------

st.subheader("Benchmark Summary")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Executed Tasks",
    summary["executed"],
)

c2.metric(
    "Passed",
    summary["passed"],
)

c3.metric(
    "Failed",
    summary["failed"],
)

c4.metric(
    "Success Rate",
    f"{summary['success_rate']:.1f}%",
)

st.markdown(f"### Overall Status: {status}")

st.divider()

# --------------------------------------------------
# Performance Metrics
# --------------------------------------------------

st.subheader("Execution Metrics")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Average Steps",
    f"{summary['average_steps']:.2f}",
)

c2.metric(
    "Average Tool Calls",
    f"{summary['average_tool_calls']:.2f}",
)

c3.metric(
    "Average Duration",
    f"{summary['average_duration']:.2f} sec",
)

st.divider()

# --------------------------------------------------
# Charts
# --------------------------------------------------

left, right = st.columns(2)

with left:

    fig = px.pie(
        names=["Passed", "Failed"],
        values=[
            summary["passed"],
            summary["failed"],
        ],
        hole=0.55,
        title="Pass vs Fail",
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

with right:

    fig = px.bar(
        x=["Avg Steps", "Avg Tools", "Avg Time (s)"],
        y=[
            summary["average_steps"],
            summary["average_tool_calls"],
            summary["average_duration"],
        ],
        title="Average Execution Statistics",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

st.divider()

# --------------------------------------------------
# Recent Tasks
# --------------------------------------------------

st.subheader("Recent Benchmark Tasks")

recent = get_recent_tasks()

recent["Status"] = recent["passed"].map(
    lambda x: "✅ Passed" if x else "❌ Failed"
)

recent = recent.rename(
    columns={
        "task_id": "Task ID",
        "duration_seconds": "Duration (s)",
        "created_at": "Created At",
    }
)

recent = recent[
    [
        "Task ID",
        "Status",
        "Duration (s)",
        "Created At",
    ]
]

recent["Duration (s)"] = recent["Duration (s)"].round(3)

st.dataframe(
    recent,
    width="stretch",
    hide_index=True,
)

st.caption(
    f"Showing the {len(recent)} most recent benchmark runs."
)