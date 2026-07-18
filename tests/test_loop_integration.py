import os
import pytest

from agent.llm import create_llm
from agent.loop import ReActLoop
from agent.providers.models import ConversationTurn, Role


pytestmark = pytest.mark.skipif(
    "GEMINI_API_KEY" not in os.environ,
    reason="Requires Gemini API key",
)


def test_weather_query():
    llm = create_llm(
        provider="gemini",
        tools=["get_weather"],
    )

    loop = ReActLoop(llm)

    trace = loop.run(
        task_id="integration-weather",
        conversation=[
            ConversationTurn(
                Role.USER,
                "What is the weather in Hyderabad?"
            )
        ],
    )

    assert trace.successful
    assert trace.final_answer is not None
    assert len(trace.final_answer) > 0
