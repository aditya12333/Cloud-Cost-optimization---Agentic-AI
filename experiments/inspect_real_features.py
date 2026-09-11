import pandas as pd


DATA_PATH = "data/real/aws_real_features.csv"


df = pd.read_csv(
    DATA_PATH,
    parse_dates=["hour"]
)

valid = df[
    df["baseline_cost_7d"].notna()
].copy()


print("\n----------------------------")
print("BASELINE QUALITY")
print("----------------------------")

print(
    "Baseline <= 0:",
    (valid["baseline_cost_7d"] <= 0).sum()
)

print(
    "Baseline between 0 and $1:",
    (
        (valid["baseline_cost_7d"] > 0)
        & (valid["baseline_cost_7d"] < 1)
    ).sum()
)


print("\n----------------------------")
print("TOP 15 COST INCREASES")
print("----------------------------")

columns = [
    "hour",
    "ServiceName",
    "current_cost_24h",
    "baseline_cost_7d",
    "cost_change_pct",
]

print(
    valid
    .sort_values(
        "cost_change_pct",
        ascending=False
    )
    [columns]
    .head(15)
    .to_string(index=False)
)


print("\n----------------------------")
print("TOP 15 COST DECREASES")
print("----------------------------")

print(
    valid
    .sort_values(
        "cost_change_pct"
    )
    [columns]
    .head(15)
    .to_string(index=False)
)