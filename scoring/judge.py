"""
LLM-based evaluation of benchmark traces.

This module augments deterministic rule-based scores with semantic
evaluation performed by an LLM.
"""

from __future__ import annotations

import json

from agent.llm import create_llm
from scoring.models import Score
from tasks.models import Task
from agent.trace import Trace


# ============================================================================
# Prompt
# ============================================================================

SYSTEM_PROMPT = """
You are an impartial benchmark evaluator.

You will receive:

1. A benchmark task.
2. The execution trace.
3. A deterministic evaluation score.

Your job is ONLY to evaluate semantic quality.

Return JSON only.

Required JSON format:

{
    "grounded": true,
    "judge_reasoning": "short explanation"
}
"""


def apply_judge_result(score: Score, data: dict) -> Score:
    score.grounded = data.get("grounded")
    score.judge_reasoning = data.get("judge_reasoning")
    return score

# ============================================================================
# Public API
# ============================================================================


def judge_score(
    task: Task,
    trace: Trace,
    score: Score,
    *,
    provider: str = "gemini",
) -> Score:
    """
    Use an LLM to augment an existing Score.
    """

    llm = create_llm(provider)

    prompt = _build_prompt(
        task,
        trace,
        score,
    )

    response = llm.generate(
        SYSTEM_PROMPT,
        prompt,
    )

    data = _parse_response(
        response.text,
    )

    return apply_judge_result(score, data)


# ============================================================================
# Prompt Construction
# ============================================================================


def _build_prompt(
    task: Task,
    trace: Trace,
    score: Score,
) -> str:

    return f"""
TASK

{task.model_dump_json(indent=2)}

TRACE

{trace.to_json(indent=2)}

RULE SCORE

{score.to_json(indent=2)}
"""


# ============================================================================
# Parsing
# ============================================================================


def _parse_response(
    text: str,
) -> dict:

    try:
        return json.loads(text)

    except Exception:

        return {
            "grounded": None,
            "judge_reasoning": (
                "Judge returned invalid JSON."
            ),
        }