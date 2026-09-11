import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"


columns = [
    "ChargePeriodStart",
    "ProviderName",
    "ServiceName",
    "ChargeCategory",
    "EffectiveCost",
    "SubAccountName",
]


df = pd.read_csv(
    DATA_PATH,
    usecols=columns,
    low_memory=False,
)

df["ChargePeriodStart"] = pd.to_datetime(
    df["ChargePeriodStart"]
)


s3 = df[
    (df["ProviderName"] == "AWS")
    & (
        df["ServiceName"]
        == "Amazon Simple Storage Service"
    )
    & (df["ChargeCategory"] == "Usage")
].copy()


# ==================================================
# SPIKE WINDOW
# ==================================================

spike = s3[
    (
        s3["ChargePeriodStart"]
        >= "2024-09-17 23:00:00"
    )
    & (
        s3["ChargePeriodStart"]
        <= "2024-09-18 22:59:59"
    )
]


spike_accounts = (
    spike.groupby(
        "SubAccountName",
        dropna=False
    )["EffectiveCost"]
    .sum()
    .rename("spike_cost_24h")
)


# ==================================================
# PREVIOUS 7-DAY BASELINE
# ==================================================

baseline = s3[
    (
        s3["ChargePeriodStart"]
        >= "2024-09-10 23:00:00"
    )
    & (
        s3["ChargePeriodStart"]
        <= "2024-09-17 22:59:59"
    )
]


baseline_accounts = (
    baseline.groupby(
        "SubAccountName",
        dropna=False
    )["EffectiveCost"]
    .sum()
    .div(7)
    .rename("baseline_daily_cost")
)


# ==================================================
# COMPARE
# ==================================================

comparison = pd.concat(
    [
        spike_accounts,
        baseline_accounts,
    ],
    axis=1,
).fillna(0)


comparison["absolute_change"] = (
    comparison["spike_cost_24h"]
    - comparison["baseline_daily_cost"]
)


comparison["spike_share_pct"] = (
    comparison["spike_cost_24h"]
    / comparison["spike_cost_24h"].sum()
    * 100
)


comparison = comparison.sort_values(
    "absolute_change",
    ascending=False,
)


print("\n----------------------------")
print("S3 SUBACCOUNT SHIFT")
print("----------------------------")

print(
    comparison.head(20).to_string()
)