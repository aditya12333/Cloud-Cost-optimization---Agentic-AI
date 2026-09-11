import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"


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
    "RegionName",
    "ResourceId",
]


print("Loading S3 billing records...")

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
].copy()


def analyse_period(name, start, end):

    period = s3[
        (s3["ChargePeriodStart"] >= start)
        & (s3["ChargePeriodStart"] <= end)
    ].copy()

    print("\n================================")
    print(name)
    print("================================")

    print("Rows:", len(period))

    print("\nCOST COMPONENTS")

    print(
        period.groupby(
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

    print("\nTOP CHARGE DESCRIPTIONS")

    print(
        period.groupby(
            "ChargeDescription"
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
        .head(15)
    )

    print("\nCOST BY REGION")

    print(
        period.groupby(
            "RegionName",
            dropna=False
        )["EffectiveCost"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    print("\nCONSUMED UNITS")

    print(
        period.groupby(
            "ConsumedUnit",
            dropna=False
        )
        .agg(
            quantity=("ConsumedQuantity", "sum"),
            effective_cost=("EffectiveCost", "sum"),
        )
        .sort_values(
            "effective_cost",
            ascending=False
        )
    )


# 24-hour window responsible for the spike
analyse_period(
    "S3 SPIKE WINDOW",
    "2024-09-17 23:00:00",
    "2024-09-18 22:59:59",
)


# Previous 7 days used as historical context
analyse_period(
    "S3 BASELINE WINDOW",
    "2024-09-10 23:00:00",
    "2024-09-17 22:59:59",
)