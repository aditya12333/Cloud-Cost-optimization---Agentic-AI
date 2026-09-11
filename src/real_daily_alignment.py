import pandas as pd
import numpy as np


INPUT_PATH = "data/real/aws_hourly_usage_by_unit.csv"

OUTPUT_PATH = "data/real/aws_real_daily_alignment.csv"


SERVICE = "Amazon Simple Storage Service"
UNIT = "GB-Months"


def build_daily_alignment():

    df = pd.read_csv(
        INPUT_PATH,
        parse_dates=["hour"],
    )

    df = df[
        (df["ServiceName"] == SERVICE)
        & (df["ConsumedUnit"] == UNIT)
    ].copy()

    df = (
        df.sort_values("hour")
        .set_index("hour")
    )

    # Current day's usage and cost
    df["current_usage"] = df["consumed_quantity"]
    df["current_cost"] = df["effective_cost"]

    # Previous 7 days only
    df["baseline_usage_7d"] = (
        df["consumed_quantity"]
        .shift(1)
        .rolling(
            7,
            min_periods=7,
        )
        .mean()
    )

    df["baseline_cost_7d"] = (
        df["effective_cost"]
        .shift(1)
        .rolling(
            7,
            min_periods=7,
        )
        .mean()
    )

    # Usage change
    df["usage_change_pct"] = (
        (
            df["current_usage"]
            - df["baseline_usage_7d"]
        )
        / df["baseline_usage_7d"]
        * 100
    )

    # Cost change
    df["cost_change_pct"] = (
        (
            df["current_cost"]
            - df["baseline_cost_7d"]
        )
        / df["baseline_cost_7d"]
        * 100
    )

    # Cost growth minus usage growth
    df["cost_usage_gap_pct"] = (
        df["cost_change_pct"]
        - df["usage_change_pct"]
    )

    # Unit cost
    df["current_unit_cost"] = np.where(
        df["current_usage"] > 0,
        df["current_cost"]
        / df["current_usage"],
        np.nan,
    )

    df["baseline_unit_cost"] = np.where(
        df["baseline_usage_7d"] > 0,
        df["baseline_cost_7d"]
        / df["baseline_usage_7d"],
        np.nan,
    )

    df["unit_cost_change_pct"] = (
        (
            df["current_unit_cost"]
            - df["baseline_unit_cost"]
        )
        / df["baseline_unit_cost"]
        * 100
    )

    df = df.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    df["ServiceName"] = SERVICE
    df["ConsumedUnit"] = UNIT
    df["cadence"] = "daily"

    return df.reset_index()


if __name__ == "__main__":

    result = build_daily_alignment()

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    valid = result[
        result["cost_change_pct"].notna()
        & result["usage_change_pct"].notna()
    ].copy()

    valid["same_direction"] = (
        np.sign(valid["cost_change_pct"])
        ==
        np.sign(valid["usage_change_pct"])
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("S3 DAILY STORAGE ALIGNMENT")
    print("----------------------------")

    print(
        "Valid observations:",
        len(valid)
    )

    print(
        "Same-direction rate:",
        valid["same_direction"].mean()
    )

    print(
        "\nCost/usage gap statistics:"
    )

    print(
        valid["cost_usage_gap_pct"]
        .describe()
    )

    print(
        "\nUnit-cost change statistics:"
    )

    print(
        valid["unit_cost_change_pct"]
        .describe()
    )


    print("\n----------------------------")
    print("SEPTEMBER 18 STORAGE EVENT")
    print("----------------------------")

    event = valid[
        valid["hour"]
        == pd.Timestamp("2024-09-18")
    ]

    columns = [
        "hour",
        "current_cost",
        "baseline_cost_7d",
        "cost_change_pct",
        "current_usage",
        "baseline_usage_7d",
        "usage_change_pct",
        "cost_usage_gap_pct",
        "unit_cost_change_pct",
    ]

    print(
        event[columns]
        .to_string(index=False)
    )