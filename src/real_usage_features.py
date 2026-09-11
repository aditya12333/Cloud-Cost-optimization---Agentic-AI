import pandas as pd
import numpy as np


INPUT_PATH = "data/real/aws_hourly_usage_by_unit.csv"

OUTPUT_PATH = "data/real/aws_real_usage_features.csv"


DAILY_SIGNALS = {
    (
        "Amazon Simple Storage Service",
        "GB-Months",
    )
}


def load_data():

    return pd.read_csv(
        INPUT_PATH,
        parse_dates=["hour"],
    )


def build_hourly_features(df):

    results = []

    hourly_df = df[
        ~df[
            ["ServiceName", "ConsumedUnit"]
        ]
        .apply(tuple, axis=1)
        .isin(DAILY_SIGNALS)
    ].copy()

    for (
        service,
        unit,
    ), group in hourly_df.groupby(
        ["ServiceName", "ConsumedUnit"]
    ):

        group = (
            group
            .set_index("hour")
            .sort_index()
        )

        complete_hours = pd.date_range(
            group.index.min(),
            group.index.max(),
            freq="h",
        )

        group = group.reindex(
            complete_hours
        )

        group.index.name = "hour"

        group["consumed_quantity"] = (
            group["consumed_quantity"]
            .fillna(0.0)
        )

        # Current 24h usage
        group["current_usage"] = (
            group["consumed_quantity"]
            .rolling(
                24,
                min_periods=24,
            )
            .sum()
        )

        # Previous 7 days,
        # excluding current 24h
        historical = (
            group["consumed_quantity"]
            .shift(24)
        )

        previous_7d = (
            historical
            .rolling(
                168,
                min_periods=168,
            )
            .sum()
        )

        group["baseline_usage"] = (
            previous_7d / 7
        )

        group["usage_change_pct"] = (
            (
                group["current_usage"]
                - group["baseline_usage"]
            )
            / group["baseline_usage"]
            * 100
        )

        group["usage_change_pct"] = (
            group["usage_change_pct"]
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
        )

        group["ServiceName"] = service
        group["ConsumedUnit"] = unit
        group["cadence"] = "hourly"

        results.append(
            group.reset_index()
        )

    return results


def build_daily_features(df):

    results = []

    for service, unit in DAILY_SIGNALS:

        group = df[
            (df["ServiceName"] == service)
            & (df["ConsumedUnit"] == unit)
        ].copy()

        group = (
            group
            .sort_values("hour")
            .set_index("hour")
        )

        # Current daily observation
        group["current_usage"] = (
            group["consumed_quantity"]
        )

        # Previous 7 daily observations
        group["baseline_usage"] = (
            group["consumed_quantity"]
            .shift(1)
            .rolling(
                7,
                min_periods=7,
            )
            .mean()
        )

        group["usage_change_pct"] = (
            (
                group["current_usage"]
                - group["baseline_usage"]
            )
            / group["baseline_usage"]
            * 100
        )

        group["usage_change_pct"] = (
            group["usage_change_pct"]
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
        )

        group["ServiceName"] = service
        group["ConsumedUnit"] = unit
        group["cadence"] = "daily"

        results.append(
            group.reset_index()
        )

    return results


if __name__ == "__main__":

    print("Loading usage data...")

    df = load_data()

    results = []

    results.extend(
        build_hourly_features(df)
    )

    results.extend(
        build_daily_features(df)
    )

    features = pd.concat(
        results,
        ignore_index=True,
    )

    features.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    valid = features[
        features["usage_change_pct"]
        .notna()
    ]

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("REAL USAGE FEATURES")
    print("----------------------------")

    print(
        "Shape:",
        features.shape
    )

    print(
        "\nValid observations:"
    )

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

    print(
        "\nUsage-change statistics:"
    )

    print(
        valid.groupby(
            [
                "ServiceName",
                "ConsumedUnit",
            ]
        )["usage_change_pct"]
        .describe()
        .to_string()
    )