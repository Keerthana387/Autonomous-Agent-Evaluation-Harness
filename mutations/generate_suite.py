from __future__ import annotations

from pathlib import Path

import yaml

from mutations.engine import MutationEngine
from tasks.loader import load_all_tasks


def write_task(task, output_path: Path) -> None:
    """
    Serialize a Task object to YAML.
    """

    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            task.model_dump(
                mode="json",
                exclude_none=True,
            ),
            f,
            sort_keys=False,
            allow_unicode=True,
        )


def clear_generated_directory(
    output_dir: Path,
) -> None:
    """
    Remove previously generated benchmark files.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for file in output_dir.glob("*.yaml"):
        file.unlink()


def generate_suite(
    *,
    base_dir: str | Path,
    output_dir: str | Path,
    engine: MutationEngine | None = None,
) -> list:
    """
    Generate all mutated benchmark tasks.

    Parameters
    ----------
    base_dir
        Directory containing the base benchmark tasks.

    output_dir
        Directory where mutated YAML files should be written.

    engine
        Mutation engine. If omitted, the default engine is used.

    Returns
    -------
    list[Task]
        All generated tasks.
    """

    if engine is None:
        engine = MutationEngine()

    base_dir = Path(base_dir)
    output_dir = Path(output_dir)

    clear_generated_directory(output_dir)

    base_tasks = load_all_tasks(base_dir)

    generated_tasks = []

    for task in base_tasks:

        mutations = engine.apply_all(task)

        for mutated in mutations:

            output_file = (
                output_dir
                / f"{mutated.id}.yaml"
            )

            write_task(
                mutated,
                output_file,
            )

            generated_tasks.append(
                mutated
            )

    return generated_tasks


def main() -> None:
    """
    Generate the benchmark mutation suite.
    """

    generated = generate_suite(
        base_dir="tasks/base",
        output_dir="tasks/generated",
    )

    print(
        f"Generated {len(generated)} mutated tasks."
    )


if __name__ == "__main__":
    main()