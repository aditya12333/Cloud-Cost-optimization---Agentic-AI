import pandas as pd

from real_evidence import (
    load_evidence_data,
    check_service_breakdown,
)


FEATURE_PATH = "data/real/aws_real_features_v2.csv"

OUTPUT_PATH = "data/real/aws_real_evidence_features.csv"


def build_evidence_features():

    feature_df = pd.read_csv(
        FEATURE_PATH,
        parse_dates=["hour"],
    )

    # Only observations where a 7-day baseline exists
    feature_df = feature_df[
        feature_df["baseline_usage_cost_7d"].notna()
    ].copy()

    evidence_data = load_evidence_data()

    results = []

    total = len(feature_df)

    for i, row in enumerate(
        feature_df.itertuples(index=False),
        start=1,
    ):

        evidence, _ = check_service_breakdown(
            evidence_data,
            service_name=row.ServiceName,
            current_hour=row.hour,
        )

        current_cost = evidence[
            "current_usage_cost"
        ]

        largest_increase = evidence[
            "largest_account_increase"
        ]

        if current_cost > 0:

            largest_increase_share_pct = (
                max(largest_increase, 0)
                / current_cost
                * 100
            )

        else:

            largest_increase_share_pct = 0.0

        results.append(
            {
                "hour": row.hour,
                "ServiceName": row.ServiceName,

                "usage_cost_change_pct":
                    row.usage_cost_change_pct,

                "current_usage_cost":
                    current_cost,

                "top_account_share_pct":
                    evidence[
                        "top_account_share_pct"
                    ],

                "top_3_account_share_pct":
                    evidence[
                        "top_3_account_share_pct"
                    ],

                "new_account_share_pct":
                    evidence[
                        "new_account_share_pct"
                    ],

                "largest_account_increase":
                    largest_increase,

                "largest_increase_share_pct":
                    largest_increase_share_pct,
            }
        )

        if i % 250 == 0:
            print(
                f"Processed {i}/{total}"
            )

    return pd.DataFrame(results)


if __name__ == "__main__":

    print(
        "Building real evidence features..."
    )

    df = build_evidence_features()

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("REAL EVIDENCE FEATURE DATA")
    print("----------------------------")

    print("Shape:", df.shape)

    metrics = [
        "top_account_share_pct",
        "top_3_account_share_pct",
        "new_account_share_pct",
        "largest_increase_share_pct",
    ]

    print("\nEvidence distributions:")

    print(
        df[metrics]
        .describe(
            percentiles=[
                0.50,
                0.75,
                0.90,
                0.95,
                0.99,
            ]
        )
        .to_string()
    )