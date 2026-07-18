"""
Gemini provider implementation.

This module contains all Gemini-specific logic:
- SDK initialization
- Tool schema conversion
- Conversation conversion
- Response parsing
- API communication

No Gemini SDK objects leave this file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from agent.providers.base import BaseLLM
from agent.providers.models import (
    ConversationTurn,
    ToolCall,
    ToolResult,
    LLMResponse,
    FinishReason,
    Role,
)

from tools.registry import get_tool_subset


# ----------------------------------------------------------------------
# Environment
# ----------------------------------------------------------------------

load_dotenv(Path(__file__).parent / ".env")


class GeminiLLM(BaseLLM):
    """
    Gemini implementation of the BaseLLM interface.

    Every Gemini-specific implementation detail is encapsulated
    inside this class.
    """

    DEFAULT_MODEL = "gemini-3.1-flash-lite"

    def __init__(
        self,
        tools: list[str],
        model: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        tools
            List of tool names available for the current task.

        model
            Optional Gemini model override.
        """

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not found in providers/.env"
            )

        self._client = genai.Client(
            api_key=api_key,
        )

        self._model = model or self.DEFAULT_MODEL

        # Cache Gemini tool definitions.
        self._tools = self._build_tools(tools)

    # ------------------------------------------------------------------
    # Tool Conversion
    # ------------------------------------------------------------------

    def _convert_parameters(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert our registry parameter format into a JSON Schema
        understood by Gemini.

        Registry format
        ---------------
        {
            "city": {
                "type": "string",
                "required": True
            }
        }

        Output
        ------
        {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string"
                }
            },
            "required": ["city"]
        }
        """

        properties: dict[str, Any] = {}
        required: list[str] = []

        for name, info in parameters.items():

            properties[name] = {
                "type": info["type"],
            }

            if info.get("required", False):
                required.append(name)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        return schema

    def _build_tools(
        self,
        tool_names: list[str],
    ) -> list[types.Tool]:
        """
        Build Gemini tool definitions from the project's tool registry.

        Parameters
        ----------
        tool_names
            List of tool names available for this task.

        Returns
        -------
        list[types.Tool]
            Gemini tool definitions that can be supplied to
            GenerateContentConfig.
        """

        tool_defs = get_tool_subset(tool_names)

        if not tool_defs:
            return []

        declarations: list[types.FunctionDeclaration] = []

        for tool_name, tool in tool_defs.items():

            declaration = types.FunctionDeclaration(
                name=tool_name,
                description=tool["description"],
                parameters_json_schema=self._convert_parameters(
                    tool["parameters"]
                ),
            )

            declarations.append(declaration)

        return [
            types.Tool(
                function_declarations=declarations,
            )
        ]

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self,
        conversation: list[ConversationTurn],
        tool_results: list[ToolResult] | None = None,
    ) -> LLMResponse:
        """
        Send the conversation to Gemini and return the model response.

        Parameters
        ----------
        conversation
            Conversation history.

        tool_results
            Results from tools executed by the agent during the
            previous iteration.
        """

        contents: list[types.Content] = []

        # --------------------------------------------------------------
        # Conversation History
        # --------------------------------------------------------------

        for turn in conversation:

            role = "user" if turn.role == Role.USER else "model"

            contents.append(
                types.Content(
                    role=role,
                    parts=[
                        types.Part.from_text(
                            text=turn.content
                        )
                    ],
                )
            )

        # --------------------------------------------------------------
        # Tool Responses
        # --------------------------------------------------------------

        if tool_results:

            for result in tool_results:

                contents.append(
                    types.Content(
                        role="tool",
                        parts=[
                            types.Part.from_function_response(
                                name=result.name,
                                response={
                                    "result": result.result
                                },
                            )
                        ],
                    )
                )

        # --------------------------------------------------------------
        # Generate
        # --------------------------------------------------------------

        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=self._tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True,
                ),
            ),
        )

        # --------------------------------------------------------------
        # Extract Tool Calls
        # --------------------------------------------------------------

        tool_calls: list[ToolCall] = []

        if response.function_calls:

            for call in response.function_calls:

                tool_calls.append(
                    ToolCall(
                        name=call.name,
                        args=dict(call.args),
                    )
                )

        # --------------------------------------------------------------
        # Finish Reason
        # --------------------------------------------------------------

        finish_reason = FinishReason.STOP

        if tool_calls:
            finish_reason = FinishReason.TOOL_CALLS

        elif (
            hasattr(response, "candidates")
            and response.candidates
        ):
            reason = response.candidates[0].finish_reason

            if str(reason).endswith("MAX_TOKENS"):
                finish_reason = FinishReason.MAX_TOKENS

        # --------------------------------------------------------------
        # Return
        # --------------------------------------------------------------

        return LLMResponse(
            text=response.text or "",
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )
    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"GeminiLLM("
            f"model='{self._model}', "
            f"tools={len(self._tools)}"
            f")"
        )