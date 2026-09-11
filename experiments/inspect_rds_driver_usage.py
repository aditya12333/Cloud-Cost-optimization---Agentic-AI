import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"

SERVICE = "Amazon Relational Database Service"

DRIVER = (
    "$2.848 per RDS db.m5.4xlarge Multi-AZ instance hour "
    "(or partial hour) running PostgreSQL"
)

EPISODE_START = pd.Timestamp("2024-09-17 05:00:00")
EPISODE_END = pd.Timestamp("2024-09-19 00:00:00")

BASELINE_START = EPISODE_START - pd.Timedelta(days=7)
BASELINE_END = EPISODE_START


columns = [
    "ChargePeriodStart",
    "ProviderName",
    "ServiceName",
    "ChargeCategory",
    "ChargeDescription",
    "EffectiveCost",
    "BilledCost",
    "ConsumedQuantity",
    "ConsumedUnit",
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


driver = df[
    (df["ProviderName"] == "AWS")
    & (df["ServiceName"] == SERVICE)
    & (df["ChargeCategory"] == "Usage")
    & (df["ChargeDescription"] == DRIVER)
].copy()


episode = driver[
    (driver["ChargePeriodStart"] >= EPISODE_START)
    & (driver["ChargePeriodStart"] < EPISODE_END)
].copy()


baseline = driver[
    (driver["ChargePeriodStart"] >= BASELINE_START)
    & (driver["ChargePeriodStart"] < BASELINE_END)
].copy()


episode_hours = (
    EPISODE_END - EPISODE_START
) / pd.Timedelta(hours=1)

baseline_hours = 7 * 24

scale_factor = (
    episode_hours / baseline_hours
)


episode_cost = episode["EffectiveCost"].sum()
episode_quantity = episode["ConsumedQuantity"].sum()

expected_cost = (
    baseline["EffectiveCost"].sum()
    * scale_factor
)

expected_quantity = (
    baseline["ConsumedQuantity"].sum()
    * scale_factor
)


episode_unit_cost = (
    episode_cost / episode_quantity
    if episode_quantity > 0
    else None
)

baseline_unit_cost = (
    baseline["EffectiveCost"].sum()
    / baseline["ConsumedQuantity"].sum()
    if baseline["ConsumedQuantity"].sum() > 0
    else None
)


quantity_change_pct = (
    (
        episode_quantity
        - expected_quantity
    )
    / expected_quantity
    * 100
)


cost_change_pct = (
    (
        episode_cost
        - expected_cost
    )
    / expected_cost
    * 100
)


unit_cost_change_pct = (
    (
        episode_unit_cost
        - baseline_unit_cost
    )
    / baseline_unit_cost
    * 100
)


print("\n----------------------------")
print("RDS DRIVER USAGE SHIFT")
print("----------------------------")

print("Episode hours:", episode_hours)

print("\nCOST")
print("Episode cost:", episode_cost)
print("Expected cost:", expected_cost)
print("Cost change %:", cost_change_pct)

print("\nUSAGE")
print("Consumed unit:", episode["ConsumedUnit"].unique())
print("Episode quantity:", episode_quantity)
print("Expected quantity:", expected_quantity)
print("Quantity change %:", quantity_change_pct)

print("\nUNIT COST")
print("Episode unit cost:", episode_unit_cost)
print("Baseline unit cost:", baseline_unit_cost)
print("Unit cost change %:", unit_cost_change_pct)

print("\nSUB-ACCOUNTS")

print(
    episode.groupby("SubAccountName")
    .agg(
        cost=("EffectiveCost", "sum"),
        quantity=("ConsumedQuantity", "sum"),
    )
    .sort_values(
        "cost",
        ascending=False,
    )
    .to_string()
)