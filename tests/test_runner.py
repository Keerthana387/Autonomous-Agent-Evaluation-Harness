from agent.trace import Trace
from harness.db import (
    get_all_traces,
    init_db,
)
from harness.runner import run_suite


def fake_run_task(task, provider="gemini"):

    trace = Trace(
        task_id=task.id,
        base_task_id=task.base_task_id,
        mutation_type=task.mutation_type,
    )

    trace.finish(f"Finished {task.id}")

    return trace


def test_run_suite(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        "harness.runner.run_task",
        fake_run_task,
    )

    db_path = tmp_path / "benchmark.db"

    conn = init_db(db_path)
    conn.close()

    run_suite(
        "tasks/base",
        conn=init_db(db_path),
    )

    conn = init_db(db_path)

    traces = get_all_traces(conn)

    assert len(traces) > 0

    assert all(
        trace.successful
        for trace in traces
    )

    conn.close()