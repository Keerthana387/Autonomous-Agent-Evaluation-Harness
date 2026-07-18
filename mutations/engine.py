from __future__ import annotations

from tasks.models import Task

from .base import BaseMutation
from .distractor import DistractorToolsMutation
from .prompt_injection import PromptInjectionMutation


class MutationEngine:
    """
    Registry and dispatcher for benchmark mutations.

    The engine owns a collection of mutation objects and is
    responsible for applying them to benchmark tasks.
    """

    def __init__(
        self,
        mutations: list[BaseMutation] | None = None,
    ) -> None:

        if mutations is None:
            mutations = [
                DistractorToolsMutation(),
                PromptInjectionMutation(),
            ]

        self._mutations = {
            mutation.mutation_type: mutation
            for mutation in mutations
        }

    @property
    def available_mutations(self) -> list[str]:
        """
        Return the registered mutation names.
        """
        return sorted(self._mutations.keys())

    def register(
        self,
        mutation: BaseMutation,
    ) -> None:
        """
        Register a new mutation.

        Existing mutations with the same name are replaced.
        """
        self._mutations[
            mutation.mutation_type
        ] = mutation

    def get(
        self,
        mutation_type: str,
    ) -> BaseMutation:
        """
        Retrieve a mutation by name.
        """

        try:
            return self._mutations[
                mutation_type
            ]
        except KeyError:
            raise ValueError(
                f"Unknown mutation '{mutation_type}'."
            ) from None

    def apply(
        self,
        task: Task,
        mutation_type: str,
    ) -> Task:
        """
        Apply one mutation to a task.
        """

        mutation = self.get(
            mutation_type
        )

        return mutation.apply(task)

    def apply_all(
        self,
        task: Task,
    ) -> list[Task]:
        """
        Apply every registered mutation.

        Returns
        -------
        list[Task]
            One mutated task per registered mutation.
        """

        return [
            mutation.apply(task)
            for mutation in self._mutations.values()
        ]