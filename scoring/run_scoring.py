"""
Run deterministic scoring on every stored benchmark trace.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from pathlib import Path
from typing import Iterable

from harness.db import (
    close_db,
    get_all_traces,
    init_db,
    save_score,
)
from scoring.rules import score_trace
from tasks.loader import load_all_tasks

logger = logging.getLogger(__name__)


# ============================================================================
# Public API
# ============================================================================


def score_database(
    db_path: str | Path,
    task_dirs: Iterable[str | Path],
) -> int:
    """
    Score every stored trace.

    Parameters
    ----------
    db_path
        SQLite database.

    task_dirs
        One or more directories containing benchmark task definitions.

    Returns
    -------
    int
        Number of traces successfully scored.
    """

    conn = init_db(db_path)

    try:
        return score_connection(
            conn,
            task_dirs,
        )

    finally:
        close_db(conn)


def score_connection(
    conn: sqlite3.Connection,
    task_dirs: Iterable[str | Path],
) -> int:
    """
    Score every trace already present in the database.

    Existing scores are overwritten.
    """

    tasks = {}

    for task_dir in task_dirs:

        tasks.update(
            {
                task.id: task
                for task in load_all_tasks(task_dir)
            }
        )

    traces = get_all_traces(conn)

    scored = 0

    for trace in traces:

        task = tasks.get(trace.task_id)

        if task is None:

            logger.warning(
                "No task found for trace '%s'. Skipping.",
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

    parser = argparse.ArgumentParser(
        description="Run deterministic benchmark scoring.",
    )

    parser.add_argument(
        "--db",
        default="benchmark.db",
        help="SQLite database path.",
    )

    parser.add_argument(
        "--tasks",
        nargs="+",
        default=[
            "tasks/base",
            "tasks/generated",
        ],
        help="One or more directories containing benchmark tasks.",
    )

    args = parser.parse_args()

    count = score_database(
        db_path=args.db,
        task_dirs=args.tasks,
    )

    print(f"Scored {count} traces.")