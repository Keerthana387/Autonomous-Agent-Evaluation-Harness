from __future__ import annotations

from abc import ABC, abstractmethod

from tasks.models import Task


class BaseMutation(ABC):
    """
    Base class for every benchmark mutation.

    A mutation takes a Task and returns a NEW mutated Task.
    The original task must never be modified.
    """

    #: Unique mutation identifier.
    mutation_type: str

    @abstractmethod
    def apply(self, task: Task) -> Task:
        """
        Apply the mutation.

        Parameters
        ----------
        task:
            Original benchmark task.

        Returns
        -------
        Task
            A new mutated task.
        """
        raise NotImplementedError