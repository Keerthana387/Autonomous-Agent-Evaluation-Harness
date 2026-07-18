from agent.providers.models import (
    FinishReason,
    LLMResponse,
    ToolCall,
    ToolResult,
)
from agent.trace import Trace
from scoring.rules import score_trace
from tasks.models import (
    Difficulty,
    ExpectedToolCall,
    SuccessCriteria,
    Task,
    TaskCategory,
)


# ============================================================================
# Helpers
# ============================================================================


def make_task(
    *,
    expected_tools=None,
    expected_plan=None,
    success_criteria=None,
):

    return Task(
        id="task_001",
        category=TaskCategory.TOOL_SELECTION,
        prompt="Dummy task",
        available_tools=[
            "weather",
            "translate",
            "calendar",
        ],
        expected_tool_calls=expected_tools or [],
        expected_plan=expected_plan or [],
        success_criteria=success_criteria
        or SuccessCriteria(),
        difficulty=Difficulty.BASE,
    )


def make_trace(
    *,
    tool_names=None,
    failed_tools=None,
    final_answer="Done",
):

    trace = Trace(task_id="task_001")

    response = LLMResponse(
        text="thinking",
        tool_calls=[],
        finish_reason=FinishReason.TOOL_CALLS,
    )

    trace.add_step(response)

    tool_names = tool_names or []
    failed_tools = failed_tools or []

    for tool in tool_names:

        trace.add_execution(
            ToolCall(
                name=tool,
                args={},
            ),
            ToolResult(
                name=tool,
                success=tool not in failed_tools,
                result={},
            ),
        )

    trace.finish(final_answer)

    return trace


# ============================================================================
# Tool Metrics
# ============================================================================


def test_correct_tool_usage():

    task = make_task(
        expected_tools=[
            ExpectedToolCall(tool="weather"),
            ExpectedToolCall(tool="translate"),
        ]
    )

    trace = make_trace(
        tool_names=[
            "weather",
            "translate",
        ]
    )

    score = score_trace(task, trace)

    assert score.correct_tools_used is True
    assert score.forbidden_tools_called is False
    assert score.tool_precision == 1.0
    assert score.tool_recall == 1.0


def test_precision_and_recall():

    task = make_task(
        expected_tools=[
            ExpectedToolCall(tool="weather"),
            ExpectedToolCall(tool="translate"),
        ]
    )

    trace = make_trace(
        tool_names=[
            "weather",
            "calendar",
        ]
    )

    score = score_trace(task, trace)

    assert score.correct_tools_used is False

    assert score.tool_precision == 0.5
    assert score.tool_recall == 0.5


def test_forbidden_tool():

    task = make_task(
        expected_tools=[
            ExpectedToolCall(tool="weather"),
        ],
        success_criteria=SuccessCriteria(
            must_not_call=["calendar"],
        ),
    )

    trace = make_trace(
        tool_names=[
            "weather",
            "calendar",
        ]
    )

    score = score_trace(task, trace)

    assert score.forbidden_tools_called is True
    assert score.passed is False


# ============================================================================
# Planning
# ============================================================================


def test_expected_plan_matches():

    task = make_task(
        expected_plan=[
            "weather",
            "translate",
        ]
    )

    trace = make_trace(
        tool_names=[
            "weather",
            "translate",
        ]
    )

    score = score_trace(task, trace)

    assert score.planning_correct is True


def test_expected_plan_fails():

    task = make_task(
        expected_plan=[
            "weather",
            "translate",
        ]
    )

    trace = make_trace(
        tool_names=[
            "translate",
            "weather",
        ]
    )

    score = score_trace(task, trace)

    assert score.planning_correct is False


# ============================================================================
# Clarification
# ============================================================================


def test_clarification_requested():

    task = make_task(
        success_criteria=SuccessCriteria(
            should_request_clarification=True,
        )
    )

    trace = make_trace(
        final_answer="Could you clarify which city you mean?"
    )

    score = score_trace(task, trace)

    assert score.clarification_requested is True


# ============================================================================
# Tool Failure Handling
# ============================================================================


def test_handles_tool_failure():

    task = make_task(
        success_criteria=SuccessCriteria(
            should_handle_tool_failure=True,
        )
    )

    trace = make_trace(
        tool_names=["weather"],
        failed_tools=["weather"],
        final_answer="The tool failed. Please try again later.",
    )

    score = score_trace(task, trace)

    assert score.handled_tool_failure is True


# ============================================================================
# Prompt Injection
# ============================================================================


def test_prompt_injection_resisted():

    task = make_task(
        expected_tools=[
            ExpectedToolCall(tool="weather"),
        ],
        success_criteria=SuccessCriteria(
            must_resist_injection=True,
        ),
    )

    trace = make_trace(
        tool_names=["weather"],
    )

    score = score_trace(task, trace)

    assert score.prompt_injection_resisted is True


# ============================================================================
# Overall
# ============================================================================


def test_failed_checks_populated():

    task = make_task(
        expected_tools=[
            ExpectedToolCall(tool="weather"),
        ],
        success_criteria=SuccessCriteria(
            must_not_call=["calendar"],
        ),
    )

    trace = make_trace(
        tool_names=[
            "calendar",
        ]
    )

    score = score_trace(task, trace)

    assert score.passed is False

    assert "correct_tools_used" in score.failed_checks

    assert "forbidden_tools_called" in score.failed_checks