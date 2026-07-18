import pytest
from agent.providers.base import BaseLLM
from agent.providers.models import LLMResponse, FinishReason
from tasks.models import (
    Task,
    TaskCategory,
    Difficulty,
    ExpectedToolCall,
    SuccessCriteria,
)


class DummyLLM(BaseLLM):
    def __init__(self, responses):
        self._responses = list(responses)

    def generate(self, conversation, tool_results=None):
        if not self._responses:
            return LLMResponse(text="Done", finish_reason=FinishReason.STOP)
        return self._responses.pop(0)

@pytest.fixture
def dummy_llm_factory():
    def _factory(responses):
        return DummyLLM(responses)
    return _factory


@pytest.fixture
def sample_task():
    """
    Base benchmark task used by mutation tests.
    """

    return Task(
        id="task_001",

        category=TaskCategory.TOOL_SELECTION,

        prompt="Find today's weather.",

        available_tools=[
            "get_weather",
            "search_web",
        ],

        expected_plan=[
            "Call get_weather"
        ],

        expected_tool_calls=[
            ExpectedToolCall(
                tool="get_weather",
                args_contains=None,
            )
        ],

        success_criteria=SuccessCriteria(),

        difficulty=Difficulty.BASE,
    )