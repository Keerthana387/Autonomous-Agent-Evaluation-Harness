from __future__ import annotations

from agent.llm import create_llm
from agent.loop import ReActLoop
from agent.providers.models import (
    ConversationTurn,
    Role,
)
from tasks.models import Task
from agent.prompts import DEFAULT_SYSTEM_PROMPT


def build_initial_conversation(
    task: Task,
) -> list[ConversationTurn]:
    """
    Build the initial conversation for a benchmark task.
    """

    return [
        ConversationTurn(
            role=Role.SYSTEM,
            content=DEFAULT_SYSTEM_PROMPT,
        ),
        ConversationTurn(
            role=Role.USER,
            content=task.prompt,
        ),
    ]


def run_task(
    task: Task,
    *,
    provider: str = "gemini",
    max_steps: int = ReActLoop.DEFAULT_MAX_STEPS,
):
    """
    Execute one benchmark task and return its Trace.
    """

    llm = create_llm(
        provider=provider,
        tools=task.available_tools,
    )

    conversation = build_initial_conversation(
        task
    )

    loop = ReActLoop(
        llm=llm,
        max_steps=max_steps,
    )

    return loop.run(
        task_id=task.id,
        conversation=conversation,
        base_task_id=task.base_task_id,
        mutation_type=task.mutation_type,
    )