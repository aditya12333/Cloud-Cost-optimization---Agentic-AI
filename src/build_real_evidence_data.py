import pandas as pd


INPUT_PATH = "data/real/focus_data_table.csv.gz"

OUTPUT_PATH = (
    "data/real/aws_hourly_subaccount_usage_cost.csv"
)


SELECTED_SERVICES = [
    "Amazon Relational Database Service",
    "Amazon Elastic File System",
    "Amazon Simple Storage Service",
    "Amazon Elastic Container Service for Kubernetes",
]


def load_data():

    columns = [
        "ChargePeriodStart",
        "ProviderName",
        "ServiceName",
        "ChargeCategory",
        "EffectiveCost",
        "SubAccountName",
    ]

    df = pd.read_csv(
        INPUT_PATH,
        usecols=columns,
        low_memory=False,
    )

    df = df[
        (df["ProviderName"] == "AWS")
        & (df["ChargeCategory"] == "Usage")
        & (df["ServiceName"].isin(SELECTED_SERVICES))
    ].copy()

    df["ChargePeriodStart"] = pd.to_datetime(
        df["ChargePeriodStart"]
    )

    df["hour"] = (
        df["ChargePeriodStart"]
        .dt.floor("h")
    )

    df["SubAccountName"] = (
        df["SubAccountName"]
        .fillna("UNKNOWN")
    )

    return df


def build_subaccount_table(df):

    hourly = (
        df.groupby(
            [
                "hour",
                "ServiceName",
                "SubAccountName",
            ],
            as_index=False,
        )
        .agg(
            usage_cost=(
                "EffectiveCost",
                "sum"
            ),
            billing_rows=(
                "EffectiveCost",
                "size"
            ),
        )
    )

    return hourly


if __name__ == "__main__":

    print("Loading billing data...")

    df = load_data()

    print(
        "Raw usage rows:",
        len(df)
    )

    print(
        "\nBuilding hourly sub-account evidence..."
    )

    evidence_df = build_subaccount_table(df)

    evidence_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("REAL EVIDENCE DATA")
    print("----------------------------")

    print(
        "Shape:",
        evidence_df.shape
    )

    print(
        "Unique sub-accounts:",
        evidence_df["SubAccountName"].nunique()
    )

    print("\nRows by service:")

    print(
        evidence_df
        .groupby("ServiceName")
        .size()
    )