import pandas as pd
import numpy as np


INPUT_PATH = "data/real/aws_real_features_v2.csv"

OUTPUT_PATH = "data/real/aws_real_pattern_features.csv"


def build_pattern_features():

    df = pd.read_csv(
        INPUT_PATH,
        parse_dates=["hour"],
    )

    df = df.sort_values(
        ["ServiceName", "hour"]
    ).copy()

    results = []

    for service, group in df.groupby("ServiceName"):

        group = group.copy()

        group["hour_of_day"] = (
            group["hour"].dt.hour
        )

        group["pattern_deviation_pct"] = np.nan

        # Compare each observation only with
        # previous observations from same hour of day.
        for idx, row in group.iterrows():

            history = group[
                (group["hour"] < row["hour"])
                & (
                    group["hour_of_day"]
                    == row["hour_of_day"]
                )
            ]

            # Require at least 5 previous matching hours.
            if len(history) < 5:
                continue

            historical_cost = (
                history["usage_cost_24h"]
                .tail(7)
                .median()
            )

            if historical_cost <= 0:
                continue

            group.loc[
                idx,
                "pattern_deviation_pct"
            ] = (
                (
                    row["usage_cost_24h"]
                    - historical_cost
                )
                / historical_cost
                * 100
            )

        # Smaller deviation means stronger
        # historical-pattern match.
        group["matches_historical_pattern"] = (
            group["pattern_deviation_pct"]
            .abs()
            <= 20
        )

        results.append(group)

    return pd.concat(
        results,
        ignore_index=True,
    )


if __name__ == "__main__":

    print(
        "Building historical-pattern evidence..."
    )

    df = build_pattern_features()

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    valid = df[
        df["pattern_deviation_pct"].notna()
    ]

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("REAL HISTORICAL PATTERN")
    print("----------------------------")

    print(
        "Valid observations:",
        len(valid)
    )

    print(
        "Pattern matches:",
        valid[
            "matches_historical_pattern"
        ].sum()
    )

    print(
        "Pattern match rate:",
        valid[
            "matches_historical_pattern"
        ].mean()
    )

    print("\nDeviation statistics:")

    print(
        valid["pattern_deviation_pct"]
        .describe()
    )

    print("\nS3 SEPTEMBER 18 EVENT:")

    event = df[
        (df["ServiceName"]
         == "Amazon Simple Storage Service")
        &
        (df["hour"]
         == "2024-09-18 22:00:00")
    ]

    print(
        event[
            [
                "hour",
                "usage_cost_24h",
                "pattern_deviation_pct",
                "matches_historical_pattern",
            ]
        ].to_string(index=False)
    )