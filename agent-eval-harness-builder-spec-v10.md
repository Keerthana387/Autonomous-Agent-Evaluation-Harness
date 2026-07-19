# Builder Spec: Autonomous Agent Evaluation Harness

This document describes the system in enough detail to start implementing it directly — component responsibilities, data schemas, file structure, and a day-by-day Week 1 plan.

---

## 1. What You're Building, Precisely

A pipeline with six components that plugs together like this:

```
Task Suite (YAML)
      │
      ▼
Mutation Engine ──────► Perturbed Task Suite (YAML/JSON)
      │                         │
      │                         ▼
Tool Library ◄────────► Execution Harness ◄──── Target Agent
(mock tools)                    │
                                 ▼
                          Trace Store (SQLite)
                                 │
                                 ▼
                          Scoring Layer
                        (rules + LLM judge)
                                 │
                                 ▼
                          Scored Results (SQLite/JSON)
                                 │
                                 ▼
                          Dashboard (Streamlit)
```

You run one command: it loads tasks, mutates them, runs the target agent against every original + mutated task inside the mock tool environment, logs everything, scores everything, and gives you a report.

---

## 2. Component-by-Component Detail

### 2.1 Tool Library (`tools/`)

**Purpose:** A fixed set of fake tools the agent can call. Each tool is a Python function with a declared schema (so the agent knows how to call it) and a `fail_mode` parameter (so the harness can corrupt its output on demand).

**Structure:**
```python
# tools/registry.py
TOOLS = {
    "get_weather": {
        "description": "Get current weather for a city",
        "parameters": {
            "city": {"type": "string", "required": True}
        },
        "function": get_weather_impl
    },
    "search_web": { ... },
    "currency_convert": { ... },
    "get_stock_price": { ... },
    "send_email": { ... },
    "book_flight": { ... },
    "get_calendar_events": { ... },
    "create_calendar_event": { ... },
    "translate_text": { ... },
    "get_stock_price_v2": { ... },   # near-duplicate schema for confusion tests
    # aim for 12-18 tools total
}
```

Each `*_impl` function signature looks like:
```python
def get_weather_impl(city: str, fail_mode: str | None = None) -> dict:
    if fail_mode == "timeout":
        raise TimeoutError("Tool call timed out")
    if fail_mode == "malformed":
        return {"raw": "{{broken json not parseable"}
    if fail_mode == "wrong_data":
        return {"city": city, "temp_c": 9999, "condition": "unknown"}
    if fail_mode == "empty":
        return {}
    # normal deterministic fake response
    return {"city": city, "temp_c": 29, "condition": "humid", "rain_chance": 0.7}
```

**Key design rule:** tool *schemas* never change during a run. Only (a) which tools are exposed to the agent for a given task, and (b) the `fail_mode` passed at call-time, are varied. This keeps scoring tractable.

**Deliverable:** `tools/registry.py` + `tools/impls.py`, unit-testable independently of the agent.

---

### 2.2 Task Suite (`tasks/`)

**Purpose:** The `tasks/` package defines the benchmark itself. It contains the shared task schema (`models.py`), YAML loading (`loader.py`), benchmark validation (`validators.py`), and the benchmark task definitions (`base/*.yaml` and later `generated/*.yaml`).

**Schema (one file per task):**
```yaml
id: task_003
category: multi_step_chaining

prompt: "Find the latest news about NVIDIA and summarize it in one sentence."

available_tools:
  - get_news
  - summarize_text

expected_plan:
  - get_news
  - summarize_text

expected_tool_calls:
  - tool: get_news
  - tool: summarize_text

success_criteria:
  requires_multi_step: true

difficulty: base

notes: >
  Tests whether the agent correctly plans a two-step workflow instead of attempting to summarize without retrieving data first.
```

Tasks may optionally define an `expected_plan`, representing the optimal sequence of tool invocations. This is not required for execution, but later enables metrics such as planning accuracy, execution efficiency, and unnecessary tool usage.

### Internal Components

**models.py**

Contains the shared Pydantic models (`Task`, `SuccessCriteria`, `ExpectedToolCall`, `FaultConfig`) and enums (`TaskCategory`, `Difficulty`, `FailMode`). The `Task` model also includes `base_task_id` and `mutation_type` fields used to preserve lineage between base and mutated tasks. These are the canonical task definitions used throughout the project.

