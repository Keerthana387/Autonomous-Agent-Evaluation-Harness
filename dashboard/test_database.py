from database import (
    database_exists,
    get_score,
    get_summary,
    get_tasks,
    get_trace,
    validate_schema,
)


print("=" * 60)
print("Dashboard Database Test")
print("=" * 60)

print("\nDatabase Exists")
print("----------------")
print(database_exists())

print("\nSchema Valid")
print("-------------")
print(validate_schema())

print("\nSummary")
print("--------")
print(get_summary())

print("\nTasks")
print("------")
print(get_tasks().head())

tasks = get_tasks()

if not tasks.empty:

    task_id = tasks.iloc[0]["task_id"]

    print(f"\nFirst Task: {task_id}")
    print("-" * 30)

    print("\nTrace JSON")
    print(get_trace(task_id))

    print("\nScore JSON")
    print(get_score(task_id))