"""
Abstract interface for all LLM providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent.providers.models import (
    ConversationTurn,
    ToolResult,
    LLMResponse,
)


class BaseLLM(ABC):
    """
    Abstract interface implemented by every provider.
    """

    @abstractmethod
    def generate(
        self,
        conversation: list[ConversationTurn],
        tool_results: list[ToolResult] | None = None,
    ) -> LLMResponse:
        """
        Generate the next model response.

        Parameters
        ----------
        conversation
            User/assistant conversation history.

        tool_results
            Tool results that should be supplied back to
            the provider for the next reasoning step.
        """
        raise NotImplementedError