"""
Run deterministic scoring on every stored benchmark trace.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from harness.db import (
    init_db,
    close_db,
    get_all_traces,
    save_score,
)

from scoring.rules import score_trace
from tasks.loader import load_all_tasks


# ============================================================================
# Public API
# ============================================================================


def score_database(
    db_path: str | Path,
    task_dir: str | Path,
) -> int:
    """
    Score every stored trace.

    Returns
    -------
    int
        Number of traces successfully scored.
    """

    conn = init_db(db_path)

    try:
        return score_connection(
            conn,
            task_dir,
        )

    finally:
        close_db(conn)


def score_connection(
    conn: sqlite3.Connection,
    task_dir: str | Path,
) -> int:
    """
    Score every trace already present in the database.

    Existing scores are overwritten.
    """

    tasks = {
        task.id: task
        for task in load_all_tasks(task_dir)
    }

    traces = get_all_traces(conn)

    scored = 0

    for trace in traces:

        task = tasks.get(trace.task_id)

        if task is None:
            import logging

            logger = logging.getLogger(__name__)

            logger.warning(
                "No task found for trace %s. Skipping.",
                trace.task_id,
            )
            continue

        score = score_trace(
            task,
            trace,
        )

        save_score(
            conn,
            score,
        )

        scored += 1

    return scored


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Run deterministic benchmark scoring."
    )

    parser.add_argument(
        "--db",
        default="benchmark.db",
        help="SQLite database path.",
    )

    parser.add_argument(
        "--tasks",
        default="tasks/generated",
        help="Directory containing benchmark tasks.",
    )

    args = parser.parse_args()

    count = score_database(
        db_path=args.db,
        task_dir=args.tasks,
    )

    print(f"Scored {count} traces.")