import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"

columns = [
    "ChargePeriodStart",
    "ProviderName",
    "ServiceName",
    "ChargeCategory",
    "ChargeClass",
    "ChargeFrequency",
    "ChargeDescription",
    "EffectiveCost",
    "BilledCost",
    "ConsumedQuantity",
    "ConsumedUnit",
    "RegionName",
]

print("Loading RDS billing records...")

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
    & (
        df["ServiceName"]
        == "Amazon Relational Database Service"
    )
].copy()


def inspect_window(name, start, end):

    window = rds[
        (rds["ChargePeriodStart"] >= start)
        & (rds["ChargePeriodStart"] <= end)
    ].copy()

    print("\n================================")
    print(name)
    print("================================")

    print("Rows:", len(window))

    print("\nTOTAL COST")
    print(
        window[
            ["EffectiveCost", "BilledCost"]
        ].sum()
    )

    print("\nCOST BY CHARGE CATEGORY")

    print(
        window.groupby(
            "ChargeCategory",
            dropna=False
        )
        .agg(
            effective_cost=("EffectiveCost", "sum"),
            billed_cost=("BilledCost", "sum"),
            rows=("EffectiveCost", "size"),
        )
        .sort_values(
            "effective_cost",
            ascending=False
        )
    )

    print("\nCOST BY CHARGE FREQUENCY")

    print(
        window.groupby(
            "ChargeFrequency",
            dropna=False
        )["EffectiveCost"]
        .sum()
        .sort_values(ascending=False)
    )

    print("\nTOP CHARGE DESCRIPTIONS")

    print(
        window.groupby(
            "ChargeDescription"
        )["EffectiveCost"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )


# Large positive spike
inspect_window(
    "RDS POSITIVE SPIKE",
    "2024-09-15 00:00:00",
    "2024-09-16 23:59:59",
)


# Large negative period
inspect_window(
    "RDS NEGATIVE PERIOD",
    "2024-09-08 00:00:00",
    "2024-09-10 23:59:59",
)