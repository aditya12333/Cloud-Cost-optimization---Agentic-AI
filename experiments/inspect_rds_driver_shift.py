import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"

SERVICE = "Amazon Relational Database Service"

EPISODE_START = pd.Timestamp(
    "2024-09-17 05:00:00"
)

EPISODE_END = pd.Timestamp(
    "2024-09-18 23:59:59"
)


columns = [
    "ChargePeriodStart",
    "ProviderName",
    "ServiceName",
    "ChargeCategory",
    "ChargeDescription",
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


rds = df[
    (df["ProviderName"] == "AWS")
    & (df["ServiceName"] == SERVICE)
    & (df["ChargeCategory"] == "Usage")
].copy()


# ==================================================
# EPISODE
# ==================================================

episode = rds[
    (rds["ChargePeriodStart"] >= EPISODE_START)
    & (rds["ChargePeriodStart"] <= EPISODE_END)
].copy()


episode_hours = (
    (EPISODE_END - EPISODE_START)
    / pd.Timedelta(hours=1)
    + 1
)


# ==================================================
# PREVIOUS 7-DAY BASELINE
# ==================================================

baseline_end = EPISODE_START

baseline_start = (
    baseline_end - pd.Timedelta(days=7)
)

baseline = rds[
    (rds["ChargePeriodStart"] >= baseline_start)
    & (rds["ChargePeriodStart"] < baseline_end)
].copy()


# Convert 7-day historical spend to the
# expected spend over an episode of this duration.
scale_factor = (
    episode_hours / (7 * 24)
)


# ==================================================
# SUB-ACCOUNT COMPARISON
# ==================================================

episode_accounts = (
    episode.groupby("SubAccountName")["EffectiveCost"]
    .sum()
    .rename("episode_cost")
)


baseline_accounts = (
    baseline.groupby("SubAccountName")["EffectiveCost"]
    .sum()
    .mul(scale_factor)
    .rename("expected_cost")
)


account_comparison = pd.concat(
    [
        episode_accounts,
        baseline_accounts,
    ],
    axis=1,
).fillna(0.0)


account_comparison["absolute_change"] = (
    account_comparison["episode_cost"]
    - account_comparison["expected_cost"]
)


account_comparison = account_comparison.sort_values(
    "absolute_change",
    ascending=False,
)


print("\n----------------------------")
print("RDS SUBACCOUNT DRIVER SHIFT")
print("----------------------------")

print(
    account_comparison
    .head(15)
    .to_string()
)


# ==================================================
# CHARGE DESCRIPTION COMPARISON
# ==================================================

episode_descriptions = (
    episode.groupby("ChargeDescription")["EffectiveCost"]
    .sum()
    .rename("episode_cost")
)


baseline_descriptions = (
    baseline.groupby("ChargeDescription")["EffectiveCost"]
    .sum()
    .mul(scale_factor)
    .rename("expected_cost")
)


description_comparison = pd.concat(
    [
        episode_descriptions,
        baseline_descriptions,
    ],
    axis=1,
).fillna(0.0)


description_comparison["absolute_change"] = (
    description_comparison["episode_cost"]
    - description_comparison["expected_cost"]
)


description_comparison = (
    description_comparison
    .sort_values(
        "absolute_change",
        ascending=False,
    )
)


print("\n----------------------------")
print("RDS CHARGE DRIVER SHIFT")
print("----------------------------")

print(
    description_comparison
    .head(15)
    .to_string()
)