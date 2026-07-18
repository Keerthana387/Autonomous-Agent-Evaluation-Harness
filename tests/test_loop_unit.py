from unittest.mock import patch

import pytest

from agent.loop import ReActLoop
from agent.providers.base import BaseLLM
from agent.providers.models import (
    ConversationTurn,
    FinishReason,
    LLMResponse,
    Role,
    ToolCall,
)
from agent.trace import Trace


# -------------------------------------------------------------------------
# Existing Tests
# -------------------------------------------------------------------------


def test_no_tool_response(dummy_llm_factory):
    llm = dummy_llm_factory(
        [
            LLMResponse(
                text="Hello",
                finish_reason=FinishReason.STOP,
            )
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="t1",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Hi",
            )
        ],
    )

    assert trace.successful
    assert trace.final_answer == "Hello"
    assert trace.num_steps == 1
    assert trace.num_tool_calls == 0


@patch("agent.loop.execute_tool")
def test_single_tool_call(
    mock_execute_tool,
    dummy_llm_factory,
):
    mock_execute_tool.return_value = "Sunny"

    llm = dummy_llm_factory(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="get_weather",
                        args={"city": "Hyderabad"},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                text="Weather is Sunny",
                finish_reason=FinishReason.STOP,
            ),
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="t2",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Weather?",
            )
        ],
    )

    mock_execute_tool.assert_called_once()

    assert trace.num_tool_calls == 1
    assert trace.final_answer == "Weather is Sunny"


@patch("agent.loop.execute_tool")
def test_tool_failure(
    mock_execute_tool,
    dummy_llm_factory,
):
    mock_execute_tool.side_effect = RuntimeError("boom")

    llm = dummy_llm_factory(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="bad_tool",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                text="Recovered",
                finish_reason=FinishReason.STOP,
            ),
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="t3",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Test",
            )
        ],
    )

    assert trace.num_tool_calls == 1

    execution = trace.steps[0].executions[0]

    assert execution.tool_result.success is False


def test_trace_json_roundtrip():
    trace = Trace(task_id="abc")

    json_data = trace.to_json()

    restored = Trace.from_json(json_data)

    assert restored.task_id == trace.task_id


# -------------------------------------------------------------------------
# Helper Classes
# -------------------------------------------------------------------------


class FailingLLM(BaseLLM):
    def generate(
        self,
        conversation,
        tool_results=None,
    ):
        raise RuntimeError("LLM crashed")


# -------------------------------------------------------------------------
# New Tests
# -------------------------------------------------------------------------


@patch("agent.loop.execute_tool")
def test_multiple_tool_calls_same_step(
    mock_execute_tool,
    dummy_llm_factory,
):
    mock_execute_tool.side_effect = [
        "Sunny",
        "25C",
    ]

    llm = dummy_llm_factory(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="weather",
                        args={},
                    ),
                    ToolCall(
                        name="temperature",
                        args={},
                    ),
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                text="Done",
                finish_reason=FinishReason.STOP,
            ),
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="multi-tool",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Tell me about today's weather",
            )
        ],
    )

    assert mock_execute_tool.call_count == 2

    assert trace.num_tool_calls == 2

    assert len(trace.steps[0].executions) == 2

    assert trace.final_answer == "Done"


@patch("agent.loop.execute_tool")
def test_multiple_reasoning_iterations(
    mock_execute_tool,
    dummy_llm_factory,
):
    mock_execute_tool.side_effect = [
        "A",
        "B",
    ]

    llm = dummy_llm_factory(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="tool1",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="tool2",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                text="Finished",
                finish_reason=FinishReason.STOP,
            ),
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="multi-step",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Run",
            )
        ],
    )

    assert trace.num_steps == 3

    assert trace.num_tool_calls == 2

    assert trace.final_answer == "Finished"


@patch("agent.loop.execute_tool")
def test_max_steps_limit(
    mock_execute_tool,
    dummy_llm_factory,
):
    mock_execute_tool.return_value = "ok"

    llm = dummy_llm_factory(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="loop",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="loop",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="loop",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
        ]
    )

    loop = ReActLoop(
        llm,
        max_steps=2,
    )

    trace = loop.run(
        task_id="limit",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Loop",
            )
        ],
    )

    assert trace.num_steps == 2


def test_empty_response(dummy_llm_factory):
    llm = dummy_llm_factory(
        [
            LLMResponse(
                text="",
                finish_reason=FinishReason.STOP,
            )
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="empty",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Hi",
            )
        ],
    )

    assert trace.successful

    assert trace.final_answer == ""


