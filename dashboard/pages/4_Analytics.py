import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    get_all_tasks,
    get_task_report,
)

st.title("📈 Benchmark Analytics")

from sidebar import render_sidebar

render_sidebar()

# --------------------------------------------------
# Load Tasks
# --------------------------------------------------

tasks = get_all_tasks()

if tasks.empty:
    st.warning("No benchmark data found.")
    st.stop()

reports = []

for task_id in tasks["task_id"]:

    report = get_task_report(task_id)

    if report is None:
        continue

    trace = report["trace"]
    score = report["score"]

    reports.append(
        {
            "task_id": task_id,
            "mutation_type": trace.get("mutation_type", "Base Task"),
            "passed": score["passed"],
            "duration": trace.get("duration_seconds", 0),
            "steps": trace.get("num_steps", 0),
            "tools": trace.get("num_tool_calls", 0),
            "failed_checks": score.get("failed_checks", []),
        }
    )

df = pd.DataFrame(reports)

# --------------------------------------------------
# KPI Cards
# --------------------------------------------------

st.subheader("Overall Statistics")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total Tasks",
    len(df),
)

c2.metric(
    "Passed",
    int(df["passed"].sum()),
)

c3.metric(
    "Failed",
    int((~df["passed"]).sum()),
)

c4.metric(
    "Success Rate",
    f"{100 * df['passed'].mean():.1f}%"
)

st.divider()

# --------------------------------------------------
# Success Rate by Mutation
# --------------------------------------------------

st.subheader("Success Rate by Mutation Type")

mutation = (
    df.groupby("mutation_type")["passed"]
      .mean()
      .reset_index()
)

mutation["passed"] *= 100

fig = px.bar(
    mutation,
    x="mutation_type",
    y="passed",
    labels={
        "mutation_type": "Mutation Type",
        "passed": "Success Rate (%)",
    },
)

fig.update_layout(
    xaxis_title="Mutation Type",
    yaxis_title="Success Rate (%)",
)

st.plotly_chart(
    fig,
    width="stretch",
)

st.divider()

# --------------------------------------------------
# Duration Distribution
# --------------------------------------------------

st.subheader("Execution Time Distribution")

fig = px.histogram(
    df,
    x="duration",
    nbins=15,
    labels={
        "duration": "Duration (seconds)",
    },
)

st.plotly_chart(
    fig,
    width="stretch",
)

st.divider()

# --------------------------------------------------
# Tool Usage
# --------------------------------------------------

left, right = st.columns(2)

with left:

    st.subheader("Tool Calls")

    fig = px.histogram(
        df,
        x="tools",
        nbins=10,
        labels={
            "tools": "Tool Calls",
        },
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

with right:

    st.subheader("Reasoning Steps")

    fig = px.histogram(
        df,
        x="steps",
        nbins=10,
        labels={
            "steps": "Steps",
        },
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

st.divider()

# --------------------------------------------------
# Pass vs Fail by Mutation
# --------------------------------------------------

st.subheader("Pass vs Fail by Mutation Type")

group = (
    df.groupby(
        ["mutation_type", "passed"]
    )
    .size()
    .reset_index(name="count")
)

group["Status"] = group["passed"].map(
    {
        True: "Passed",
        False: "Failed",
    }
)

fig = px.bar(
    group,
    x="mutation_type",
    y="count",
    color="Status",
    barmode="group",
)

st.plotly_chart(
    fig,
    width="stretch",
)

st.divider()

# --------------------------------------------------
# Failure Reasons
# --------------------------------------------------

st.subheader("Failure Reasons")

failures = {}

for checks in df["failed_checks"]:

    for check in checks:

        failures[check] = failures.get(check, 0) + 1

if failures:

    failure_df = (
        pd.DataFrame(
            {
                "Reason": failures.keys(),
                "Count": failures.values(),
            }
        )
        .sort_values(
            "Count",
            ascending=False,
        )
    )

    fig = px.bar(
        failure_df,
        x="Reason",
        y="Count",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    st.dataframe(
        failure_df,
        width="stretch",
        hide_index=True,
    )

else:

    st.success("No failed checks found.")

st.divider()

# --------------------------------------------------
# Raw Analytics Table
# --------------------------------------------------

st.subheader("Benchmark Data")

st.dataframe(
    df,
    width="stretch",
    hide_index=True,
)