from pathlib import Path

from agent.trace import Trace
from harness.db import (
    init_db,
    save_trace,
    get_trace,
    get_all_traces,
    clear_traces,
    trace_count,
    close_db,
)


# ==========================================================
# Helper
# ==========================================================

def make_trace(task_id: str = "task_001") -> Trace:

    trace = Trace(task_id=task_id)

    trace.finish("Finished successfully")

    return trace


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