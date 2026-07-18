from __future__ import annotations

import random

from tasks.models import Task
from tools.registry import TOOLS

from .base import BaseMutation
from .utils import (
    attach_mutation_metadata,
    clone_task,
)


class DistractorToolsMutation(BaseMutation):
    """
    Adds irrelevant tools to a benchmark task.

    Purpose
    -------
    Evaluate whether the agent can select the appropriate
    tool while ignoring distractors.
    """

    mutation_type = "distractor"

    def __init__(
        self,
        *,
        num_distractors: int = 3,
    ) -> None:
        self.num_distractors = num_distractors

    def apply(
        self,
        task: Task,
    ) -> Task:
        """
        Produce a mutated task with additional distractor tools.
        """

        mutated = clone_task(task)

        # ------------------------------------------------------
        # Determine candidate distractor tools
        # ------------------------------------------------------

        available = set(mutated.available_tools)

        candidates = [
            tool
            for tool in TOOLS.keys()
            if tool not in available
        ]

        # Nothing to add
        if not candidates:
            attach_mutation_metadata(
                mutated,
                mutation_type=self.mutation_type,
            )
            return mutated

        distractors = random.sample(
            candidates,
            k=min(
                self.num_distractors,
                len(candidates),
            ),
        )

        # ------------------------------------------------------
        # Update task
        # ------------------------------------------------------

        mutated.available_tools.extend(distractors)

        # Ensure uniqueness while preserving order
        mutated.available_tools = list(
            dict.fromkeys(mutated.available_tools)
        )

        # Tell the scorer these tools should never be used
        mutated.success_criteria.must_not_call.extend(
            distractors
        )

        mutated.success_criteria.must_not_call = list(
            dict.fromkeys(
                mutated.success_criteria.must_not_call
            )
        )

        attach_mutation_metadata(
            mutated,
            mutation_type=self.mutation_type,
        )

        return mutated