**loader.py**

Loads YAML files and validates them against the shared models.

**validators.py**

Performs benchmark-level validation such as duplicate IDs, invalid tool references, invalid expected tool calls, and category distribution checks.

**Categories to cover (aim ~15 base tasks across these in Week 1):**
1. `tool_selection` — select the appropriate tool while ignoring distractors and near-duplicate schemas.
2. `multi_step_chaining` — perform sequential reasoning where outputs from earlier tool calls are required by later ones.
3. `ambiguous_input` — recognize insufficient information and request clarification rather than guessing.
4. `error_handling` — respond gracefully to tool failures, malformed outputs, or clearly incorrect tool results.
5. `no_tool_needed` — recognize tasks solvable entirely through reasoning without unnecessary tool invocation.

**Deliverable:**

```
tasks/
├── models.py
├── loader.py
├── validators.py
├── base/
│   ├── task_001.yaml
│   └── ... task_015.yaml
└── generated/
```

- `models.py` — shared task models and enums.
- `loader.py` — YAML loading and schema validation.
- `validators.py` — benchmark consistency validation.
- `base/*.yaml` — realistic benchmark tasks.
- `generated/*.yaml` — produced later by the mutation engine.

---
### 2.3 Target Agent (`agent/`)

**Purpose:** The target agent is the system under evaluation. It is implemented as a provider-agnostic ReAct agent rather than using an existing framework (e.g. LangChain AgentExecutor). The agent is responsible only for orchestration—LLM providers handle all provider-specific logic.

### Design Goals

- Provider-independent orchestration.
- Single ReAct execution loop regardless of provider.
- Standardized request/response models across providers.
- Manual tool execution by the harness.
- Complete execution tracing.
- Deterministic, JSON-serializable traces.

### Architecture

```
Task
   │
   ▼
create_llm(provider, tools)
   │
   ▼
BaseLLM
   │
   ▼
LLMResponse
   │
   ▼
ReActLoop
   │
   ├── Final Answer → Trace.finish()
   └── Tool Calls → execute_tool() → ToolResult(s) → Next LLM Iteration
```

### Components

#### `agent/providers/base.py`

Defines the abstract provider interface:

```python
generate(
    conversation: list[ConversationTurn],
    tool_results: list[ToolResult] | None = None,
) -> LLMResponse
```

Every provider implements this interface.

#### `agent/providers/models.py`

Shared models:
- Role
- ConversationTurn
- ToolCall
- ToolResult
- FinishReason
- LLMResponse

Tool outputs are intentionally **not** conversation turns. Tool results are passed separately as `ToolResult` objects and converted into provider-native formats inside each provider.

#### `agent/providers/gemini.py`

Responsibilities:
- Load credentials.
- Validate requested tools.
- Build Gemini tool schemas.
- Convert conversations.
- Convert ToolResults.
- Parse Gemini responses.
- Never execute tools automatically.

#### `agent/llm.py`

Factory for creating provider instances.

#### `agent/runner.py`

Public entry point for benchmark execution.

Responsibilities:
- Build the provider.
- Build the initial conversation.
- Create the `ReActLoop`.
- Execute one benchmark task.
- Return the resulting `Trace`.

#### `agent/loop.py`

Execution flow:

1. Create Trace.
2. Initialize conversation.
3. Call `BaseLLM.generate()`.
4. Record the returned response.
5. Execute requested tools using `execute_tool()`.
6. Pass ToolResults into the next iteration.
7. Finish when the model returns a final response.
8. Stop after the configured maximum number of reasoning steps.
9. Record provider exceptions inside the trace instead of crashing.

#### `agent/trace.py`

Implements an event-sourced execution log.

Structure:
- Trace
- TraceStep
- ToolExecution

Features:
- Full reasoning history.
- Initial conversation stored once.
- One TraceStep per reasoning iteration.
- One ToolExecution per completed tool call.
- JSON serialization/deserialization.
- Explicit serialization of enums (`Role`, `FinishReason`).
- Statistics (`num_steps`, `num_tool_calls`, `num_failed_tool_calls`, `duration_seconds`, `successful`).

### Testing (Day 2)

Coverage includes:
- Provider tests
- ReAct loop unit tests
- Integration tests
- Trace serialization tests
- Multi-step reasoning
- Multiple tool calls
- Tool failures
- Unknown tools
- LLM exception handling
- Maximum-step termination

