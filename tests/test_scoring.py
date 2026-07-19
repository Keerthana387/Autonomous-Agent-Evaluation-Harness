from pathlib import Path

from harness.db import (
    close_db,
    get_all_scores,
    get_score,
    init_db,
    save_score,
    save_trace,
    score_count,
)

from scoring.rules import score_trace
from scoring.run_scoring import score_connection

# Reuse the working helpers from test_rules.py
from tests.test_rules import (
    make_task,
    make_trace,
)


# ==========================================================
# Rule Scoring + Database
# ==========================================================

def test_score_save_and_load(tmp_path):

    conn = init_db(tmp_path / "test.db")

    task = make_task()

    trace = make_trace()

    score = score_trace(task, trace)

    save_score(conn, score)

    loaded = get_score(conn, score.task_id)

    assert loaded is not None
    assert loaded.to_dict() == score.to_dict()

    close_db(conn)


# ==========================================================
# Multiple Scores
# ==========================================================

def test_multiple_scores(tmp_path):

    conn = init_db(tmp_path / "test.db")

    for i in range(5):

        task = make_task()

        task.id = f"task_{i}"

        trace = make_trace()

        trace.task_id = f"task_{i}"

        score = score_trace(task, trace)

        save_score(conn, score)

    assert score_count(conn) == 5

    scores = get_all_scores(conn)

    assert len(scores) == 5

    close_db(conn)


# ==========================================================
# Replace Existing Score
# ==========================================================

def test_replace_existing_score(tmp_path):

    conn = init_db(tmp_path / "test.db")

    task = make_task()

    trace = make_trace()

    score = score_trace(task, trace)

    save_score(conn, score)

    score.passed = False

    save_score(conn, score)

    loaded = get_score(conn, score.task_id)

    assert loaded is not None
    assert loaded.passed is False

    assert score_count(conn) == 1

    close_db(conn)


# ==========================================================
# Empty Database
# ==========================================================

def test_empty_database(tmp_path):

    conn = init_db(tmp_path / "test.db")

    assert score_count(conn) == 0

    assert get_all_scores(conn) == []

    close_db(conn)


# ==========================================================
# score_connection()
# ==========================================================

def test_score_connection(monkeypatch, tmp_path):

    conn = init_db(tmp_path / "test.db")

    trace = make_trace()

    save_trace(conn, trace)

    task = make_task()

    monkeypatch.setattr(
        "scoring.run_scoring.load_all_tasks",
        lambda _: [task],
    )

    scored = score_connection(
        conn,
        [Path("unused")],
    )

    assert scored == 1

    assert score_count(conn) == 1

    loaded = get_score(conn, "task_001")

    assert loaded is not None

    close_db(conn)


# ==========================================================
# Missing Task
# ==========================================================

def test_missing_task(monkeypatch, tmp_path):

    conn = init_db(tmp_path / "test.db")

    save_trace(conn, make_trace())

    monkeypatch.setattr(
        "scoring.run_scoring.load_all_tasks",
        lambda _: [],
    )

    scored = score_connection(
        conn,
        [Path("unused")],
    )

    assert scored == 0

    assert score_count(conn) == 0

    close_db(conn)