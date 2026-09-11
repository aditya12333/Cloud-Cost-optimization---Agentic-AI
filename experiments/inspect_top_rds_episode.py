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
    "ChargeFrequency",
    "ChargeDescription",
    "EffectiveCost",
    "BilledCost",
    "ConsumedQuantity",
    "ConsumedUnit",
    "SubAccountName",
    "RegionName",
]


print("Loading RDS episode data...")

df = pd.read_csv(
    DATA_PATH,
    usecols=columns,
    low_memory=False,
)

df["ChargePeriodStart"] = pd.to_datetime(
    df["ChargePeriodStart"]
)

episode = df[
    (df["ProviderName"] == "AWS")
    & (df["ServiceName"] == SERVICE)
    & (df["ChargePeriodStart"] >= EPISODE_START)
    & (df["ChargePeriodStart"] <= EPISODE_END)
].copy()


print("\n----------------------------")
print("RDS HIGH-RISK EPISODE")
print("----------------------------")

print("Rows:", len(episode))

print("\nCOST BY CHARGE CATEGORY")

print(
    episode.groupby(
        "ChargeCategory",
        dropna=False,
    )
    .agg(
        effective_cost=("EffectiveCost", "sum"),
        billed_cost=("BilledCost", "sum"),
        rows=("EffectiveCost", "size"),
    )
    .sort_values(
        "effective_cost",
        ascending=False,
    )
    .to_string()
)


print("\nTOP CHARGE DESCRIPTIONS")

print(
    episode.groupby(
        "ChargeDescription",
        dropna=False,
    )
    .agg(
        effective_cost=("EffectiveCost", "sum"),
        billed_cost=("BilledCost", "sum"),
        rows=("EffectiveCost", "size"),
    )
    .sort_values(
        "effective_cost",
        ascending=False,
    )
    .head(15)
    .to_string()
)


print("\nUSAGE BY UNIT")

print(
    episode[
        episode["ChargeCategory"] == "Usage"
    ]
    .groupby(
        "ConsumedUnit",
        dropna=False,
    )
    .agg(
        quantity=("ConsumedQuantity", "sum"),
        effective_cost=("EffectiveCost", "sum"),
    )
    .sort_values(
        "effective_cost",
        ascending=False,
    )
    .to_string()
)


print("\nTOP SUB-ACCOUNTS")

print(
    episode[
        episode["ChargeCategory"] == "Usage"
    ]
    .groupby(
        "SubAccountName",
        dropna=False,
    )["EffectiveCost"]
    .sum()
    .sort_values(
        ascending=False,
    )
    .head(15)
    .to_string()
)


print("\nTOP REGIONS")

print(
    episode[
        episode["ChargeCategory"] == "Usage"
    ]
    .groupby(
        "RegionName",
        dropna=False,
    )["EffectiveCost"]
    .sum()
    .sort_values(
        ascending=False,
    )
    .head(10)
    .to_string()
)