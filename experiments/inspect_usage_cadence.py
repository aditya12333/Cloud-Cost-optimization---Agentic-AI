import pandas as pd


DATA_PATH = "data/real/aws_hourly_usage_by_unit.csv"


df = pd.read_csv(
    DATA_PATH,
    parse_dates=["hour"],
)


print("\n----------------------------")
print("USAGE CADENCE")
print("----------------------------")

summary = (
    df.groupby(
        ["ServiceName", "ConsumedUnit"]
    )
    .agg(
        observations=("hour", "size"),
        unique_days=("hour", lambda x: x.dt.date.nunique()),
        first_observation=("hour", "min"),
        last_observation=("hour", "max"),
    )
)

print(summary.to_string())


print("\n----------------------------")
print("S3 GB-MONTHS TIMESTAMPS")
print("----------------------------")

s3_storage = df[
    (df["ServiceName"] == "Amazon Simple Storage Service")
    & (df["ConsumedUnit"] == "GB-Months")
]

print(
    s3_storage[
        [
            "hour",
            "consumed_quantity",
            "effective_cost",
        ]
    ].to_string(index=False)
)