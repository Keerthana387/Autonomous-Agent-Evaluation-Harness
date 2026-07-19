from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable

from harness.runner import run_all
from mutations.generate_suite import generate_suite
from scoring.run_scoring import score_database


# ============================================================================
# Configuration
# ============================================================================


@dataclass(slots=True)
class PipelineConfig:
    """
    Configuration for a benchmark pipeline run.
    """

    provider: str = "gemini"

    db_path: Path = Path("databases/benchmark.db")

    base_task_dir: Path = Path("tasks/base")

    generated_task_dir: Path = Path("tasks/generated")


# ============================================================================
# Result
# ============================================================================


@dataclass(slots=True)
class PipelineResult:
    """
    Summary of a completed benchmark pipeline.
    """

    provider: str

    database: Path

    generated_tasks: int

    executed_tasks: int

    scored_tasks: int

    duration_seconds: float


# ============================================================================
# Pipeline
# ============================================================================


def run_pipeline(
    config: PipelineConfig,
    progress_callback: (
        Callable[[str, float], None] | None
    ) = None,
) -> PipelineResult:
    """
    Execute the complete benchmark pipeline.

    Parameters
    ----------
    config
        Pipeline configuration.

    progress_callback
        Optional callback used to report progress.

        Signature:
            callback(message: str, progress: float)

        Progress is a value in [0.0, 1.0].
    """

    start_time = time.perf_counter()

    def update_progress(
        message: str,
        progress: float,
    ) -> None:
        if progress_callback is not None:
            progress_callback(message, progress)

    print("=" * 60)
    print("Autonomous Agent Evaluation Harness")
    print("=" * 60)

    # ---------------------------------------------------------------------
    # Generate mutations
    # ---------------------------------------------------------------------

    print("\n[1/3] Generating mutated benchmark tasks...")
    update_progress("Generating mutated tasks...", 0.05)

    generated = generate_suite(
        base_dir=config.base_task_dir,
        output_dir=config.generated_task_dir,
    )

    print(f"Generated {len(generated)} mutated tasks.")
    update_progress("Task generation complete.", 0.33)

    # ---------------------------------------------------------------------
    # Execute benchmark
    # ---------------------------------------------------------------------

    print("\n[2/3] Running benchmark...")
    update_progress("Running benchmark...", 0.40)

    executed_tasks = run_all(
        db_path=config.db_path,
        provider=config.provider,
    )

    print(f"Executed {executed_tasks} tasks.")
    update_progress("Benchmark execution complete.", 0.66)

    # ---------------------------------------------------------------------
    # Score benchmark
    # ---------------------------------------------------------------------

    print("\n[3/3] Scoring traces...")
    update_progress("Scoring benchmark...", 0.75)

    scored_tasks = score_database(
        db_path=config.db_path,
        task_dirs=[
            config.base_task_dir,
            config.generated_task_dir,
        ],
    )

    print(f"Scored {scored_tasks} traces.")
    update_progress("Scoring complete.", 0.95)

    duration = time.perf_counter() - start_time

    print("\nPipeline completed successfully.")
    update_progress("Pipeline completed successfully.", 1.0)

    return PipelineResult(
        provider=config.provider,
        database=config.db_path,
        generated_tasks=len(generated),
        executed_tasks=executed_tasks,
        scored_tasks=scored_tasks,
        duration_seconds=duration,
    )


# ============================================================================
# CLI
# ============================================================================


def parse_args() -> PipelineConfig:

    parser = argparse.ArgumentParser(
        description="Autonomous Agent Evaluation Harness",
    )

    parser.add_argument(
        "--provider",
        default="gemini",
        help="LLM provider to evaluate.",
    )

    parser.add_argument(
        "--db",
        default="databases/benchmark.db",
        help="SQLite database path.",
    )

    parser.add_argument(
        "--base-dir",
        default="tasks/base",
        help="Directory containing base benchmark tasks.",
    )

    parser.add_argument(
        "--generated-dir",
        default="tasks/generated",
        help="Directory containing generated benchmark tasks.",
    )

    args = parser.parse_args()

    return PipelineConfig(
        provider=args.provider,
        db_path=Path(args.db),
        base_task_dir=Path(args.base_dir),
        generated_task_dir=Path(args.generated_dir),
    )


# ============================================================================
# Entry Point
# ============================================================================


def main() -> None:

    result = run_pipeline(
        parse_args(),
    )

    print("\nSummary")
    print("-" * 60)
    print(f"Provider         : {result.provider}")
    print(f"Database         : {result.database}")
    print(f"Generated Tasks  : {result.generated_tasks}")
    print(f"Executed Tasks   : {result.executed_tasks}")
    print(f"Scored Tasks     : {result.scored_tasks}")
    print(f"Duration         : {result.duration_seconds:.2f} seconds")


if __name__ == "__main__":
    main()