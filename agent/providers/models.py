"""
Provider-independent models shared across the agent.

Every provider converts its SDK-specific objects into these
common models so that the rest of the agent remains completely
provider-independent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(Enum):
    """
    Supported conversation roles.
    """

    USER = "user"
    ASSISTANT = "assistant"


class FinishReason(Enum):
    """
    Reason why generation stopped.
    """

    STOP = "stop"
    TOOL_CALLS = "tool_calls"
    MAX_TOKENS = "max_tokens"
    ERROR = "error"


@dataclass(slots=True)
class ConversationTurn:
    """
    A conversational exchange between the user and the assistant.
    """

    role: Role
    content: str


@dataclass(slots=True)
class ToolCall:
    """
    Tool requested by the model.
    """

    name: str
    args: dict[str, Any]


@dataclass(slots=True)
class ToolResult:
    name: str
    result: Any
    success: bool = True


@dataclass(slots=True)
class LLMResponse:
    """
    Provider-independent model response.
    """

    text: str | None = None

    tool_calls: list[ToolCall] = field(default_factory=list)

    finish_reason: FinishReason = FinishReason.STOP