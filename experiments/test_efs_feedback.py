from real_driver_evidence import (
    load_driver_data,
    check_cost_driver,
)

from real_feedback import (
    interpret_driver_evidence,
)


driver_data = load_driver_data()


evidence, _ = check_cost_driver(
    driver_data,
    service_name=(
        "Amazon Elastic File System"
    ),
    current_hour=(
        "2024-09-22 01:00:00"
    ),
)


feedback = interpret_driver_evidence(
    evidence
)


print("\n----------------------------")
print("EFS FEEDBACK TEST")
print("----------------------------")

print(
    "Effective cost change:",
    evidence["cost_change_pct"]
)

print(
    "Billed cost change:",
    evidence[
        "billed_cost_change_pct"
    ]
)

print(
    "Usage change:",
    evidence["usage_change_pct"]
)

print(
    "Billed unit-cost change:",
    evidence[
        "unit_cost_change_pct"
    ]
)

print(
    "Feedback:",
    feedback
)