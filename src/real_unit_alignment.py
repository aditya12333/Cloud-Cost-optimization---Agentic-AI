import pandas as pd
import numpy as np


INPUT_PATH = "data/real/aws_hourly_usage_by_unit.csv"

OUTPUT_PATH = "data/real/aws_real_unit_alignment.csv"


# S3 GB-Months is daily, so exclude it from
# this hourly calculation for now.
DAILY_SIGNALS = {
    (
        "Amazon Simple Storage Service",
        "GB-Months",
    )
}


def build_hourly_unit_alignment(df):

    hourly = df[
        ~df[
            ["ServiceName", "ConsumedUnit"]
        ]
        .apply(tuple, axis=1)
        .isin(DAILY_SIGNALS)
    ].copy()

    results = []

    start_hour = df["hour"].min()
    end_hour = df["hour"].max()

    complete_hours = pd.date_range(
        start=start_hour,
        end=end_hour,
        freq="h",
    )

    for (
        service,
        unit,
    ), group in hourly.groupby(
        ["ServiceName", "ConsumedUnit"]
    ):

        group = (
            group
            .set_index("hour")
            .sort_index()
        )

        group = group.reindex(
            complete_hours
        )

        group.index.name = "hour"

        group["had_usage_record"] = (
            group["consumed_quantity"].notna()
        )

        group["consumed_quantity"] = (
            group["consumed_quantity"]
            .fillna(0.0)
        )

        group["effective_cost"] = (
            group["effective_cost"]
            .fillna(0.0)
        )

        # ==================================================
        # CURRENT 24 HOURS
        # ==================================================

        group["current_usage_24h"] = (
            group["consumed_quantity"]
            .rolling(
                24,
                min_periods=24,
            )
            .sum()
        )

        group["current_cost_24h"] = (
            group["effective_cost"]
            .rolling(
                24,
                min_periods=24,
            )
            .sum()
        )

        # ==================================================
        # PREVIOUS 7-DAY BASELINE
        # ==================================================

        historical_usage = (
            group["consumed_quantity"]
            .shift(24)
        )

        historical_cost = (
            group["effective_cost"]
            .shift(24)
        )

        group["baseline_usage_7d"] = (
            historical_usage
            .rolling(
                168,
                min_periods=168,
            )
            .sum()
            / 7
        )

        group["baseline_cost_7d"] = (
            historical_cost
            .rolling(
                168,
                min_periods=168,
            )
            .sum()
            / 7
        )

        # ==================================================
        # CHANGE FEATURES
        # ==================================================

        group["usage_change_pct"] = (
            (
                group["current_usage_24h"]
                - group["baseline_usage_7d"]
            )
            / group["baseline_usage_7d"]
            * 100
        )

        group["cost_change_pct"] = (
            (
                group["current_cost_24h"]
                - group["baseline_cost_7d"]
            )
            / group["baseline_cost_7d"]
            * 100
        )

        # Cost growth minus usage growth
        group["cost_usage_gap_pct"] = (
            group["cost_change_pct"]
            - group["usage_change_pct"]
        )

        # ==================================================
        # UNIT COST
        # ==================================================

        group["current_unit_cost"] = np.where(
            group["current_usage_24h"] > 0,
            group["current_cost_24h"]
            / group["current_usage_24h"],
            np.nan,
        )

        group["baseline_unit_cost"] = np.where(
            group["baseline_usage_7d"] > 0,
            group["baseline_cost_7d"]
            / group["baseline_usage_7d"],
            np.nan,
        )

        group["unit_cost_change_pct"] = (
            (
                group["current_unit_cost"]
                - group["baseline_unit_cost"]
            )
            / group["baseline_unit_cost"]
            * 100
        )

        columns_to_clean = [
            "usage_change_pct",
            "cost_change_pct",
            "cost_usage_gap_pct",
            "unit_cost_change_pct",
        ]

        group[columns_to_clean] = (
            group[columns_to_clean]
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
        )

        group["ServiceName"] = service
        group["ConsumedUnit"] = unit

        results.append(
            group.reset_index()
        )

    return pd.concat(
        results,
        ignore_index=True,
    )


if __name__ == "__main__":

    df = pd.read_csv(
        INPUT_PATH,
        parse_dates=["hour"],
    )

    print(
        "Building unit-level cost/usage alignment..."
    )

    result = build_hourly_unit_alignment(df)

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    valid = result[
        result["cost_change_pct"].notna()
        & result["usage_change_pct"].notna()
    ].copy()

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("UNIT-LEVEL ALIGNMENT")
    print("----------------------------")

    print(
        "Valid observations:",
        len(valid)
    )

    print("\nSame-direction rate:")

    valid["same_direction"] = (
        np.sign(valid["cost_change_pct"])
        ==
        np.sign(valid["usage_change_pct"])
    )

    print(
        valid.groupby(
            [
                "ServiceName",
                "ConsumedUnit",
            ]
        )["same_direction"]
        .mean()
        .to_string()
    )

    print("\nMean cost/usage gap:")

    print(
        valid.groupby(
            [
                "ServiceName",
                "ConsumedUnit",
            ]
        )["cost_usage_gap_pct"]
        .mean()
        .to_string()
    )

    print("\nMean unit-cost change:")

    print(
        valid.groupby(
            [
                "ServiceName",
                "ConsumedUnit",
            ]
        )["unit_cost_change_pct"]
        .mean()
        .to_string()
    )