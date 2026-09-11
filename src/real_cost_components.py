import pandas as pd


INPUT_PATH = "data/real/focus_data_table.csv.gz"
OUTPUT_PATH = "data/real/aws_hourly_cost_components.csv"


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
        "ServiceCategory",
        "ChargeCategory",
        "ChargeFrequency",
        "EffectiveCost",
        "BilledCost",
    ]

    df = pd.read_csv(
        INPUT_PATH,
        usecols=columns,
        low_memory=False,
    )

    df = df[
        (df["ProviderName"] == "AWS")
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


def build_hourly_components(df):

    # Usage portion
    df["usage_effective_cost"] = (
        df["EffectiveCost"]
        .where(
            df["ChargeCategory"] == "Usage",
            0.0
        )
    )

    # Credit portion
    df["credit_effective_cost"] = (
        df["EffectiveCost"]
        .where(
            df["ChargeCategory"] == "Credit",
            0.0
        )
    )

    # Everything that is neither Usage nor Credit
    df["other_effective_cost"] = (
        df["EffectiveCost"]
        .where(
            ~df["ChargeCategory"].isin(
                ["Usage", "Credit"]
            ),
            0.0
        )
    )

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
            usage_effective_cost=(
                "usage_effective_cost",
                "sum"
            ),
            credit_effective_cost=(
                "credit_effective_cost",
                "sum"
            ),
            other_effective_cost=(
                "other_effective_cost",
                "sum"
            ),
            total_effective_cost=(
                "EffectiveCost",
                "sum"
            ),
            billed_cost=(
                "BilledCost",
                "sum"
            ),
        )
    )

    return hourly


if __name__ == "__main__":

    print("Loading selected AWS services...")

    df = load_data()

    print("Raw rows:", len(df))

    print("\nBuilding hourly cost components...")

    hourly = build_hourly_components(df)

    hourly.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\nSaved:", OUTPUT_PATH)

    print("\n----------------------------")
    print("COST COMPONENT SUMMARY")
    print("----------------------------")

    summary = (
        hourly.groupby("ServiceName")
        [
            [
                "usage_effective_cost",
                "credit_effective_cost",
                "other_effective_cost",
                "total_effective_cost",
                "billed_cost",
            ]
        ]
        .sum()
    )

    print(
    summary.to_string()
    )

    print("\n----------------------------")
    print("RECONCILIATION CHECK")
    print("----------------------------")

    summary["reconstructed_total"] = (
        summary["usage_effective_cost"]
        + summary["credit_effective_cost"]
        + summary["other_effective_cost"]
    )

    summary["difference"] = (
        summary["reconstructed_total"]
        - summary["total_effective_cost"]
    )

    print(
        summary[
            [
                "total_effective_cost",
                "reconstructed_total",
                "difference",
            ]
        ].to_string()
    )