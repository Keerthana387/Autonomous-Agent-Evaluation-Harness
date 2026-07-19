import streamlit as st

from database import (
    get_all_tasks,
    get_task_report,
)

from sidebar import render_sidebar

render_sidebar()

# --------------------------------------------------
# Page
# --------------------------------------------------

st.title("🔍 Trace Viewer")

tasks = get_all_tasks()

if tasks.empty:
    st.warning("No benchmark tasks found.")
    st.stop()

task_id = st.selectbox(
    "Select Task",
    tasks["task_id"].tolist(),
)

report = get_task_report(task_id)

if report is None:
    st.error("Task not found.")
    st.stop()

trace = report.get("trace")
score = report.get("score")

if trace is None:
    st.error("Trace not found.")
    st.stop()

if score is None:
    st.error("Score not found.")
    st.stop()

# --------------------------------------------------
# Header
# --------------------------------------------------

if score["passed"]:
    st.success("✅ Benchmark Passed")
else:
    st.error("❌ Benchmark Failed")

c1, c2 = st.columns(2)

with c1:
    st.metric("Task ID", task_id)

with c2:
    st.metric(
        "Mutation",
        trace.get("mutation_type") or "Base Task"
    )

st.divider()

# --------------------------------------------------
# User Prompt
# --------------------------------------------------

st.subheader("👤 User Prompt")

conversation = trace.get("initial_conversation", [])

user_prompt = ""

for message in conversation:
    if message["role"] == "user":
        user_prompt = message["content"]
        break

st.info(user_prompt)

st.divider()

# --------------------------------------------------
# Reasoning Timeline
# --------------------------------------------------

st.subheader("🧠 Reasoning Timeline")

steps = trace.get("steps", [])

if not steps:
    st.warning("No reasoning steps recorded.")

for step in steps:

    with st.expander(
        f"Step {step['step']}",
        expanded=True,
    ):

        llm = step["llm_response"]

        st.markdown("### 🤖 LLM Response")

        if llm.get("text"):
            st.write(llm["text"])
        else:
            st.caption("No text response (tool call only).")

        tool_calls = llm.get("tool_calls", [])

        if tool_calls:

            st.markdown("### 🔧 Tool Calls")

            for tool in tool_calls:
                st.json(tool)

        executions = step.get("executions", [])

        if executions:

            st.markdown("### 📦 Tool Results")

            for execution in executions:
                st.json(execution["tool_result"])

st.divider()

# --------------------------------------------------
# Final Answer
# --------------------------------------------------

st.subheader("💬 Final Answer")

if trace.get("final_answer"):
    st.success(trace["final_answer"])
else:
    st.warning("No final answer generated.")

# --------------------------------------------------
# Error
# --------------------------------------------------

if trace.get("error"):

    st.divider()

    st.subheader("⚠ Execution Error")

    st.error(trace["error"])

# --------------------------------------------------
# Evaluation
# --------------------------------------------------

st.divider()

st.subheader("📋 Evaluation")

evaluation_fields = [
    "correct_tools_used",
    "forbidden_tools_called",
    "planning_correct",
    "clarification_requested",
    "handled_tool_failure",
    "prompt_injection_resisted",
    "grounded",
]

for field in evaluation_fields:

    value = score.get(field)

    if value is None:
        continue

    icon = "✅" if value else "❌"

    st.write(
        f"{icon} **{field.replace('_', ' ').title()}**"
    )

st.divider()

st.subheader("❌ Failed Checks")

failed = score.get("failed_checks", [])

if failed:

    for check in failed:
        st.error(check)

else:
    st.success("No failed checks.")

# --------------------------------------------------
# Raw JSON
# --------------------------------------------------

with st.expander("Raw Trace JSON"):
    st.json(trace)

with st.expander("Raw Score JSON"):
    st.json(score)