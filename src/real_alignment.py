import pandas as pd
import numpy as np


COST_PATH = "data/real/aws_real_features_v2.csv"
USAGE_PATH = "data/real/aws_real_usage_features.csv"

OUTPUT_PATH = "data/real/aws_real_alignment_features.csv"


PRIMARY_USAGE = {
    "Amazon Elastic Container Service for Kubernetes": "Hours",
    "Amazon Relational Database Service": "Hours",
    "Amazon Elastic File System": "GB",
    "Amazon Simple Storage Service": "GB",
}


def build_alignment():

    cost = pd.read_csv(
        COST_PATH,
        parse_dates=["hour"],
    )

    usage = pd.read_csv(
        USAGE_PATH,
        parse_dates=["hour"],
    )

    results = []

    for service, primary_unit in PRIMARY_USAGE.items():

        service_cost = cost[
            cost["ServiceName"] == service
        ].copy()

        service_usage = usage[
            (usage["ServiceName"] == service)
            & (usage["ConsumedUnit"] == primary_unit)
            & (usage["cadence"] == "hourly")
        ][
            [
                "hour",
                "usage_change_pct",
                "current_usage",
                "baseline_usage",
            ]
        ].copy()

        merged = service_cost.merge(
            service_usage,
            on="hour",
            how="left",
        )

        merged["primary_usage_unit"] = primary_unit

        # Difference between cost growth and usage growth.
        merged["cost_usage_gap_pct"] = (
            merged["usage_cost_change_pct"]
            - merged["usage_change_pct"]
        )

        # Same-direction movement?
        merged["cost_usage_same_direction"] = (
            np.sign(
                merged["usage_cost_change_pct"]
            )
            ==
            np.sign(
                merged["usage_change_pct"]
            )
        )

        results.append(merged)

    return pd.concat(
        results,
        ignore_index=True,
    )


if __name__ == "__main__":

    print("Building cost/usage alignment features...")

    df = build_alignment()

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    valid = df[
        df["usage_cost_change_pct"].notna()
        & df["usage_change_pct"].notna()
    ]

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("COST / USAGE ALIGNMENT")
    print("----------------------------")

    print("Valid observations:", len(valid))

    print("\nBy service:")

    print(
        valid.groupby("ServiceName")[
            [
                "usage_cost_change_pct",
                "usage_change_pct",
                "cost_usage_gap_pct",
            ]
        ]
        .mean()
        .to_string()
    )

    print(
        "\nSame-direction rate:"
    )

    print(
        valid.groupby("ServiceName")[
            "cost_usage_same_direction"
        ]
        .mean()
        .to_string()
    )