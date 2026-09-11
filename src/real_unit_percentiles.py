import pandas as pd
import numpy as np


HOURLY_PATH = "data/real/aws_real_unit_alignment.csv"
DAILY_PATH = "data/real/aws_real_daily_alignment.csv"

OUTPUT_PATH = "data/real/aws_real_unit_percentiles.csv"


def historical_percentile(values, window):

    values = np.asarray(values, dtype=float)

    result = np.full(
        len(values),
        np.nan,
    )

    for i in range(window, len(values)):

        current = values[i]

        history = values[
            i - window:i
        ]

        history = history[
            ~np.isnan(history)
        ]

        if (
            len(history) == 0
            or np.isnan(current)
        ):
            continue

        result[i] = (
            np.mean(history < current)
            * 100
        )

    return result


def build_hourly_percentiles():

    df = pd.read_csv(
        HOURLY_PATH,
        parse_dates=["hour"],
    )

    results = []

    for (
        service,
        unit,
    ), group in df.groupby(
        ["ServiceName", "ConsumedUnit"]
    ):

        group = (
            group
            .sort_values("hour")
            .copy()
        )

        group[
            "unit_cost_percentile"
        ] = historical_percentile(
            group[
                "unit_cost_change_pct"
            ].values,
            window=168,
        )

        group["cadence"] = "hourly"

        results.append(group)

    return pd.concat(
        results,
        ignore_index=True,
    )


def build_daily_percentiles():

    df = pd.read_csv(
        DAILY_PATH,
        parse_dates=["hour"],
    )

    df = (
        df
        .sort_values("hour")
        .copy()
    )

    df[
        "unit_cost_percentile"
    ] = historical_percentile(
        df[
            "unit_cost_change_pct"
        ].values,
        window=7,
    )

    df["cadence"] = "daily"

    return df


if __name__ == "__main__":

    print(
        "Building unit-cost percentiles..."
    )

    hourly = build_hourly_percentiles()

    daily = build_daily_percentiles()

    # Keep the important columns only
    hourly_output = hourly[
        [
            "hour",
            "ServiceName",
            "ConsumedUnit",
            "unit_cost_change_pct",
            "unit_cost_percentile",
            "cadence",
        ]
    ]

    daily_output = daily[
        [
            "hour",
            "ServiceName",
            "ConsumedUnit",
            "unit_cost_change_pct",
            "unit_cost_percentile",
            "cadence",
        ]
    ]

    result = pd.concat(
        [
            hourly_output,
            daily_output,
        ],
        ignore_index=True,
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    valid = result[
        result["unit_cost_percentile"]
        .notna()
    ]

    print("\n----------------------------")
    print("UNIT COST PERCENTILES")
    print("----------------------------")

    print(
        "Valid observations:",
        len(valid)
    )

    print("\nBy service / unit:")

    print(
        valid.groupby(
            [
                "ServiceName",
                "ConsumedUnit",
                "cadence",
            ]
        )
        .size()
        .to_string()
    )

    print("\nPercentile statistics:")

    print(
        valid[
            "unit_cost_percentile"
        ]
        .describe()
    )