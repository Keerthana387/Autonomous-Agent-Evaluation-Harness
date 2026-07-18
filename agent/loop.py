from __future__ import annotations

from copy import deepcopy

from agent.providers.base import BaseLLM
from agent.providers.models import (
    ConversationTurn,
    FinishReason,
    Role,
    ToolCall,
    ToolResult,
)
from agent.trace import Trace
from tools.registry import execute_tool


class ReActLoop:
    """
    Executes one complete ReAct reasoning loop.

    Responsibilities
    ----------------
    • Maintain conversation state
    • Call the LLM
    • Execute requested tools
    • Update the execution trace
    • Return the completed trace
    """

    DEFAULT_MAX_STEPS = 10

    def __init__(
        self,
        llm: BaseLLM,
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> None:
        self._llm = llm
        self._max_steps = max_steps

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        task_id: str,
        conversation: list[ConversationTurn],
        *,
        base_task_id: str | None = None,
        mutation_type: str | None = None,
    ) -> Trace:
        """
        Execute the complete ReAct loop.
        """

        trace = Trace(
            task_id=task_id,
            base_task_id=base_task_id,
            mutation_type=mutation_type,
            initial_conversation=deepcopy(conversation),
        )

        conversation = deepcopy(conversation)

        previous_tool_results: list[ToolResult] | None = None

        for _ in range(self._max_steps):
            try:
                response = self._llm.generate(
                    conversation=conversation,
                    tool_results=previous_tool_results,
                )
            except Exception as exc:
                trace.set_error(str(exc))
                return trace

            trace.add_step(response)

            if response.text:

                conversation.append(
                    ConversationTurn(
                        role=Role.ASSISTANT,
                        content=response.text,
                    )
                )

            if response.finish_reason != FinishReason.TOOL_CALLS:

                trace.finish(
                    response.text or ""
                )

                return trace

            previous_tool_results = self._execute_tool_calls(
                response.tool_calls,
                trace,
            )

        trace.set_error(
            f"Maximum reasoning steps ({self._max_steps}) exceeded."
        )

        return trace

    # ------------------------------------------------------------------
    # Tool Execution
    # ------------------------------------------------------------------

    def _execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
        trace: Trace,
    ) -> list[ToolResult]:
        """
        Execute every requested tool and record the results.
        """

        results: list[ToolResult] = []

        for call in tool_calls:

            try:

                output = execute_tool(
                    call.name,
                    call.args,
                )

                result = ToolResult(
                    name=call.name,
                    result=output,
                    success=True,
                )

            except Exception as exc:

                result = ToolResult(
                    name=call.name,
                    result=f"Tool execution failed: {exc}",
                    success=False,
                )

            trace.add_execution(
                call,
                result,
            )

            results.append(result)

        return results

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"ReActLoop("
            f"max_steps={self._max_steps})"
        )