**Deliverables**

```
agent/
├── llm.py
├── loop.py
├── runner.py
├── prompts.py
├── trace.py
└── providers/
    ├── base.py
    ├── models.py
    └── gemini.py
```


---

### 2.4 Mutation Engine (`mutations/`)

**Purpose:** Take a base task and produce adversarial variants while preserving the original task.

The mutation subsystem is object-oriented and built around a shared `BaseMutation` interface. A central `MutationEngine` maintains a registry of mutation objects and dispatches them.

**Structure:**
```
mutations/
├── __init__.py
├── base.py
├── utils.py
├── distractor.py
├── prompt_injection.py
├── engine.py
└── generate_suite.py
```

**Week 1 mutation types**

- **Distractor tools:** clone the task, add irrelevant tools, update `must_not_call`, set `base_task_id`, `mutation_type`, and a new task id.
- **Prompt injection:** clone the task, attach `FaultConfig`, configure `target_tool` and `inject_text`, and set `must_resist_injection=True`.

The mutation layer never edits tool implementations directly. Instead, `execute_tool()` applies `FaultConfig` (`fail_mode` and `inject_text`) during tool execution.

`MutationEngine` supports registering mutations, applying a single mutation, or applying every registered mutation. `generate_suite.py` loads the base task suite, applies every registered mutation, and writes the results into `tasks/generated/`.

---

### 2.5 Execution Harness (`harness/`)

**Purpose:** Glue that runs every task (base + mutated) through the target agent(s) and persists results.

```python
def run_all(db_path: str = "benchmark.db"):
    conn = init_db(db_path)
    try:
        run_suite("tasks/base", conn)
        run_suite("tasks/generated", conn)
    finally:
        close_db(conn)

def run_suite(task_dir: str, conn):
    tasks = load_all_tasks(task_dir)
    for task in tasks:
        try:
            trace = run_task(task)
        except Exception as e:
            trace = Trace(task_id=task.id, error=str(e))
        save_trace(conn, trace)
```

Run async (`asyncio.gather` with a concurrency cap, e.g. 5) so a 15-task suite with 2 mutations each (45 runs) doesn't take forever serially.

**SQLite schema:**
```sql
CREATE TABLE traces (
    task_id TEXT PRIMARY KEY,
    base_task_id TEXT,
    mutation_type TEXT,
    agent_id TEXT,
    trace_json TEXT,
    final_answer TEXT,
    num_tool_calls INTEGER,
    error TEXT,
    created_at TIMESTAMP
);
```

**Deliverable:** `harness/runner.py`, `harness/db.py`.

---

### 2.6 Scoring Layer (`scoring/`)

**Purpose:** Convert execution traces into deterministic and semantic benchmark scores, then persist the results for reporting.

The scoring layer is split into two stages:

1. **Deterministic rule-based scoring** (`rules.py`) computes objective metrics directly from the `Task` and `Trace`.
2. **LLM judging** (`judge.py`) augments those results with semantic evaluation (grounding) without replacing the deterministic metrics.

### Structure

```
scoring/
├── __init__.py
├── models.py
├── rules.py
├── judge.py
└── run_scoring.py
```

### `models.py`

Defines the serializable `Score` model.

Stores:
- Task metadata (`task_id`, `agent_id`, `base_task_id`, `mutation_type`)
- Deterministic metrics
- LLM judge metrics
- Overall benchmark result
- Failed rule checks

The model supports:

```python
to_dict()
from_dict()
to_json()
from_json()
```

matching the serialization API used by `Trace`.

### `rules.py`

Implements deterministic evaluation.

Metrics include:

- correct tool usage
- forbidden tool detection
- tool precision
- tool recall
- planning correctness
- clarification requested
- tool failure handling
- prompt injection resistance

Each applicable metric contributes to:

```python
Score.failed_checks
Score.passed
```

without requiring any LLM calls.

### `judge.py`

Uses the provider abstraction (`create_llm()`) to perform semantic evaluation.

The judge receives:

- Task
- Trace
- Deterministic Score

and augments the existing `Score` with:

- `grounded`
- `judge_reasoning`

Invalid judge responses are handled gracefully without crashing the benchmark.

### `run_scoring.py`

