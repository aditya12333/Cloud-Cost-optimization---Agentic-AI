import pandas as pd


DATA_PATH = (
    "results/real_two_stage_agent_decisions.csv"
)


df = pd.read_csv(
    DATA_PATH,
    parse_dates=["hour"],
)


# ==================================================
# FEEDBACK VS ACTION TRANSITION
# ==================================================

df["transition"] = (
    df["initial_action"]
    + " -> "
    + df["final_action"]
)


print("\n----------------------------")
print("FEEDBACK VS TRANSITION")
print("----------------------------")

print(
    pd.crosstab(
        df["feedback"],
        df["transition"],
    ).to_string()
)


# ==================================================
# FINAL ESCALATIONS
# ==================================================

print("\n----------------------------")
print("FINAL ESCALATIONS")
print("----------------------------")

escalations = df[
    df["final_action"] == "ESCALATE"
].copy()

print(
    "Total final escalations:",
    len(escalations)
)

print("\nFeedback causing escalation:")

print(
    escalations["feedback"]
    .value_counts()
    .to_string()
)


columns = [
    "hour",
    "ServiceName",
    "initial_action",
    "feedback",
    "driver_description",
    "driver_sub_account",
    "driver_cost_change_pct",
    "driver_usage_change_pct",
    "driver_unit_cost_change_pct",
    "initial_cost_incident",
    "final_cost_incident",
    "final_action",
]


print("\nTop final escalations:")

print(
    escalations
    .sort_values(
        "final_cost_incident",
        ascending=False,
    )
    [columns]
    .head(15)
    .to_string(index=False)
)


# ==================================================
# DE-ESCALATIONS TO WAIT
# ==================================================

print("\n----------------------------")
print("DE-ESCALATIONS TO WAIT")
print("----------------------------")

deescalated = df[
    (df["initial_action"] != "WAIT")
    & (df["final_action"] == "WAIT")
]

print(
    "Total:",
    len(deescalated)
)

print("\nFeedback:")

print(
    deescalated["feedback"]
    .value_counts()
    .to_string()
)