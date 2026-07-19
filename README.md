# Autonomous Agent Evaluation Harness

A modular benchmarking framework for evaluating LLM-powered autonomous agents under realistic and adversarial conditions.

The project provides an end-to-end evaluation pipeline that generates benchmark tasks, creates adversarial task variants, executes an agent inside a controlled tool environment, records detailed execution traces, scores the results, and visualizes everything through an interactive Streamlit dashboard.

---

## Features

- **Provider-agnostic agent architecture**
  - Easily extendable to multiple LLM providers.
  - Current implementation supports **Google Gemini**.

- **ReAct-based execution loop**
  - Manual tool execution.
  - Multi-step reasoning.
  - Configurable maximum reasoning steps.
  - Complete execution tracing.

- **Mock tool environment**
  - Deterministic tool implementations.
  - Tool fault injection.
  - Distractor tools.
  - Prompt injection testing.

- **Task mutation engine**
  - Generates adversarial benchmark variants.
  - Preserves lineage using `base_task_id`.
  - Multiple mutation strategies.

- **Execution harness**
  - Executes entire benchmark suites.
  - Persists traces to SQLite.
  - Robust error handling.

- **Scoring framework**
  - Rule-based evaluation.
  - LLM judge support.
  - Detailed per-task reports.

- **Interactive dashboard**
  - Run benchmarks directly from the UI.
  - Support for multiple benchmark databases.
  - Trace inspection.
  - Analytics and visualizations.

---

# System Architecture

```
Base Tasks
     │
     ▼
Mutation Engine
     │
     ▼
Generated Tasks
     │
     ▼
Execution Harness
     │
     ▼
Target Agent (ReAct)
     │
     ▼
Tool Execution
     │
     ▼
Execution Traces
     │
     ▼
Scoring Layer
     │
     ▼
SQLite Database
     │
     ▼
Streamlit Dashboard
```

---

# Repository Structure

```
agent-eval-harness/
│
├── agent/
│   ├── providers/
│   ├── llm.py
│   ├── loop.py
│   ├── runner.py
│   └── trace.py
│
├── dashboard/
│   ├── app.py
│   ├── sidebar.py
│   ├── database.py
│   └── pages/
│
├── harness/
│   ├── db.py
│   └── runner.py
│
├── mutations/
│
├── scoring/
│
├── tasks/
│   ├── base/
│   └── generated/
│
├── tools/
│
├── tests/
│
├── databases/
│
├── run_pipeline.py
│
└── README.md
```

---

# Evaluation Pipeline

Running the benchmark performs the following steps:

```
Load Base Tasks
        │
        ▼
Generate Mutations
        │
        ▼
Execute Agent
        │
        ▼
Store Execution Traces
        │
        ▼
Score Traces
        │
        ▼
Populate Dashboard Database
```

---

# Dashboard

The Streamlit dashboard provides a complete interface for running and analyzing benchmarks.

## Home

- Select provider
- Select existing benchmark database
- Create new benchmark database
- Run the complete evaluation pipeline

## Overview

- Benchmark summary
- Success rate
- Average execution statistics
- Recent benchmark runs

## Tasks

- Browse all benchmark tasks
- View execution metadata
- Filter benchmark results

## Trace Viewer

- Inspect complete execution traces
- View reasoning steps
- Inspect tool calls
- View scoring details

## Analytics

- Aggregate benchmark statistics
- Mutation analysis
- Execution metrics
- Performance visualization

---

# Database Management

Each benchmark run is stored independently.

```
databases/

benchmark_default.db

benchmark_20260719_151032.db

benchmark_20260720_101215.db
```

The dashboard allows switching between benchmark databases without rerunning previous experiments.

---

# Agent Architecture

The evaluated agent uses a provider-independent ReAct loop.

```
Task
   │
   ▼
LLM Provider
   │
   ▼
Reasoning
   │
   ▼
Tool Calls
   │
   ▼
Tool Execution
   │
   ▼
Tool Results
   │
   ▼
Next Reasoning Step
   │
   ▼
Final Answer
```

Every reasoning iteration is recorded as a structured execution trace.

---

# Testing

The project includes unit and integration tests for:

- Provider implementation
- ReAct execution loop
- Trace serialization
- Mutation engine
- Scoring layer
- Execution harness
- Pipeline components

Run all tests:

```bash
pytest
```

---

# Running the Project

## 1. Clone the repository

```bash
git clone <repository-url>
cd agent-eval-harness
```

---

## 2. Create a virtual environment

Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Gemini API

Create:

```
agent/providers/.env
```

Example:

```
GEMINI_API_KEY=YOUR_API_KEY
```

---

## 5. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

From the **Home** page you can:

- create a new benchmark database
- select an existing database
- run the complete benchmark pipeline

---

# Current Status

## Version 1 Complete

Implemented:

- Provider-independent agent framework
- Gemini provider
- ReAct execution loop
- Structured execution tracing
- Mock tool environment
- Mutation engine
- SQLite persistence
- Rule-based scoring
- Interactive Streamlit dashboard
- Multi-database support
- Pipeline execution from the dashboard

---

# Future Work

- Additional LLM providers (OpenAI, Anthropic, Ollama, etc.)
- More mutation strategies
- Richer scoring metrics
- Concurrent benchmark execution
- Benchmark comparison across databases
- Export reports
- Advanced analytics
- CI/CD integration

---

# License

This project is intended for educational and research purposes.