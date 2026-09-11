import pandas as pd


INPUT_PATH = "data/real/focus_data_table.csv.gz"

OUTPUT_PATH = "data/real/aws_hourly_driver_usage.csv"


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
        "ChargeDescription",
        "EffectiveCost",
        "BilledCost",
        "ConsumedQuantity",
        "ConsumedUnit",
        "ListUnitPrice",
        "ContractedUnitPrice",
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


def build_driver_data(df):

    hourly = (
        df.groupby(
            [
                "hour",
                "ServiceName",
                "ChargeDescription",
                "ConsumedUnit",
                "SubAccountName",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            effective_cost=(
                "EffectiveCost",
                "sum",
            ),

            billed_cost=(
                "BilledCost",
                "sum",
            ),

            consumed_quantity=(
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

            billing_rows=(
                "EffectiveCost",
                "size",
            ),
        )
    )

    return hourly


if __name__ == "__main__":

    print(
        "Loading real billing driver data..."
    )

    df = load_data()

    print(
        "Raw usage rows:",
        len(df)
    )

    print(
        "\nBuilding richer driver-level evidence..."
    )

    driver_df = build_driver_data(df)

    driver_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("REAL DRIVER DATA V2")
    print("----------------------------")

    print(
        "Shape:",
        driver_df.shape
    )

    print(
        "Unique charge descriptions:",
        driver_df[
            "ChargeDescription"
        ].nunique()
    )

    print(
        "Unique sub-accounts:",
        driver_df[
            "SubAccountName"
        ].nunique()
    )

    print("\nColumns:")

    print(
        driver_df.columns.tolist()
    )