from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json


@dataclass
class Score:
    """
    Evaluation results for a single benchmark task.

    Rule-based metrics are computed first.
    LLM-judge metrics are populated later by judge.py.
    """

    # =========================================================================
    # Task metadata
    # =========================================================================

    task_id: str

    agent_id: str | None = None

    base_task_id: str | None = None

    mutation_type: str | None = None

    # =========================================================================
    # Rule-based metrics
    # =========================================================================

    correct_tools_used: bool = False

    forbidden_tools_called: bool = False

    tool_precision: float = 0.0

    tool_recall: float = 0.0

    planning_correct: bool | None = None

    clarification_requested: bool | None = None

    handled_tool_failure: bool | None = None

    prompt_injection_resisted: bool | None = None

    # =========================================================================
    # LLM Judge metrics
    # =========================================================================

    grounded: bool | None = None

    judge_reasoning: str | None = None

    # =========================================================================
    # Overall result
    # =========================================================================

    passed: bool | None = None

    failed_checks: list[str] = field(default_factory=list)

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict:
        """Convert Score to a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Score":
        """Create a Score from a dictionary."""
        return cls(**data)

    def to_json(
        self,
        *,
        indent: int | None = 2,
    ) -> str:
        """Serialize Score to JSON."""
        return json.dumps(
            self.to_dict(),
            indent=indent,
        )

    @classmethod
    def from_json(
        cls,
        json_str: str,
    ) -> "Score":
        """Deserialize Score from JSON."""
        return cls.from_dict(json.loads(json_str))