def test_llm_exception():
    loop = ReActLoop(FailingLLM())

    trace = loop.run(
        task_id="error",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Hi",
            )
        ],
    )

    assert trace.successful is False

    assert trace.error is not None

# -------------------------------------------------------------------------
# Additional Tests
# -------------------------------------------------------------------------


@patch("agent.loop.execute_tool")
def test_unknown_tool_execution(
    mock_execute_tool,
    dummy_llm_factory,
):
    mock_execute_tool.side_effect = ValueError(
        "Unknown tool"
    )

    llm = dummy_llm_factory(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="does_not_exist",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                text="Recovered",
                finish_reason=FinishReason.STOP,
            ),
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="unknown-tool",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Hello",
            )
        ],
    )

    execution = trace.steps[0].executions[0]

    assert execution.tool_result.success is False

    assert trace.final_answer == "Recovered"


class RecordingLLM(BaseLLM):
    """
    Records every tool_results argument passed to generate().
    """

    def __init__(self):
        self.calls = 0
        self.history = []

    def generate(
        self,
        conversation,
        tool_results=None,
    ):
        self.history.append(tool_results)

        self.calls += 1

        if self.calls == 1:
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="weather",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            )

        return LLMResponse(
            text="Done",
            finish_reason=FinishReason.STOP,
        )


@patch("agent.loop.execute_tool")
def test_tool_results_forwarded_between_iterations(
    mock_execute_tool,
):
    mock_execute_tool.return_value = "Sunny"

    llm = RecordingLLM()

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="tool-results",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Weather?",
            )
        ],
    )

    assert trace.successful

    assert len(llm.history) == 2

    assert llm.history[0] is None

    assert llm.history[1] is not None

    assert len(llm.history[1]) == 1

    assert llm.history[1][0].success is True


def test_trace_metrics():
    trace = Trace(task_id="metrics")

    assert trace.num_steps == 0

    assert trace.num_tool_calls == 0

    assert trace.num_failed_tool_calls == 0

    assert trace.successful

    trace.finish("Done")

    assert trace.final_answer == "Done"

    assert trace.duration_seconds >= 0


@patch("agent.loop.execute_tool")
def test_trace_json_roundtrip_multiple_steps(
    mock_execute_tool,
    dummy_llm_factory,
):
    mock_execute_tool.side_effect = [
        "A",
        "B",
    ]

    llm = dummy_llm_factory(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="tool1",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="tool2",
                        args={},
                    )
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                text="Finished",
                finish_reason=FinishReason.STOP,
            ),
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="serialize",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Go",
            )
        ],
    )

    restored = Trace.from_json(
        trace.to_json()
    )

    assert restored.task_id == trace.task_id

    assert restored.num_steps == trace.num_steps

    assert restored.num_tool_calls == trace.num_tool_calls

    assert restored.final_answer == trace.final_answer


def test_initial_conversation_preserved(
    dummy_llm_factory,
):
    conversation = [
        ConversationTurn(
            Role.USER,
            "Original",
        )
    ]

    llm = dummy_llm_factory(
        [
            LLMResponse(
                text="Done",
                finish_reason=FinishReason.STOP,
            )
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="conversation",
        conversation=conversation,
    )

    assert len(trace.initial_conversation) == 1

    assert (
        trace.initial_conversation[0].content
        == "Original"
    )


@patch("agent.loop.execute_tool")
def test_tool_execution_order(
    mock_execute_tool,
    dummy_llm_factory,
):
    mock_execute_tool.side_effect = [
        "A",
        "B",
        "C",
    ]

    llm = dummy_llm_factory(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="A",
                        args={},
                    ),
                    ToolCall(
                        name="B",
                        args={},
                    ),
                    ToolCall(
                        name="C",
                        args={},
                    ),
                ],
                finish_reason=FinishReason.TOOL_CALLS,
            ),
            LLMResponse(
                text="Done",
                finish_reason=FinishReason.STOP,
            ),
        ]
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="ordering",
        conversation=[
            ConversationTurn(
                Role.USER,
                "Run",
            )
        ],
    )

    executions = trace.steps[0].executions

    assert executions[0].tool_call.name == "A"

    assert executions[1].tool_call.name == "B"

    assert executions[2].tool_call.name == "C"

    assert trace.final_answer == "Done"


def test_trace_repr():
    trace = Trace(
        task_id="repr-test",
    )

    text = repr(trace)

    assert "repr-test" in text

    assert "Trace" in text