import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"

columns = [
    "ChargePeriodStart",
    "ProviderName",
    "ServiceName",
    "ChargeCategory",
    "ChargeDescription",
    "EffectiveCost",
    "SubAccountName",
    "ResourceId",
    "RegionName",
    "Tags",
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
    & (df["ServiceName"] == "Amazon Simple Storage Service")
    & (df["ChargeCategory"] == "Usage")
].copy()


def analyse(name, start, end):

    period = s3[
        (s3["ChargePeriodStart"] >= start)
        & (s3["ChargePeriodStart"] <= end)
    ].copy()

    print("\n================================")
    print(name)
    print("================================")

    print("\nTOP SUB-ACCOUNTS")

    print(
        period.groupby(
            "SubAccountName",
            dropna=False
        )["EffectiveCost"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )

    print("\nTOP RESOURCES")

    print(
        period.groupby(
            "ResourceId",
            dropna=False
        )["EffectiveCost"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )

    print("\nTOP REGIONS")

    print(
        period.groupby(
            "RegionName",
            dropna=False
        )["EffectiveCost"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )


analyse(
    "S3 SPIKE WINDOW",
    "2024-09-17 23:00:00",
    "2024-09-18 22:59:59",
)

analyse(
    "S3 BASELINE WINDOW",
    "2024-09-10 23:00:00",
    "2024-09-17 22:59:59",
)