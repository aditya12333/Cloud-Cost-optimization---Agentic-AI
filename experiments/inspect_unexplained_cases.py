import pandas as pd


PATH = (
    "results/real_two_stage_agent_decisions.csv"
)


df = pd.read_csv(
    PATH,
    parse_dates=["hour"],
)


cases = df[
    df["feedback"]
    ==
    "UNEXPLAINED_DRIVER_COST_INCREASE"
].copy()


print("\n----------------------------")
print("UNEXPLAINED REAL CASES")
print("----------------------------")

print(
    "Total:",
    len(cases)
)


columns = [
    "hour",
    "ServiceName",

    "initial_action",
    "final_action",

    "initial_cost_incident",
    "final_cost_incident",

    "driver_description",
    "driver_sub_account",

    "driver_cost_change_pct",
    "driver_usage_change_pct",
    "driver_unit_cost_change_pct",
]


print(
    cases[
        columns
    ].to_string(
        index=False
    )
)