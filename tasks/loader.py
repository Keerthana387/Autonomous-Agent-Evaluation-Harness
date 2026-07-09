from pathlib import Path

import yaml
from pydantic import ValidationError

from tasks.models import Task


def load_task(path: str | Path) -> Task:

    path = Path(path)

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    try:
        return Task.model_validate(raw)

    except ValidationError as e:
        raise ValueError(
            f"\nInvalid task schema: {path.name}\n\n{e}"
        )


def load_all_tasks(task_dir: str | Path) -> list[Task]:

    task_dir = Path(task_dir)

    return [
        load_task(file)
        for file in sorted(task_dir.glob("*.yaml"))
    ]


def get_task(task_dir: str | Path, task_id: str) -> Task:

    for task in load_all_tasks(task_dir):

        if task.id == task_id:
            return task

    raise ValueError(f"Task '{task_id}' not found.")