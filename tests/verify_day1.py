"""
Day 1 Acceptance Test

Verifies:
- Tool registry
- Tool implementations
- Failure modes
- Task loading
- Benchmark validation

Run:

    python tests/verify_day1.py
"""

from pathlib import Path
import sys

# Allow running from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from tasks.loader import load_all_tasks
from tasks.validators import validate_tasks
from tools.registry import TOOLS


# ==========================================================
# Pretty Printing
# ==========================================================

PASS = "✓"
FAIL = "✗"


def heading(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def success(message: str):
    print(f"{PASS} {message}")


def failure(message: str):
    print(f"{FAIL} {message}")
    raise SystemExit(1)


# ==========================================================
# Registry Verification
# ==========================================================

def verify_registry():

    heading("Checking Tool Registry")

    if len(TOOLS) < 15:
        failure(
            f"Expected at least 15 tools, found {len(TOOLS)}."
        )

    for name, tool in TOOLS.items():

        required = [
            "description",
            "parameters",
            "function"
        ]

        for field in required:

            if field not in tool:
                failure(
                    f"{name}: missing '{field}'."
                )

        if not callable(tool["function"]):
            failure(
                f"{name}: function is not callable."
            )

    success(f"{len(TOOLS)} tools registered.")


# ==========================================================
# Tool Execution
# ==========================================================

def verify_tools():

    heading("Checking Tool Execution")

    sample_args = {

        "get_weather":
            {"city": "Mumbai"},

        "search_web":
            {"query": "Artificial Intelligence"},

        "currency_convert":
            {
                "amount": 100,
                "from_currency": "USD",
                "to_currency": "INR"
            },

        "get_stock_price":
            {"ticker": "AAPL"},

        "send_email":
            {
                "recipient": "alice@example.com",
                "subject": "Test",
                "body": "Hello"
            },

        "book_flight":
            {
                "origin": "Delhi",
                "destination": "Mumbai",
                "date": "2026-07-20"
            },

        "get_calendar_events":
            {"date": "2026-07-20"},

        "create_calendar_event":
            {
                "title": "Meeting",
                "date": "2026-07-20",
                "time": "10:00"
            },

        "translate_text":
            {
                "text": "Hello",
                "target_language": "French"
            },

        "get_stock_price_v2":
            {"symbol": "AAPL"},

        "calculator":
            {
                "operation": "add",
                "a": 10,
                "b": 20
            },

        "get_news":
            {"topic": "AI"},

        "search_documents":
            {"query": "policy"},

        "summarize_text":
            {
                "text": "This is a long paragraph for testing."
            },

        "get_current_time":
            {},

        "lookup_contact":
            {"name": "Alice"}
    }

    for tool_name, kwargs in sample_args.items():

        try:

            result = TOOLS[tool_name]["function"](
                **kwargs
            )

            if result is None:
                failure(
                    f"{tool_name} returned None."
                )

        except Exception as e:

            failure(
                f"{tool_name} failed.\n{e}"
            )

    success("All tools execute successfully.")


# ==========================================================
# Failure Modes
# ==========================================================

def verify_failure_modes():

    heading("Checking Failure Modes")

    weather = TOOLS["get_weather"]["function"]

    try:

        weather(
            city="Mumbai",
            fail_mode="timeout"
        )

        failure("Timeout mode failed.")

    except TimeoutError:
        pass

    malformed = weather(
        city="Mumbai",
        fail_mode="malformed"
    )

    if not isinstance(malformed, dict):
        failure("Malformed response invalid.")

    empty = weather(
        city="Mumbai",
        fail_mode="empty"
    )

    if empty != {}:
        failure("Empty fail mode incorrect.")

    wrong = weather(
        city="Mumbai",
        fail_mode="wrong_data"
    )

    if wrong["temperature_c"] != 999:
        failure("Wrong data mode failed.")

    success("Failure modes verified.")


# ==========================================================
# Tasks
# ==========================================================

def verify_tasks():

    heading("Checking Benchmark Tasks")

    tasks = load_all_tasks(
        PROJECT_ROOT / "tasks" / "base"
    )

    if len(tasks) != 15:

        failure(
            f"Expected 15 tasks, got {len(tasks)}."
        )

    validate_tasks(tasks)

    success("All benchmark tasks validated.")

    return tasks


# ==========================================================
# Statistics
# ==========================================================

def print_summary(tasks):

    heading("Summary")

    print(f"Tools : {len(TOOLS)}")
    print(f"Tasks : {len(tasks)}")

    print()

    from collections import Counter

    counts = Counter(
        task.category.value
        for task in tasks
    )

    for category, count in counts.items():

        print(
            f"{category:<25}"
            f"{count}"
        )


# ==========================================================
# Main
# ==========================================================

def main():

    verify_registry()

    verify_tools()

    verify_failure_modes()

    tasks = verify_tasks()

    print_summary(tasks)

    heading("DAY 1 COMPLETE")

    success(
        "Everything passed. Ready for Day 2."
    )


if __name__ == "__main__":
    main()