import pandas as pd
import numpy as np


INPUT_PATH = "data/real/aws_real_evidence_features.csv"

OUTPUT_PATH = "data/real/aws_real_percentile_features.csv"


METRICS = [
    "usage_cost_change_pct",
    "new_account_share_pct",
    "largest_increase_share_pct",
]


HISTORY_WINDOW = 168  # previous 7 days of hourly observations


def historical_percentile(values, window=168):
    """
    Calculate percentile using ONLY previous observations.

    Current observation is never included in its own
    historical distribution.
    """

    result = np.full(len(values), np.nan)

    values = np.asarray(values, dtype=float)

    for i in range(window, len(values)):

        history = values[i - window:i]

        current = values[i]

        history = history[
            ~np.isnan(history)
        ]

        if len(history) == 0 or np.isnan(current):
            continue

        result[i] = (
            np.mean(history < current) * 100
        )

    return result


def build_percentiles(df):

    results = []

    for service, service_df in df.groupby(
        "ServiceName"
    ):

        service_df = (
            service_df
            .sort_values("hour")
            .copy()
        )

        for metric in METRICS:

            service_df[
                f"{metric}_percentile"
            ] = historical_percentile(
                service_df[metric].values,
                window=HISTORY_WINDOW,
            )

        results.append(service_df)

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
        "Building leak-free historical percentiles..."
    )

    result = build_percentiles(df)

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    percentile_columns = [
        f"{metric}_percentile"
        for metric in METRICS
    ]

    valid = result.dropna(
        subset=percentile_columns
    )

    print("\n----------------------------")
    print("REAL HISTORICAL PERCENTILES")
    print("----------------------------")

    print(
        "Total observations:",
        len(result)
    )

    print(
        "Observations with historical percentile:",
        len(valid)
    )

    print("\nValid observations by service:")

    print(
        valid.groupby("ServiceName").size()
    )

    print("\nPercentile distributions:")

    print(
        valid[percentile_columns]
        .describe()
        .to_string()
    )


    print("\n----------------------------")
    print("S3 SPIKE PERCENTILES")
    print("----------------------------")

    spike = result[
        (result["ServiceName"]
         == "Amazon Simple Storage Service")
        &
        (result["hour"]
         == "2024-09-18 22:00:00")
    ]

    columns = [
        "hour",
        "usage_cost_change_pct",
        "usage_cost_change_pct_percentile",
        "new_account_share_pct",
        "new_account_share_pct_percentile",
        "largest_increase_share_pct",
        "largest_increase_share_pct_percentile",
    ]

    print(
        spike[columns].to_string(index=False)
    )