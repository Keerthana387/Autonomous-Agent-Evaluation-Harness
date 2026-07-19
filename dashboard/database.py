"""
Database access helpers for the dashboard.

This module is read-only. Database creation and initialization
are handled by harness.db.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Current Database
# ---------------------------------------------------------------------


def current_database() -> Path:
    """
    Return the currently selected database.
    """

    return Path(st.session_state["selected_database"])


# ---------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------


def get_connection(
    db_path: str | Path | None = None,
) -> sqlite3.Connection:
    """
    Open a SQLite connection.
    """

    if db_path is None:
        db_path = current_database()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    return conn


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


def database_exists(
    db_path: str | Path | None = None,
) -> bool:
    """
    Return True if the selected database exists.
    """

    if db_path is None:
        db_path = current_database()

    return Path(db_path).exists()


def validate_schema(
    db_path: str | Path | None = None,
) -> bool:
    """
    Verify the required benchmark tables exist.
    """

    conn = get_connection(db_path)

    try:

        tables = {
            row["name"]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            )
        }

        return {
            "traces",
            "scores",
        }.issubset(tables)

    finally:
        conn.close()


# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------


def get_summary(
    db_path: str | Path | None = None,
) -> dict:
    """
    Return overall benchmark statistics.
    """

    conn = get_connection(db_path)

    try:

        executed = conn.execute(
            """
            SELECT COUNT(*)
            FROM traces
            """
        ).fetchone()[0]

        passed = conn.execute(
            """
            SELECT COUNT(*)
            FROM scores
            WHERE passed = 1
            """
        ).fetchone()[0]

        avg_steps = conn.execute(
            """
            SELECT AVG(num_steps)
            FROM traces
            WHERE successful = 1
            """
        ).fetchone()[0]

        avg_tools = conn.execute(
            """
            SELECT AVG(num_tool_calls)
            FROM traces
            WHERE successful = 1
            """
        ).fetchone()[0]

        avg_duration = conn.execute(
            """
            SELECT AVG(duration_seconds)
            FROM traces
            WHERE successful = 1
            """
        ).fetchone()[0]

    finally:
        conn.close()

    failed = executed - passed

    success_rate = (
        (passed / executed) * 100
        if executed
        else 0
    )

    return {
        "executed": executed,
        "passed": passed,
        "failed": failed,
        "success_rate": success_rate,
        "average_steps": avg_steps or 0,
        "average_tool_calls": avg_tools or 0,
        "average_duration": avg_duration or 0,
    }


# ---------------------------------------------------------------------
# Task Table
# ---------------------------------------------------------------------


def get_tasks(
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Return every benchmark task.
    """

    conn = get_connection(db_path)

    try:

        query = """
        SELECT
            t.task_id,
            t.base_task_id,
            t.mutation_type,
            t.successful,
            t.num_steps,
            t.num_tool_calls,
            t.duration_seconds,
            s.passed
        FROM traces t
        LEFT JOIN scores s
            ON t.task_id = s.task_id
        ORDER BY t.task_id
        """

        return pd.read_sql_query(
            query,
            conn,
        )

    finally:
        conn.close()


def get_all_tasks(
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Convenience wrapper.
    """

    return get_tasks(db_path)

# ---------------------------------------------------------------------
# Individual Trace
# ---------------------------------------------------------------------


def get_trace(
    task_id: str,
    db_path: str | Path | None = None,
):
    """
    Return the raw trace JSON for a task.
    """

    conn = get_connection(db_path)

    try:

        row = conn.execute(
            """
            SELECT trace_json
            FROM traces
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

    finally:
        conn.close()

    return None if row is None else row["trace_json"]


def get_trace_details(
    task_id: str,
    db_path: str | Path | None = None,
) -> dict | None:
    """
    Return the parsed trace JSON.
    """

    trace_json = get_trace(
        task_id,
        db_path,
    )

    if trace_json is None:
        return None

    return json.loads(trace_json)


# ---------------------------------------------------------------------
# Individual Score
# ---------------------------------------------------------------------


def get_score(
    task_id: str,
    db_path: str | Path | None = None,
):
    """
    Return the raw score JSON.
    """

    conn = get_connection(db_path)

    try:

        row = conn.execute(
            """
            SELECT score_json
            FROM scores
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

    finally:
        conn.close()

    return None if row is None else row["score_json"]


def get_score_details(
    task_id: str,
    db_path: str | Path | None = None,
) -> dict | None:
    """
    Return the parsed score JSON.
    """

    score_json = get_score(
        task_id,
        db_path,
    )

    if score_json is None:
        return None

    return json.loads(score_json)


# ---------------------------------------------------------------------
# Recent Tasks
# ---------------------------------------------------------------------


def get_recent_tasks(
    limit: int = 10,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Return the most recent benchmark tasks.
    """

    conn = get_connection(db_path)

    try:

        query = """
        SELECT
            t.task_id,
            t.successful,
            s.passed,
            t.duration_seconds,
            t.created_at
        FROM traces t
        LEFT JOIN scores s
            ON t.task_id = s.task_id
        ORDER BY t.created_at DESC
        LIMIT ?
        """

        return pd.read_sql_query(
            query,
            conn,
            params=(limit,),
        )

    finally:
        conn.close()


# ---------------------------------------------------------------------
# Mutation Types
# ---------------------------------------------------------------------


def get_mutation_types(
    db_path: str | Path | None = None,
) -> list[str]:
    """
    Return all mutation types.
    """

    conn = get_connection(db_path)

    try:

        rows = conn.execute(
            """
            SELECT DISTINCT mutation_type
            FROM traces
            WHERE mutation_type IS NOT NULL
            ORDER BY mutation_type
            """
        ).fetchall()

    finally:
        conn.close()

    return [
        row["mutation_type"]
        for row in rows
    ]


# ---------------------------------------------------------------------
# Task Summary
# ---------------------------------------------------------------------


def get_task_summary(
    task_id: str,
    db_path: str | Path | None = None,
):
    """
    Return summary information for one task.
    """

    conn = get_connection(db_path)

    try:

        row = conn.execute(
            """
            SELECT
                t.task_id,
                t.base_task_id,
                t.mutation_type,
                t.successful,
                t.num_steps,
                t.num_tool_calls,
                t.duration_seconds,
                s.passed
            FROM traces t
            LEFT JOIN scores s
                ON t.task_id = s.task_id
            WHERE t.task_id = ?
            """,
            (task_id,),
        ).fetchone()

    finally:
        conn.close()

    return dict(row) if row else None


# ---------------------------------------------------------------------
# Complete Task Report
# ---------------------------------------------------------------------


def get_task_report(
    task_id: str,
    db_path: str | Path | None = None,
):
    """
    Return both the trace and score for a task.
    """

    return {
        "trace": get_trace_details(
            task_id,
            db_path,
        ),
        "score": get_score_details(
            task_id,
            db_path,
        ),
    }