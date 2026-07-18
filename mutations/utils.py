from __future__ import annotations

from copy import deepcopy

from tasks.models import Task


def clone_task(task: Task) -> Task:
    """
    Return a deep copy of a task.

    Mutations must never modify the original task.
    """
    return deepcopy(task)


def make_mutated_id(
    task: Task,
    mutation_type: str,
) -> str:
    """
    Generate the identifier for a mutated task.

    Example
    -------
    task_003
        ->
    task_003_mut_distractor
    """
    return f"{task.id}_mut_{mutation_type}"


def attach_mutation_metadata(
    task: Task,
    *,
    mutation_type: str,
) -> None:
    """
    Attach mutation metadata to a cloned task.
    """

    task.base_task_id = task.id
    task.mutation_type = mutation_type
    task.id = make_mutated_id(task, mutation_type)