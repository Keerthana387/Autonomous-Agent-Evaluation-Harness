"""
Factory for creating LLM providers.
"""

from __future__ import annotations

from agent.providers.base import BaseLLM
from agent.providers.gemini import GeminiLLM


def create_llm(
    provider: str = "gemini",
    tools: list | None = None,
) -> BaseLLM:

    provider = provider.lower()

    if provider == "gemini":
        return GeminiLLM(tools or [])

    raise ValueError(f"Unsupported provider: {provider}")