import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"


SERVICE = "Amazon Elastic File System"

START = pd.Timestamp(
    "2024-09-21 07:00:00"
)

END = pd.Timestamp(
    "2024-09-22 12:00:00"
)

BASELINE_START = (
    START - pd.Timedelta(days=7)
)

BASELINE_END = START


columns = [
    "ChargePeriodStart",
    "ProviderName",
    "ServiceName",
    "ChargeCategory",
    "ChargeDescription",
    "EffectiveCost",
    "BilledCost",
    "ListCost",
    "ConsumedQuantity",
    "ConsumedUnit",
    "ListUnitPrice",
    "ContractedUnitPrice",
    "SubAccountName",
]


print("Loading EFS billing data...")


df = pd.read_csv(
    DATA_PATH,
    usecols=columns,
    low_memory=False,
)


df["ChargePeriodStart"] = pd.to_datetime(
    df["ChargePeriodStart"]
)


efs = df[
    (df["ProviderName"] == "AWS")
    & (df["ServiceName"] == SERVICE)
    & (df["ChargeCategory"] == "Usage")
].copy()


# ==================================================
# EPISODE
# ==================================================

episode = efs[
    (efs["ChargePeriodStart"] >= START)
    & (efs["ChargePeriodStart"] < END)
].copy()


# ==================================================
# BASELINE
# ==================================================

baseline = efs[
    (efs["ChargePeriodStart"] >= BASELINE_START)
    & (efs["ChargePeriodStart"] < BASELINE_END)
].copy()


# Episode is 29 hours.
episode_hours = (
    END - START
) / pd.Timedelta(hours=1)

scale_factor = (
    episode_hours / (7 * 24)
)


# ==================================================
# GROUP BY EXACT DRIVER
# ==================================================

keys = [
    "ChargeDescription",
    "ConsumedUnit",
    "SubAccountName",
]


episode_driver = (
    episode.groupby(
        keys,
        dropna=False,
    )
    .agg(
        episode_effective_cost=(
            "EffectiveCost",
            "sum",
        ),
        episode_billed_cost=(
            "BilledCost",
            "sum",
        ),
        episode_quantity=(
            "ConsumedQuantity",
            "sum",
        ),
        mean_list_unit_price=(
            "ListUnitPrice",
            "mean",
        ),
        mean_contracted_unit_price=(
            "ContractedUnitPrice",
            "mean",
        ),
    )
)


baseline_driver = (
    baseline.groupby(
        keys,
        dropna=False,
    )
    .agg(
        baseline_effective_cost=(
            "EffectiveCost",
            "sum",
        ),
        baseline_billed_cost=(
            "BilledCost",
            "sum",
        ),
        baseline_quantity=(
            "ConsumedQuantity",
            "sum",
        ),
    )
)


# Convert previous 7 days into expected spend
# for a 29-hour episode.
baseline_driver[
    "expected_effective_cost"
] = (
    baseline_driver[
        "baseline_effective_cost"
    ]
    * scale_factor
)

baseline_driver[
    "expected_billed_cost"
] = (
    baseline_driver[
        "baseline_billed_cost"
    ]
    * scale_factor
)

baseline_driver[
    "expected_quantity"
] = (
    baseline_driver[
        "baseline_quantity"
    ]
    * scale_factor
)


comparison = episode_driver.join(
    baseline_driver[
        [
            "expected_effective_cost",
            "expected_billed_cost",
            "expected_quantity",
        ]
    ],
    how="outer",
).fillna(0.0)


comparison[
    "effective_cost_change"
] = (
    comparison["episode_effective_cost"]
    - comparison["expected_effective_cost"]
)


# ==================================================
# IMPLIED UNIT COSTS
# ==================================================

comparison[
    "episode_effective_unit_cost"
] = (
    comparison["episode_effective_cost"]
    / comparison["episode_quantity"]
)

comparison[
    "expected_effective_unit_cost"
] = (
    comparison["expected_effective_cost"]
    / comparison["expected_quantity"]
)


comparison[
    "episode_billed_unit_cost"
] = (
    comparison["episode_billed_cost"]
    / comparison["episode_quantity"]
)

comparison[
    "expected_billed_unit_cost"
] = (
    comparison["expected_billed_cost"]
    / comparison["expected_quantity"]
)


comparison = comparison.replace(
    [float("inf"), -float("inf")],
    pd.NA,
)


comparison = comparison.sort_values(
    "effective_cost_change",
    ascending=False,
)


print("\n----------------------------")
print("EFS ESCALATION DRIVER CHECK")
print("----------------------------")


columns_to_show = [
    "episode_effective_cost",
    "expected_effective_cost",
    "episode_billed_cost",
    "expected_billed_cost",
    "episode_quantity",
    "expected_quantity",
    "episode_effective_unit_cost",
    "expected_effective_unit_cost",
    "episode_billed_unit_cost",
    "expected_billed_unit_cost",
    "mean_list_unit_price",
    "mean_contracted_unit_price",
]


print(
    comparison[
        columns_to_show
    ]
    .head(10)
    .to_string()
)