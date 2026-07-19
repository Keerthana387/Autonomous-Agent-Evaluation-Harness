"""
SQLite persistence layer for benchmark execution traces.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime

from agent.trace import Trace
from scoring.models import Score

TRACE_TABLE = "traces"
SCORE_TABLE = "scores"
DATABASE_DIR = Path("databases")

# ============================================================================
# Database Initialization
# ============================================================================


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """
    Create (or open) the benchmark database.

    Ensures the required tables exist before returning the connection.
    """

    conn = sqlite3.connect(db_path)

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TRACE_TABLE} (

            task_id TEXT PRIMARY KEY,

            base_task_id TEXT,

            mutation_type TEXT,

            agent_id TEXT NOT NULL,

            successful INTEGER NOT NULL,

            final_answer TEXT,

            trace_json TEXT NOT NULL,

            num_steps INTEGER NOT NULL,

            num_tool_calls INTEGER NOT NULL,

            duration_seconds REAL,

            error TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCORE_TABLE} (

            task_id TEXT PRIMARY KEY,

            agent_id TEXT,

            base_task_id TEXT,

            mutation_type TEXT,

            passed INTEGER,

            score_json TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        );
        """
    )

    conn.commit()

    return conn


# ============================================================================
# Save
# ============================================================================


def save_trace(
    conn: sqlite3.Connection,
    trace: Trace,
) -> None:
    """
    Insert or replace a trace in the database.
    """

    conn.execute(
        f"""
        INSERT OR REPLACE INTO {TRACE_TABLE}
        (
            task_id,
            base_task_id,
            mutation_type,
            agent_id,
            successful,
            final_answer,
            trace_json,
            num_steps,
            num_tool_calls,
            duration_seconds,
            error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            trace.task_id,
            trace.base_task_id,
            trace.mutation_type,
            trace.agent_id,
            int(trace.successful),
            trace.final_answer,
            trace.to_json(indent=None),
            trace.num_steps,
            trace.num_tool_calls,
            trace.duration_seconds,
            trace.error,
        ),
    )

    conn.commit()


# ============================================================================
# Load
# ============================================================================


def get_trace(
    conn: sqlite3.Connection,
    task_id: str,
) -> Trace | None:
    """
    Load one trace by task id.
    """

    cursor = conn.execute(
        f"""
        SELECT trace_json
        FROM {TRACE_TABLE}
        WHERE task_id = ?
        """,
        (task_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return Trace.from_json(row[0])


def get_all_traces(
    conn: sqlite3.Connection,
) -> list[Trace]:
    """
    Load every stored trace.
    """

    cursor = conn.execute(
        f"""
        SELECT trace_json
        FROM {TRACE_TABLE}
        ORDER BY created_at
        """
    )

    rows = cursor.fetchall()

    return [
        Trace.from_json(row[0])
        for row in rows
    ]


# ============================================================================
# Utilities
# ============================================================================


def clear_traces(
    conn: sqlite3.Connection,
) -> None:
    """
    Remove every stored trace.
    """

    conn.execute(
        f"DELETE FROM {TRACE_TABLE}"
    )

    conn.commit()


def trace_count(
    conn: sqlite3.Connection,
) -> int:
    """
    Return the number of stored traces.
    """

    cursor = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM {TRACE_TABLE}
        """
    )

    return cursor.fetchone()[0]


def close_db(
    conn: sqlite3.Connection,
) -> None:
    """
    Close the database connection.
    """

    conn.close()

# ============================================================================
# Score Persistence
# ============================================================================

def save_score(
    conn: sqlite3.Connection,
    score: Score,
) -> None:
    """
    Insert or replace a score in the database.
    """

    conn.execute(
        f"""
        INSERT OR REPLACE INTO {SCORE_TABLE}
        (
            task_id,
            agent_id,
            base_task_id,
            mutation_type,
            passed,
            score_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            score.task_id,
            score.agent_id,
            score.base_task_id,
            score.mutation_type,
            (
                None
                if score.passed is None
                else int(score.passed)
            ),
            score.to_json(indent=None),
        ),
    )

    conn.commit()


def get_score(
    conn: sqlite3.Connection,
    task_id: str,
) -> Score | None:
    """
    Load one score by task id.
    """

    cursor = conn.execute(
        f"""
        SELECT score_json
        FROM {SCORE_TABLE}
        WHERE task_id = ?
        """,
        (task_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return Score.from_json(row[0])


def get_all_scores(
    conn: sqlite3.Connection,
) -> list[Score]:
    """
    Load every stored score.
    """

    cursor = conn.execute(
        f"""
        SELECT score_json
        FROM {SCORE_TABLE}
        ORDER BY created_at
        """
    )

    rows = cursor.fetchall()

    return [
        Score.from_json(row[0])
        for row in rows
    ]


def clear_scores(
    conn: sqlite3.Connection,
) -> None:
    """
    Remove every stored score.
    """

    conn.execute(
        f"DELETE FROM {SCORE_TABLE}"
    )

    conn.commit()


def score_count(
    conn: sqlite3.Connection,
) -> int:
    """
    Return the number of stored scores.
    """

    cursor = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM {SCORE_TABLE}
        """
    )

    return cursor.fetchone()[0]

def ensure_database_dir() -> Path:
    """
    Ensure the databases directory exists.
    """

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return DATABASE_DIR

def list_databases() -> list[Path]:
    """
    Return every database ordered by newest first.
    """

    directory = ensure_database_dir()

    return sorted(
        directory.glob("*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

def default_database_name() -> str:
    """
    Generate the default timestamp-based database name.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"benchmark_{timestamp}"

def sanitize_database_name(
    name: str,
) -> str:
    """
    Convert a user-provided name into a valid filename.
    """

    name = name.strip()

    name = name.replace(" ", "_")

    invalid = '<>:"/\\|?*'

    for char in invalid:
        name = name.replace(char, "")

    if not name.endswith(".db"):
        name += ".db"

    return name

def database_exists(
    name: str | Path,
) -> bool:
    """
    Return True if the database already exists.
    """

    path = DATABASE_DIR / Path(name).name

    return path.exists()

def create_database(
    name: str,
) -> Path:
    """
    Create and initialize a new benchmark database.
    """

    ensure_database_dir()

    filename = sanitize_database_name(name)

    path = DATABASE_DIR / filename

    if path.exists():
        raise FileExistsError(
            f"Database '{filename}' already exists."
        )

    conn = init_db(path)

    conn.close()

    return path

def latest_database() -> Path | None:
    """
    Return the newest database.
    """

    databases = list_databases()

    if not databases:
        return None

    return databases[0]

def get_database_names() -> list[str]:
    """
    Return all database filenames ordered by newest first.
    """

    return [
        db.name
        for db in list_databases()
    ]

def get_database_path(
    name: str,
) -> Path:
    """
    Return the full path of a database.
    """

    return ensure_database_dir() / name