import pandas as pd
import numpy as np


INPUT_PATH = "data/real/aws_hourly_cost_components.csv"
OUTPUT_PATH = "data/real/aws_real_features_v2.csv"


SELECTED_SERVICES = [
    "Amazon Relational Database Service",
    "Amazon Elastic File System",
    "Amazon Simple Storage Service",
    "Amazon Elastic Container Service for Kubernetes",
]


def load_data():

    df = pd.read_csv(
        INPUT_PATH,
        parse_dates=["hour"],
    )

    df = df[
        df["ServiceName"].isin(SELECTED_SERVICES)
    ].copy()

    return df


def build_features(df):

    all_features = []

    start_hour = df["hour"].min()
    end_hour = df["hour"].max()

    complete_hours = pd.date_range(
        start=start_hour,
        end=end_hour,
        freq="h",
    )

    for service in SELECTED_SERVICES:

        service_df = (
            df[df["ServiceName"] == service]
            .set_index("hour")
            .sort_index()
        )

        service_df = service_df.reindex(
            complete_hours
        )

        service_df.index.name = "hour"

        # Was this service-hour present in original data?
        service_df["had_billing_record"] = (
            service_df["usage_effective_cost"].notna()
        )

        cost_columns = [
            "usage_effective_cost",
            "credit_effective_cost",
            "other_effective_cost",
            "total_effective_cost",
            "billed_cost",
        ]

        service_df[cost_columns] = (
            service_df[cost_columns]
            .fillna(0.0)
        )

        service_df["ServiceName"] = service

        # ==================================================
        # CURRENT 24-HOUR COSTS
        # ==================================================

        service_df["usage_cost_24h"] = (
            service_df["usage_effective_cost"]
            .rolling(24, min_periods=24)
            .sum()
        )

        service_df["credit_cost_24h"] = (
            service_df["credit_effective_cost"]
            .rolling(24, min_periods=24)
            .sum()
        )

        service_df["other_cost_24h"] = (
            service_df["other_effective_cost"]
            .rolling(24, min_periods=24)
            .sum()
        )

        service_df["net_cost_24h"] = (
            service_df["total_effective_cost"]
            .rolling(24, min_periods=24)
            .sum()
        )

        # ==================================================
        # 7-DAY HISTORICAL USAGE-COST BASELINE
        # ==================================================

        previous_usage_cost = (
            service_df["usage_effective_cost"]
            .shift(24)
        )

        previous_7d_usage_cost = (
            previous_usage_cost
            .rolling(
                168,
                min_periods=168,
            )
            .sum()
        )

        service_df["baseline_usage_cost_7d"] = (
            previous_7d_usage_cost / 7
        )

        # ==================================================
        # USAGE COST CHANGE
        # ==================================================

        service_df["usage_cost_change_pct"] = (
            (
                service_df["usage_cost_24h"]
                - service_df["baseline_usage_cost_7d"]
            )
            / service_df["baseline_usage_cost_7d"]
            * 100
        )

        service_df["usage_cost_change_pct"] = (
            service_df["usage_cost_change_pct"]
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
        )

        # ==================================================
        # CREDIT OFFSET
        # ==================================================

        service_df["credit_offset_ratio"] = np.where(
            service_df["usage_cost_24h"] > 0,
            -service_df["credit_cost_24h"]
            / service_df["usage_cost_24h"],
            np.nan,
        )

        all_features.append(
            service_df.reset_index()
        )

    return pd.concat(
        all_features,
        ignore_index=True,
    )


if __name__ == "__main__":

    print("Loading hourly cost components...")

    df = load_data()

    print("Input observations:", len(df))

    print("\nBuilding V2 real-data features...")

    features = build_features(df)

    features.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\nSaved:", OUTPUT_PATH)

    valid = features[
        features["baseline_usage_cost_7d"].notna()
    ]

    print("\n----------------------------")
    print("REAL FEATURES V2")
    print("----------------------------")

    print("Shape:", features.shape)

    print(
        "Valid baseline observations:",
        len(valid)
    )

    print("\nUsage cost change statistics:")

    print(
        valid["usage_cost_change_pct"]
        .describe()
    )

    print("\nCredit offset statistics:")

    print(
        valid["credit_offset_ratio"]
        .describe()
    )