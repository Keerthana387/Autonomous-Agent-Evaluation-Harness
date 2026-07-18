from pathlib import Path

from agent.trace import Trace
from harness.db import (
    init_db,
    save_trace,
    get_trace,
    get_all_traces,
    clear_traces,
    trace_count,
    save_score,
    get_score,
    get_all_scores,
    clear_scores,
    score_count,
    close_db,
)

from scoring.models import Score


# ==========================================================
# Helper
# ==========================================================

def make_trace(task_id: str = "task_001") -> Trace:

    trace = Trace(task_id=task_id)

    trace.finish("Finished successfully")

    return trace

# ==========================================================
# Score Helper
# ==========================================================

def make_score(task_id: str = "task_001") -> Score:

    return Score(
        task_id=task_id,
        agent_id="react_v1",
        passed=True,
        correct_tools_used=True,
        tool_precision=1.0,
        tool_recall=1.0,
    )

# ==========================================================
# Database initialization
# ==========================================================

def test_init_db(tmp_path):

    db_path = tmp_path / "test.db"

    conn = init_db(db_path)

    assert db_path.exists()

    close_db(conn)


# ==========================================================
# Save / Load
# ==========================================================

def test_save_and_get_trace(tmp_path):

    conn = init_db(tmp_path / "test.db")

    trace = make_trace()

    save_trace(conn, trace)

    loaded = get_trace(conn, trace.task_id)

    assert loaded is not None

    assert loaded.task_id == trace.task_id

    assert loaded.final_answer == trace.final_answer

    close_db(conn)


# ==========================================================
# Multiple traces
# ==========================================================

def test_get_all_traces(tmp_path):

    conn = init_db(tmp_path / "test.db")

    for i in range(5):

        save_trace(
            conn,
            make_trace(f"task_{i}")
        )

    traces = get_all_traces(conn)

    assert len(traces) == 5

    close_db(conn)


# ==========================================================
# Count
# ==========================================================

def test_trace_count(tmp_path):

    conn = init_db(tmp_path / "test.db")

    assert trace_count(conn) == 0

    save_trace(
        conn,
        make_trace("task1")
    )

    save_trace(
        conn,
        make_trace("task2")
    )

    assert trace_count(conn) == 2

    close_db(conn)


# ==========================================================
# Clear
# ==========================================================

def test_clear_traces(tmp_path):

    conn = init_db(tmp_path / "test.db")

    save_trace(
        conn,
        make_trace("task1")
    )

    save_trace(
        conn,
        make_trace("task2")
    )

    assert trace_count(conn) == 2

    clear_traces(conn)

    assert trace_count(conn) == 0

    close_db(conn)


# ==========================================================
# Serialization
# ==========================================================

def test_trace_serialization_preserved(tmp_path):

    conn = init_db(tmp_path / "test.db")

    trace = make_trace()

    save_trace(conn, trace)

    loaded = get_trace(conn, trace.task_id)

    assert loaded.to_dict() == trace.to_dict()

    close_db(conn)

# ==========================================================
# Score Save / Load
# ==========================================================

def test_save_and_get_score(tmp_path):

    conn = init_db(tmp_path / "test.db")

    score = make_score()

    save_score(conn, score)

    loaded = get_score(conn, score.task_id)

    assert loaded is not None

    assert loaded.task_id == score.task_id

    assert loaded.passed == score.passed

    close_db(conn)


# ==========================================================
# Multiple Scores
# ==========================================================

def test_get_all_scores(tmp_path):

    conn = init_db(tmp_path / "test.db")

    for i in range(5):

        save_score(
            conn,
            make_score(f"task_{i}")
        )

    scores = get_all_scores(conn)

    assert len(scores) == 5

    close_db(conn)


# ==========================================================
# Score Count
# ==========================================================

def test_score_count(tmp_path):

    conn = init_db(tmp_path / "test.db")

    assert score_count(conn) == 0

    save_score(
        conn,
        make_score("task1")
    )

    save_score(
        conn,
        make_score("task2")
    )

    assert score_count(conn) == 2

    close_db(conn)


# ==========================================================
# Clear Scores
# ==========================================================

def test_clear_scores(tmp_path):

    conn = init_db(tmp_path / "test.db")

    save_score(
        conn,
        make_score("task1")
    )

    save_score(
        conn,
        make_score("task2")
    )

    assert score_count(conn) == 2

    clear_scores(conn)

    assert score_count(conn) == 0

    close_db(conn)


# ==========================================================
# Score Serialization
# ==========================================================

def test_score_serialization_preserved(tmp_path):

    conn = init_db(tmp_path / "test.db")

    score = make_score()

    save_score(conn, score)

    loaded = get_score(conn, score.task_id)

    assert loaded.to_dict() == score.to_dict()

    close_db(conn)

# ==========================================================
# Trace and Score coexistence
# ==========================================================

def test_trace_and_score_coexist(tmp_path):

    conn = init_db(tmp_path / "test.db")

    trace = make_trace("task1")
    score = make_score("task1")

    save_trace(conn, trace)
    save_score(conn, score)

    assert trace_count(conn) == 1
    assert score_count(conn) == 1

    assert get_trace(conn, "task1") is not None
    assert get_score(conn, "task1") is not None

    close_db(conn)