Runs deterministic scoring over every stored trace.

Workflow:

```
SQLite Traces
      │
      ▼
Load Tasks
      │
      ▼
score_trace()
      │
      ▼
save_score()
      │
      ▼
SQLite Scores
```

Responsibilities:

- Load every task.
- Load every stored trace.
- Match traces to their originating task.
- Compute deterministic scores.
- Persist scores into the SQLite `scores` table.
- Skip traces whose task definition cannot be found.

### Database

The execution database now contains two independent tables:

- `traces`
- `scores`

Each score row stores metadata for querying together with the serialized `Score` object, allowing the scoring schema to evolve without requiring database migrations.

**Deliverables**

- `scoring/models.py`
- `scoring/rules.py`
- `scoring/judge.py`
- `scoring/run_scoring.py`
- Updated `harness/db.py` with score persistence
- Unit tests:
  - `tests/test_rules.py`
  - `tests/test_scoring.py`
  - `tests/test_judge.py`
  - Updated `tests/test_db.py`

### 2.7 Dashboard (`dashboard/`)

**Purpose:** A multi-page Streamlit dashboard for running benchmarks, selecting benchmark databases and exploring benchmark results.

### Architecture

```
dashboard/
├── app.py
├── sidebar.py
├── database.py
└── pages/
    ├── 0_Home.py
    ├── 1_Overview.py
    ├── 2_Tasks.py
    ├── 3_Trace_Viewer.py
    └── 4_Analytics.py
```

### Features

- Shared sidebar on every page.
- Switch between benchmark databases stored in `databases/`.
- Run the full benchmark pipeline from the Home page.
- Overview page with KPIs and charts.
- Tasks page for browsing benchmark executions.
- Trace Viewer for inspecting traces and scores.
- Analytics page for aggregate benchmark statistics.

`dashboard/database.py` only performs read operations. Database creation and initialization are handled by `harness/db.py`.

The dashboard integrates directly with:

```
generate_suite()
      ↓
run_all()
      ↓
score_database()
```

After a pipeline run, the selected database is automatically updated.

---

## 3. Repository Structure

```
agent-eval-harness/
├── tools/
│   ├── registry.py
│   └── impls.py
├── tasks/
│   ├── models.py
│   ├── loader.py
│   ├── validators.py
│   ├── base/
│   └── generated/
├── agent/
│   ├── llm.py
│   ├── runner.py
│   ├── loop.py
│   ├── trace.py
│   └── providers/
│       ├── base.py
│       ├── models.py
│       └── gemini.py
├── mutations/
│   ├── __init__.py
│   ├── base.py
│   ├── utils.py
│   ├── distractor.py
│   ├── prompt_injection.py
│   ├── engine.py
│   └── generate_suite.py
├── harness/
│   ├── runner.py
│   └── db.py
├── scoring/
│   ├── __init__.py
│   ├── models.py
│   ├── rules.py
│   ├── judge.py
│   └── run_scoring.py
├── dashboard/
│   ├── app.py
│   ├── sidebar.py
│   ├── database.py
│   └── pages/
│       ├── 0_Home.py
│       ├── 1_Overview.py
│       ├── 2_Tasks.py
│       ├── 3_Trace_Viewer.py
│       └── 4_Analytics.py
├── databases/
├── tests/
├── run_pipeline.py
├── requirements.txt
└── README.md
```

`run_pipeline.py` remains the single entry point that orchestrates the complete benchmark pipeline.


## 4. Detailed Week 1 Timeline

**Goal for the week:** a thin, fully working vertical slice — not every mutation type, not a polished dashboard, but every stage connected and runnable end to end by Day 7.

### Day 1 — Tool library + task suite
- Set up repo structure, `requirements.txt` (`anthropic`, `pyyaml`, `streamlit`, `pytest`)
- Implement 12-15 mock tools in `tools/impls.py` with `fail_mode` support
- Define `TOOLS` registry with schemas in `tools/registry.py`
- Write 15 realistic benchmark tasks in `tasks/base/*.yaml` across the five evaluation categories listed in 2.2. Include `expected_plan` for multi-step tasks where appropriate.
- Implement `tasks/models.py` (shared Pydantic models and enums)
- Implement `tasks/loader.py` (YAML loading and schema validation)
- Implement `tasks/validators.py` (benchmark consistency checks)
- **End of day check:** `python -c "from tasks.loader import load_all; print(len(load_all('tasks/base')))"` prints 15, no errors

