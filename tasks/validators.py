"""
Cross-task validation.

These checks validate the benchmark as a whole rather than
individual YAML files.
"""

from collections import Counter

from tasks.models import Task
from tools.registry import TOOLS


def validate_unique_ids(tasks: list[Task]):

    ids = [task.id for task in tasks]

    duplicates = {
        task_id
        for task_id in ids
        if ids.count(task_id) > 1
    }

    if duplicates:
        raise ValueError(
            f"Duplicate task IDs found: {duplicates}"
        )


def validate_tool_references(tasks: list[Task]):

    for task in tasks:

        for tool in task.available_tools:

            if tool not in TOOLS:

                raise ValueError(
                    f"{task.id}: unknown tool '{tool}'"
                )


def validate_expected_tool_calls(tasks: list[Task]):

    for task in tasks:

        for call in task.expected_tool_calls:

            if call.tool not in TOOLS:

                raise ValueError(
                    f"{task.id}: expected tool '{call.tool}' "
                    "not present in registry"
                )


def validate_category_distribution(
    tasks: list[Task],
    expected_per_category: int = 3
):

    counts = Counter(
        task.category.value
        for task in tasks
    )

    for category, count in counts.items():

        if count != expected_per_category:

            raise ValueError(
                f"{category}: expected "
                f"{expected_per_category}, found {count}"
            )


def validate_tasks(tasks: list[Task]):

    validate_unique_ids(tasks)

    validate_tool_references(tasks)

    validate_expected_tool_calls(tasks)

    validate_category_distribution(tasks)