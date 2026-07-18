from agent.providers.gemini import GeminiLLM
from agent.providers.models import (
    ConversationTurn,
    Role,
    ToolResult,
    FinishReason,
)

import pytest

def test_basic_generation():
    """
    Verify Gemini can generate a normal text response.
    """

    llm = GeminiLLM(
        tools=[],
    )

    response = llm.generate(
        conversation=[
            ConversationTurn(
                role=Role.USER,
                content="Say hello in one sentence.",
            )
        ]
    )

    print("\n=== Basic Generation ===")
    print(response)

    assert response is not None
    assert response.text != ""
    assert response.tool_calls == []
    assert response.finish_reason == FinishReason.STOP


def test_tool_call():
    """
    Verify Gemini decides to call the get_weather tool.
    """

    llm = GeminiLLM(
        tools=["get_weather"],
    )

    response = llm.generate(
        conversation=[
            ConversationTurn(
                role=Role.USER,
                content="What's the weather in Hyderabad?",
            )
        ]
    )

    print("\n=== Tool Call ===")
    print(response)

    assert len(response.tool_calls) == 1
    assert response.finish_reason == FinishReason.TOOL_CALLS

    tool_call = response.tool_calls[0]

    assert tool_call.name == "get_weather"
    assert tool_call.args["city"] == "Hyderabad"


def test_tool_result_roundtrip():
    """
    Simulate a complete tool execution cycle.

    User
        ↓
    Gemini requests tool
        ↓
    Fake tool execution
        ↓
    Gemini produces final answer
    """

    llm = GeminiLLM(
        tools=["get_weather"],
    )

    conversation = [
        ConversationTurn(
            role=Role.USER,
            content="What's the weather in Hyderabad?",
        )
    ]

    response = llm.generate(conversation)

    print("\n=== Initial Tool Request ===")
    print(response)

    assert len(response.tool_calls) == 1

    tool_results = [
        ToolResult(
            name="get_weather",
            result={
                "temperature": 31,
                "condition": "Sunny",
            },
        )
    ]

    final_response = llm.generate(
        conversation=conversation,
        tool_results=tool_results,
    )

    print("\n=== Final Response ===")
    print(final_response)

    assert final_response.text != ""
    assert final_response.finish_reason == FinishReason.STOP
    assert final_response.tool_calls == []


def test_multi_turn_conversation():
    """
    Verify Gemini correctly receives conversation history.
    """

    llm = GeminiLLM(
        tools=[],
    )

    response = llm.generate(
        conversation=[
            ConversationTurn(
                role=Role.USER,
                content="My favourite language is Python.",
            ),
            ConversationTurn(
                role=Role.ASSISTANT,
                content="Got it! I'll remember that for this conversation.",
            ),
            ConversationTurn(
                role=Role.USER,
                content="What's my favourite language?",
            ),
        ]
    )

    print("\n=== Multi-turn Conversation ===")
    print(response)

    assert "Python" in response.text


def test_no_tools_available():
    """
    Verify Gemini answers normally when no tools are provided.
    """

    llm = GeminiLLM(
        tools=[],
    )

    response = llm.generate(
        conversation=[
            ConversationTurn(
                role=Role.USER,
                content="What is the capital of France?",
            )
        ]
    )

    print("\n=== No Tools Available ===")
    print(response)

    assert response.text != ""
    assert response.tool_calls == []
    assert response.finish_reason == FinishReason.STOP


def test_invalid_tool_name():
    """
    Ensure invalid tool names are rejected immediately.
    """

    with pytest.raises(ValueError):
        GeminiLLM(
            tools=["definitely_not_a_real_tool"],
        )

def test_multiple_generations():
    llm = GeminiLLM(tools=[])

    response1 = llm.generate(
        [
            ConversationTurn(
                role=Role.USER,
                content="Say hello."
            )
        ]
    )

    response2 = llm.generate(
        [
            ConversationTurn(
                role=Role.USER,
                content="What is 2 + 2?"
            )
        ]
    )

    assert response1.text != ""
    assert response2.text != ""