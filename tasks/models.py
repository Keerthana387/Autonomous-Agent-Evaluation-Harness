from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ==========================================================
# ENUMS
# ==========================================================

class TaskCategory(str, Enum):
    TOOL_SELECTION = "tool_selection"
    MULTI_STEP_CHAINING = "multi_step_chaining"
    AMBIGUOUS_INPUT = "ambiguous_input"
    ERROR_HANDLING = "error_handling"
    NO_TOOL_NEEDED = "no_tool_needed"


class Difficulty(str, Enum):
    BASE = "base"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class FailMode(str, Enum):
    TIMEOUT = "timeout"
    MALFORMED = "malformed"
    WRONG_DATA = "wrong_data"
    EMPTY = "empty"


# ==========================================================
# SUBMODELS
# ==========================================================

class ExpectedToolCall(BaseModel):
    tool: str
    args_contains: dict[str, Any] | None = None


class SuccessCriteria(BaseModel):
    final_answer_must_mention: list[str] = Field(default_factory=list)
    final_answer_should: list[str] = Field(default_factory=list)

    must_not_call: list[str] = Field(default_factory=list)

    requires_multi_step: bool = False
    should_request_clarification: bool = False
    should_handle_tool_failure: bool = False
    should_detect_unreasonable_result: bool = False
    must_resist_injection: bool = False


class FaultConfig(BaseModel):
    target_tool: str
    fail_mode: FailMode | None = None
    inject_text: str | None = None


# ==========================================================
# MAIN TASK MODEL
# ==========================================================

class Task(BaseModel):

    id: str

    base_task_id: str | None = None

    mutation_type: str | None = None

    category: TaskCategory

    prompt: str

    available_tools: list[str]

    expected_plan: list[str] = Field(default_factory=list)

    expected_tool_calls: list[ExpectedToolCall] = Field(default_factory=list)

    success_criteria: SuccessCriteria

    difficulty: Difficulty = Difficulty.BASE

    notes: str = ""

    fault_config: FaultConfig | None = None