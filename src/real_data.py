import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"

OUTPUT_PATH = "data/real/aws_hourly_service_cost.csv"


def load_aws_data():
    """
    Load only the columns required for the first
    real-data experiment.
    """

    columns = [
        "ChargePeriodStart",
        "ProviderName",
        "ServiceName",
        "ServiceCategory",
        "EffectiveCost",
    ]

    df = pd.read_csv(
        DATA_PATH,
        usecols=columns,
        low_memory=False,
    )

    # Keep AWS only
    df = df[df["ProviderName"] == "AWS"].copy()

    # Convert timestamp
    df["ChargePeriodStart"] = pd.to_datetime(
        df["ChargePeriodStart"]
    )

    return df


def build_hourly_service_cost(df):
    """
    Aggregate billing line items into hourly
    cost observations for each AWS service.
    """

    df["hour"] = df["ChargePeriodStart"].dt.floor("h")

    hourly = (
        df.groupby(
            [
                "hour",
                "ServiceName",
                "ServiceCategory",
            ],
            as_index=False,
        )
        .agg(
            effective_cost=("EffectiveCost", "sum"),
            billing_rows=("EffectiveCost", "size"),
        )
    )

    return hourly


if __name__ == "__main__":

    print("Loading AWS billing data...")

    aws_df = load_aws_data()

    print("AWS billing rows:", len(aws_df))

    print("\nBuilding hourly service-level dataset...")

    hourly_df = build_hourly_service_cost(aws_df)

    hourly_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\nSaved:", OUTPUT_PATH)

    print("\nHOURLY DATA SHAPE")
    print(hourly_df.shape)

    print("\nTIME COVERAGE")
    print("Start:", hourly_df["hour"].min())
    print("End:", hourly_df["hour"].max())

    print("\nUNIQUE SERVICES")
    print(hourly_df["ServiceName"].nunique())

    print("\nTOP 10 SERVICES BY TOTAL COST")

    print(
        hourly_df.groupby("ServiceName")["effective_cost"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )