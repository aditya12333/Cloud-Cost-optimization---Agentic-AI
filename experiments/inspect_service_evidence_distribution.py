import pandas as pd


DATA_PATH = "data/real/aws_real_evidence_features.csv"


df = pd.read_csv(
    DATA_PATH,
    parse_dates=["hour"],
)


metrics = [
    "usage_cost_change_pct",
    "top_account_share_pct",
    "new_account_share_pct",
    "largest_increase_share_pct",
]


for service, service_df in df.groupby("ServiceName"):

    print("\n================================")
    print(service)
    print("================================")

    print(
        service_df[metrics]
        .describe(
            percentiles=[
                0.50,
                0.75,
                0.90,
                0.95,
                0.99,
            ]
        )
        .to_string()
    )