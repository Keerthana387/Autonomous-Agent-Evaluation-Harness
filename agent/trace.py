from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from .providers.models import (
    ConversationTurn,
    FinishReason,
    Role,
    ToolCall,
    ToolResult,
    LLMResponse,
    ToolCall,
    ToolResult,
)


# ============================================================================
# Tool Execution
# ============================================================================


@dataclass
class ToolExecution:
    """
    Represents one completed tool invocation.

    Explicitly pairs the ToolCall requested by the LLM with the
    ToolResult returned by the tool.
    """

    tool_call: ToolCall
    tool_result: ToolResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_call": asdict(self.tool_call),
            "tool_result": asdict(self.tool_result),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "ToolExecution":
        return cls(
            tool_call=ToolCall(**data["tool_call"]),
            tool_result=ToolResult(**data["tool_result"]),
        )


# ============================================================================
# Trace Step
# ============================================================================


@dataclass
class TraceStep:
    """
    Represents one iteration of the ReAct loop.

    A step contains

        • one LLM response
        • zero or more completed tool executions
        • completion timestamp
    """

    step: int

    llm_response: LLMResponse

    executions: list[ToolExecution] = field(
        default_factory=list
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def add_execution(
        self,
        tool_call: ToolCall,
        tool_result: ToolResult,
    ) -> None:
        """
        Record one completed tool execution.
        """

        self.executions.append(
            ToolExecution(
                tool_call=tool_call,
                tool_result=tool_result,
            )
        )

    @property
    def num_tool_calls(self) -> int:
        return len(self.executions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "llm_response": {
                "text": self.llm_response.text,
                "tool_calls": [
                    {
                        "name": call.name,
                        "args": call.args,
                    }
                    for call in self.llm_response.tool_calls
                ],
                "finish_reason": self.llm_response.finish_reason.value,
            },
            "executions": [
                execution.to_dict()
                for execution in self.executions
            ],
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "TraceStep":
        """
        Reconstruct a TraceStep from its serialized representation.
        """

        llm_data = data["llm_response"]

        llm_response = LLMResponse(
            text=llm_data.get("text", ""),
            tool_calls=[
                ToolCall(**call)
                for call in llm_data.get("tool_calls", [])
            ],
            finish_reason=FinishReason(
                llm_data["finish_reason"]
            ),
        )

        step = cls(
            step=data["step"],
            llm_response=llm_response,
            timestamp=datetime.fromisoformat(
                data["timestamp"]
            ),
        )

        step.executions = [
            ToolExecution.from_dict(execution)
            for execution in data.get(
                "executions",
                [],
            )
        ]

        return step


# ============================================================================
# Trace
# ============================================================================


@dataclass
class Trace:
    """
    Represents one complete execution of an agent.

    The trace follows an event-sourced design.

    The initial conversation is stored once.

    Every subsequent interaction is recorded as a sequence of
    TraceSteps, each containing the LLM response together with the
    resulting tool executions.
    """

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    task_id: str

    agent_id: str = "react_v1"

    base_task_id: str | None = None

    mutation_type: str | None = None

    # ------------------------------------------------------------------
    # Initial State
    # ------------------------------------------------------------------

    initial_conversation: list[
        ConversationTurn
    ] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    steps: list[TraceStep] = field(
        default_factory=list
    )

    final_answer: str | None = None

    error: str | None = None

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------

    started_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    finished_at: datetime | None = None

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def add_step(
        self,
        llm_response: LLMResponse,
    ) -> TraceStep:
        """
        Create a new reasoning step.

        Returns the created TraceStep so callers can attach
        ToolExecution objects as tools complete.
        """

        step = TraceStep(
            step=len(self.steps),
            llm_response=llm_response,
        )

        self.steps.append(step)

        return step

    def finish(
        self,
        final_answer: str,
    ) -> None:
        """
        Mark execution as successfully completed.
        """

        self.final_answer = final_answer
        self.finished_at = datetime.now(UTC)

    def set_error(
        self,
        error: Exception | str,
    ) -> None:
        """
        Mark execution as failed.
        """

        self.error = str(error)
        self.finished_at = datetime.now(UTC)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the trace into a JSON-serializable dictionary.
        """

        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "base_task_id": self.base_task_id,
            "mutation_type": self.mutation_type,
            "initial_conversation": [
                {
                    "role": turn.role.value,
                    "content": turn.content,
                }
                for turn in self.initial_conversation
            ],
            "steps": [
                step.to_dict()
                for step in self.steps
            ],
            "final_answer": self.final_answer,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at is not None
                else None
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Trace":
        """
        Reconstruct a Trace object from a serialized dictionary.
        """

        trace = cls(
            task_id=data["task_id"],
            agent_id=data.get("agent_id", "react_v1"),
            base_task_id=data.get("base_task_id"),
            mutation_type=data.get("mutation_type"),
            initial_conversation=[
                ConversationTurn(
                    role=Role(turn["role"]),
                    content=turn["content"],
                )
                for turn in data.get(
                    "initial_conversation",
                    []
                )
            ],
            final_answer=data.get("final_answer"),
            error=data.get("error"),
            started_at=datetime.fromisoformat(
                data["started_at"]
            ),
            finished_at=(
                datetime.fromisoformat(data["finished_at"])
                if data.get("finished_at")
                else None
            ),
        )

        trace.steps = [
            TraceStep.from_dict(step)
            for step in data.get("steps", [])
        ]

        return trace

    def to_json(
        self,
        *,
        indent: int | None = 2,
    ) -> str:
        """
        Serialize the trace to a JSON string.
        """

        import json

        return json.dumps(
            self.to_dict(),
            indent=indent,
        )

    @classmethod
    def from_json(
        cls,
        json_string: str,
    ) -> "Trace":
        """
        Deserialize a trace from a JSON string.
        """

        import json

        return cls.from_dict(
            json.loads(json_string)
        )

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    @property
    def duration_seconds(self) -> float | None:
        """
        Total execution duration in seconds.
        """

        if self.finished_at is None:
            return None

        return (
            self.finished_at - self.started_at
        ).total_seconds()

    @property
    def successful(self) -> bool:
        """
        Whether execution completed successfully.
        """

        return self.error is None

    @property
    def num_steps(self) -> int:
        """
        Number of reasoning iterations.
        """

        return len(self.steps)

    @property
    def num_tool_calls(self) -> int:
        """
        Total number of tool executions.
        """

        return sum(
            step.num_tool_calls
            for step in self.steps
        )

    @property
    def num_failed_tool_calls(self) -> int:
        """
        Number of failed tool executions.
        """

        return sum(
            1
            for step in self.steps
            for execution in step.executions
            if not execution.tool_result.success
        )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Trace("
            f"task_id={self.task_id!r}, "
            f"agent_id={self.agent_id!r}, "
            f"steps={self.num_steps}, "
            f"tool_calls={self.num_tool_calls}, "
            f"successful={self.successful})"
        )

    def add_execution(
        self,
        tool_call: ToolCall,
        tool_result: ToolResult,
    ) -> None:
        """
        Add a tool execution to the most recent reasoning step.
        """

        if not self.steps:
            raise RuntimeError(
                "Cannot record a tool execution before a trace step exists."
            )

        self.steps[-1].add_execution(
            tool_call,
            tool_result,
        )