### Day 2 — Target agent + trace logging
- Implement `agent/trace.py` (the `Trace` dataclass/schema from 2.3)
- Implement the provider-independent model layer and `BaseLLM`
- Implement the Gemini provider
- Implement the provider-independent ReAct loop with manual tool execution, trace logging, provider exception handling and maximum-step protection
- Implement JSON-serializable tracing (`Trace`, `TraceStep`, `ToolExecution`)
- Add comprehensive provider, unit and integration tests
- **End of day check:** all provider, loop and trace tests pass and the agent correctly solves representative base tasks

### Day 3 — Mutation engine
- Implement the object-oriented mutation framework (`BaseMutation`, utilities and `MutationEngine`)
- Implement the two Week 1 mutation types (distractor tools and prompt injection)
- Update `execute_tool()` to centrally apply `FaultConfig` (`fail_mode` and `inject_text`)
- Implement `mutations/generate_suite.py` to apply every registered mutation and write `tasks/generated/*.yaml`
- Add comprehensive mutation unit tests (including tool fault injection) using shared pytest fixtures
- Manually inspect generated files to confirm metadata, YAML validity and injected content
- **End of day check:** `tasks/generated/` contains 30 files (15 tasks × 2 mutations) and all mutation tests pass.

### Day 4 — Execution harness
- Implement `harness/db.py` (SQLite schema + insert/query helpers)
- Implement `agent/runner.py` as the public execution entry point
- Implement `harness/runner.py` with robust error handling and trace persistence
- Run the full suite (base + generated = 45 tasks) through the agent
- Add harness integration/unit tests
- **Optional (Week 2):** add async concurrency for larger benchmark suites
- **End of day check:** `traces` table has 45 rows, no unhandled exceptions, spot-check 3 traces manually

### Day 5 — Scoring layer
- Implement `scoring/models.py` (serializable Score model)
- Implement `scoring/rules.py` (deterministic scoring: tool usage, planning, clarification, tool failures, prompt injection resistance)
- Extend `harness/db.py` with SQLite score persistence (`scores` table)
- Implement `scoring/run_scoring.py` to score every stored trace and persist results
- Implement `scoring/judge.py` using the provider abstraction to augment scores with semantic grounding evaluation
- Add unit and integration tests for rules, scoring pipeline, judge and database persistence
- **End of day check:** every trace has a corresponding score row, all scoring tests pass, and aggregate pass rate can be printed by category.

### Day 6 — Dashboard (Implemented)
- Implement the multi-page Streamlit dashboard with Home, Overview, Tasks, Trace Viewer and Analytics pages.
- Integrate the dashboard with `run_pipeline.py`, allowing benchmarks to be launched directly from the Home page while supporting multiple SQLite benchmark databases.
- **End of day check:** The dashboard can launch benchmarks, switch databases and visualize benchmark results.

### Day 7 — Buffer / stabilization
- Re-run the full pipeline 2-3 times, note anything flaky (LLM non-determinism, occasional malformed tool_use response, rate limits)
- Fix whatever's actually broken — do not add new mutation types or dashboard features today
- Write a short `README.md` stub: what this is, how to run it, current limitations (this will be expanded in Week 4, but start it now while context is fresh)
- **End of day check:** a person cloning the repo fresh, with an API key set, can run `python run_pipeline.py && streamlit run dashboard/app.py` and see results

---

## 5. Definition of Done for Week 1

- [ ] 15 realistic benchmark tasks across five categories, schema-validated on load, with planning metadata where applicable
- [ ] 12-15 mock tools with fault-injection support
- [ ] One hand-built agent loop with full trace logging
- [ ] 2 working mutation types generating 30 adversarial task variants
- [ ] Execution harness runs all 45 tasks and persists traces to SQLite without crashing
- [ ] Scoring layer produces both rule-based and LLM-judge scores per trace
- [ ] Dashboard launches benchmarks, manages multiple benchmark databases, displays analytics and supports trace inspection.
- [ ] Single command (`run_pipeline.py`) runs the whole thing end to end

If Day 7 ends with all of the above true, you're exactly on pace for the Week 2-4 plan (deepen mutations, validate the judge, add a second agent, scale up, polish, and write up).
