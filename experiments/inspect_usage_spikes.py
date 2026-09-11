import pandas as pd


DATA_PATH = "data/real/aws_real_features_v2.csv"


df = pd.read_csv(
    DATA_PATH,
    parse_dates=["hour"]
)

valid = df[
    df["baseline_usage_cost_7d"].notna()
].copy()


columns = [
    "hour",
    "ServiceName",
    "usage_cost_24h",
    "baseline_usage_cost_7d",
    "usage_cost_change_pct",
    "credit_cost_24h",
    "credit_offset_ratio",
    "net_cost_24h",
]


print("\n----------------------------")
print("TOP 20 USAGE COST INCREASES")
print("----------------------------")

print(
    valid
    .sort_values(
        "usage_cost_change_pct",
        ascending=False
    )
    [columns]
    .head(20)
    .to_string(index=False)
)


print("\n----------------------------")
print("TOP 20 USAGE COST DECREASES")
print("----------------------------")

print(
    valid
    .sort_values(
        "usage_cost_change_pct"
    )
    [columns]
    .head(20)
    .to_string(index=False)
)