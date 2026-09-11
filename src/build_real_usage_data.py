import pandas as pd


INPUT_PATH = "data/real/focus_data_table.csv.gz"

OUTPUT_PATH = "data/real/aws_hourly_usage_by_unit.csv"


SELECTED_SERVICES = [
    "Amazon Relational Database Service",
    "Amazon Elastic File System",
    "Amazon Simple Storage Service",
    "Amazon Elastic Container Service for Kubernetes",
]


RELEVANT_UNITS = {
    "Amazon Elastic Container Service for Kubernetes": [
        "Hours",
    ],

    "Amazon Elastic File System": [
        "GB",
        "GB-Months",
    ],

    "Amazon Relational Database Service": [
        "Hours",
        "GB-Months",
        "IOs",
    ],

    "Amazon Simple Storage Service": [
        "GB",
        "GB-Months",
    ],
}


def load_data():

    columns = [
        "ChargePeriodStart",
        "ProviderName",
        "ServiceName",
        "ChargeCategory",
        "ConsumedQuantity",
        "ConsumedUnit",
        "EffectiveCost",
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

    return df


def keep_relevant_units(df):

    mask = pd.Series(
        False,
        index=df.index,
    )

    for service, units in RELEVANT_UNITS.items():

        mask = mask | (
            (df["ServiceName"] == service)
            & (df["ConsumedUnit"].isin(units))
        )

    return df[mask].copy()


def build_hourly_usage(df):

    hourly = (
        df.groupby(
            [
                "hour",
                "ServiceName",
                "ConsumedUnit",
            ],
            as_index=False,
        )
        .agg(
            consumed_quantity=(
                "ConsumedQuantity",
                "sum",
            ),
            effective_cost=(
                "EffectiveCost",
                "sum",
            ),
            billing_rows=(
                "EffectiveCost",
                "size",
            ),
        )
    )

    return hourly


if __name__ == "__main__":

    print("Loading real usage data...")

    df = load_data()

    df = keep_relevant_units(df)

    print(
        "Relevant usage rows:",
        len(df)
    )

    hourly = build_hourly_usage(df)

    hourly.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("REAL HOURLY USAGE DATA")
    print("----------------------------")

    print("Shape:", hourly.shape)

    print("\nObservations by service/unit:")

    print(
        hourly.groupby(
            [
                "ServiceName",
                "ConsumedUnit",
            ]
        )
        .size()
        .to_string()
    )

    print("\nTotal quantity and cost:")

    print(
        hourly.groupby(
            [
                "ServiceName",
                "ConsumedUnit",
            ]
        )
        .agg(
            total_quantity=(
                "consumed_quantity",
                "sum",
            ),
            total_cost=(
                "effective_cost",
                "sum",
            ),
        )
        .to_string()
    )