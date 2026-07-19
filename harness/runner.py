from __future__ import annotations

from pathlib import Path

from agent.runner import run_task
from agent.trace import Trace
from harness.db import (
    close_db,
    init_db,
    save_trace,
)
from tasks.loader import load_all_tasks


# ============================================================================
# Suite Runner
# ============================================================================


def run_suite(
    task_dir: str | Path,
    conn,
    *,
    provider: str = "gemini",
) -> int:
    """
    Execute every task in a directory.

    Any unexpected failure while executing one task is recorded as a failed
    trace, allowing the remainder of the benchmark to continue.
    """
    count =0
    tasks = load_all_tasks(task_dir)

    for task in tasks:

        try:

            trace = run_task(
                task,
                provider=provider,
            )

        except Exception as exc:

            trace = Trace(
                task_id=task.id,
                base_task_id=task.base_task_id,
                mutation_type=task.mutation_type,
            )

            trace.set_error(exc)

        save_trace(
            conn,
            trace,
        )
        count += 1

    return count



# ============================================================================
# Benchmark Runner
# ============================================================================


def run_all(
    *,
    db_path: str | Path = "benchmark.db",
    provider: str = "gemini",
) -> int:
    """
    Run the complete benchmark.

    Executes both the base benchmark tasks and every generated mutation.
    """

    conn = init_db(db_path)

    try:
        total = 0
        total += run_suite(
            "tasks/base",
            conn,
            provider=provider,
        )

        total += run_suite(
            "tasks/generated",
            conn,
            provider=provider,
        )

    finally:

        close_db(conn)

    return total

# ============================================================================
# Entry Point
# ============================================================================


if __name__ == "__main__":

    run_all()