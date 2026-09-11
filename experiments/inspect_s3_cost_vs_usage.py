import pandas as pd


COST_PATH = "data/real/aws_real_features_v2.csv"
USAGE_PATH = "data/real/aws_real_usage_features.csv"


cost_df = pd.read_csv(
    COST_PATH,
    parse_dates=["hour"],
)

usage_df = pd.read_csv(
    USAGE_PATH,
    parse_dates=["hour"],
)


SERVICE = "Amazon Simple Storage Service"

SPIKE_HOUR = pd.Timestamp(
    "2024-09-18 22:00:00"
)


# ==================================================
# COST SIGNAL
# ==================================================

cost_row = cost_df[
    (cost_df["ServiceName"] == SERVICE)
    & (cost_df["hour"] == SPIKE_HOUR)
]


print("\n----------------------------")
print("S3 COST SIGNAL")
print("----------------------------")

print(
    cost_row[
        [
            "hour",
            "usage_cost_24h",
            "baseline_usage_cost_7d",
            "usage_cost_change_pct",
            "credit_cost_24h",
            "net_cost_24h",
        ]
    ].to_string(index=False)
)


# ==================================================
# S3 DATA-TRANSFER USAGE
# ==================================================

gb_row = usage_df[
    (usage_df["ServiceName"] == SERVICE)
    & (usage_df["ConsumedUnit"] == "GB")
    & (usage_df["hour"] == SPIKE_HOUR)
]


print("\n----------------------------")
print("S3 GB USAGE SIGNAL")
print("----------------------------")

print(
    gb_row[
        [
            "hour",
            "current_usage",
            "baseline_usage",
            "usage_change_pct",
        ]
    ].to_string(index=False)
)


# ==================================================
# S3 STORAGE USAGE
# ==================================================

storage_day = SPIKE_HOUR.normalize()

storage_row = usage_df[
    (usage_df["ServiceName"] == SERVICE)
    & (usage_df["ConsumedUnit"] == "GB-Months")
    & (usage_df["hour"] == storage_day)
]


print("\n----------------------------")
print("S3 STORAGE USAGE SIGNAL")
print("----------------------------")

print(
    storage_row[
        [
            "hour",
            "current_usage",
            "baseline_usage",
            "usage_change_pct",
        ]
    ].to_string(index=False)
)