from tests.test_rules import (
    make_task,
    make_trace,
)

from scoring.rules import score_trace
from scoring.judge import judge_score


# ==========================================================
# Fake LLM
# ==========================================================

class FakeLLM:

    def generate(self, system_prompt, prompt):

        class Response:

            text = """
            {
                "grounded": true,
                "judge_reasoning": "The final answer is supported by the tool results."
            }
            """

        return Response()


class InvalidJSONLLM:

    def generate(self, system_prompt, prompt):

        class Response:

            text = "not json"

        return Response()


# ==========================================================
# Successful Judge
# ==========================================================

def test_judge_updates_score(monkeypatch):

    monkeypatch.setattr(
        "scoring.judge.create_llm",
        lambda provider="gemini": FakeLLM(),
    )

    task = make_task()

    trace = make_trace()

    score = score_trace(task, trace)

    judged = judge_score(
        task,
        trace,
        score,
    )

    assert judged.grounded is True

    assert judged.judge_reasoning == (
        "The final answer is supported by the tool results."
    )


# ==========================================================
# Invalid JSON
# ==========================================================

def test_invalid_json_response(monkeypatch):

    monkeypatch.setattr(
        "scoring.judge.create_llm",
        lambda provider="gemini": InvalidJSONLLM(),
    )

    task = make_task()

    trace = make_trace()

    score = score_trace(task, trace)

    judged = judge_score(
        task,
        trace,
        score,
    )

    assert judged.grounded is None

    assert "invalid json" in judged.judge_reasoning.lower()


# ==========================================================
# Existing Score Fields Preserved
# ==========================================================

def test_existing_fields_preserved(monkeypatch):

    monkeypatch.setattr(
        "scoring.judge.create_llm",
        lambda provider="gemini": FakeLLM(),
    )

    task = make_task()

    trace = make_trace()

    score = score_trace(task, trace)

    original_passed = score.passed
    original_precision = score.tool_precision

    judged = judge_score(
        task,
        trace,
        score,
    )

    assert judged.passed == original_passed

    assert judged.tool_precision == original_precision

    assert judged.grounded is True


# ==========================================================
# Judge Returns Same Object
# ==========================================================

def test_returns_same_score_object(monkeypatch):

    monkeypatch.setattr(
        "scoring.judge.create_llm",
        lambda provider="gemini": FakeLLM(),
    )

    task = make_task()

    trace = make_trace()

    score = score_trace(task, trace)

    judged = judge_score(
        task,
        trace,
        score,
    )

    assert judged is score