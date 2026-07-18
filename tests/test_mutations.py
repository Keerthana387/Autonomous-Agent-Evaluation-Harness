from copy import deepcopy

import pytest

from mutations.distractor import DistractorToolsMutation
from mutations.prompt_injection import PromptInjectionMutation
from mutations.engine import MutationEngine

from tasks.models import (
    FaultConfig,
    FailMode,
)

from tools.registry import execute_tool


# ==========================================================
# Distractor Mutation
# ==========================================================

def test_distractor_returns_new_task(sample_task):

    mutated = DistractorToolsMutation().apply(sample_task)

    assert mutated is not sample_task


def test_original_task_not_modified(sample_task):

    original = deepcopy(sample_task)

    DistractorToolsMutation().apply(sample_task)

    assert sample_task == original


def test_distractor_adds_tools(sample_task):

    mutated = DistractorToolsMutation(
        num_distractors=3
    ).apply(sample_task)

    assert (
        len(mutated.available_tools)
        >
        len(sample_task.available_tools)
    )


def test_distractor_updates_must_not_call(sample_task):

    mutated = DistractorToolsMutation().apply(sample_task)

    added_tools = (
        set(mutated.available_tools)
        -
        set(sample_task.available_tools)
    )

    for tool in added_tools:

        assert (
            tool
            in mutated.success_criteria.must_not_call
        )


def test_distractor_sets_metadata(sample_task):

    mutated = DistractorToolsMutation().apply(sample_task)

    assert mutated.base_task_id == sample_task.id

    assert mutated.mutation_type == "distractor"

    assert mutated.id != sample_task.id


# ==========================================================
# Prompt Injection Mutation
# ==========================================================

def test_prompt_injection_sets_fault_config(sample_task):

    mutated = PromptInjectionMutation().apply(sample_task)

    assert isinstance(
        mutated.fault_config,
        FaultConfig,
    )


def test_prompt_injection_target(sample_task):

    mutated = PromptInjectionMutation().apply(sample_task)

    assert (
        mutated.fault_config.target_tool
        ==
        "search_web"
    )


def test_prompt_injection_payload(sample_task):

    mutated = PromptInjectionMutation().apply(sample_task)

    assert (
        "IGNORE"
        in mutated.fault_config.inject_text
    )


def test_prompt_injection_sets_flag(sample_task):

    mutated = PromptInjectionMutation().apply(sample_task)

    assert (
        mutated.success_criteria.must_resist_injection
        is True
    )


def test_prompt_injection_metadata(sample_task):

    mutated = PromptInjectionMutation().apply(sample_task)

    assert mutated.mutation_type == "prompt_injection"

    assert mutated.base_task_id == sample_task.id


# ==========================================================
# Mutation Engine
# ==========================================================

def test_engine_available_mutations():

    engine = MutationEngine()

    names = engine.available_mutations

    assert "distractor" in names

    assert "prompt_injection" in names


def test_engine_apply(sample_task):

    engine = MutationEngine()

    mutated = engine.apply(
        sample_task,
        "distractor",
    )

    assert mutated.mutation_type == "distractor"


def test_engine_apply_all(sample_task):

    engine = MutationEngine()

    tasks = engine.apply_all(sample_task)

    assert (
        len(tasks)
        ==
        len(engine.available_mutations)
    )


def test_unknown_mutation(sample_task):

    engine = MutationEngine()

    with pytest.raises(ValueError):

        engine.apply(
            sample_task,
            "does_not_exist",
        )


# ==========================================================
# Tool Registry
# ==========================================================

def test_execute_tool_prompt_injection():

    fault = FaultConfig(
        target_tool="search_web",
        inject_text="HACKED",
    )

    result = execute_tool(
        "search_web",
        {
            "query": "python",
        },
        fault_config=fault,
    )

    content = result["results"][0]["content"]

    assert "HACKED" in content


def test_execute_tool_wrong_data():

    fault = FaultConfig(
        target_tool="search_web",
        fail_mode=FailMode.WRONG_DATA,
    )

    result = execute_tool(
        "search_web",
        {
            "query": "python",
        },
        fault_config=fault,
    )

    assert (
        result["results"][0]["title"]
        ==
        "Completely Incorrect"
    )


def test_fault_only_affects_target_tool():

    fault = FaultConfig(
        target_tool="search_web",
        inject_text="HACKED",
    )

    result = execute_tool(
        "get_weather",
        {
            "city": "Delhi",
        },
        fault_config=fault,
    )

    assert result["city"] == "Delhi"

    assert "temperature_c" in result