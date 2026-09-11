import pandas as pd


DATA_PATH = "data/real/aws_hourly_subaccount_usage_cost.csv"


def load_evidence_data():

    return pd.read_csv(
        DATA_PATH,
        parse_dates=["hour"],
    )


def check_service_breakdown(
    df,
    service_name,
    current_hour,
):
    """
    Compare the current 24-hour service cost distribution
    across sub-accounts with the previous 7-day baseline.

    Returns structured evidence for the agent.
    """

    current_hour = pd.Timestamp(current_hour)

    # --------------------------------------------
    # CURRENT 24-HOUR WINDOW
    # --------------------------------------------

    current_start = (
        current_hour - pd.Timedelta(hours=23)
    )

    current = df[
        (df["ServiceName"] == service_name)
        & (df["hour"] >= current_start)
        & (df["hour"] <= current_hour)
    ].copy()

    # --------------------------------------------
    # PREVIOUS 7-DAY BASELINE
    # --------------------------------------------

    baseline_end = current_start

    baseline_start = (
        baseline_end - pd.Timedelta(days=7)
    )

    baseline = df[
        (df["ServiceName"] == service_name)
        & (df["hour"] >= baseline_start)
        & (df["hour"] < baseline_end)
    ].copy()

    # --------------------------------------------
    # COST BY SUB-ACCOUNT
    # --------------------------------------------

    current_accounts = (
        current.groupby("SubAccountName")["usage_cost"]
        .sum()
        .rename("current_cost_24h")
    )

    baseline_accounts = (
        baseline.groupby("SubAccountName")["usage_cost"]
        .sum()
        .div(7)
        .rename("baseline_daily_cost")
    )

    comparison = pd.concat(
        [
            current_accounts,
            baseline_accounts,
        ],
        axis=1,
    ).fillna(0.0)

    comparison["absolute_change"] = (
        comparison["current_cost_24h"]
        - comparison["baseline_daily_cost"]
    )

    total_current_cost = (
        comparison["current_cost_24h"].sum()
    )

    # --------------------------------------------
    # ACCOUNT SHARES
    # --------------------------------------------

    if total_current_cost > 0:

        comparison["current_share_pct"] = (
            comparison["current_cost_24h"]
            / total_current_cost
            * 100
        )

    else:

        comparison["current_share_pct"] = 0.0

    # --------------------------------------------
    # NEW CONTRIBUTORS
    # --------------------------------------------

    comparison["is_new_contributor"] = (
        (comparison["baseline_daily_cost"] == 0)
        & (comparison["current_cost_24h"] > 0)
    )

    new_account_cost = (
        comparison.loc[
            comparison["is_new_contributor"],
            "current_cost_24h",
        ]
        .sum()
    )

    if total_current_cost > 0:

        new_account_share_pct = (
            new_account_cost
            / total_current_cost
            * 100
        )

    else:

        new_account_share_pct = 0.0

    # --------------------------------------------
    # CONCENTRATION
    # --------------------------------------------

    comparison = comparison.sort_values(
        "current_cost_24h",
        ascending=False,
    )

    top_account_share_pct = (
        comparison["current_share_pct"].max()
        if not comparison.empty
        else 0.0
    )

    top_3_share_pct = (
        comparison["current_share_pct"]
        .head(3)
        .sum()
    )

    # --------------------------------------------
    # LARGEST INCREASE
    # --------------------------------------------

    largest_increase_account = (
        comparison["absolute_change"]
        .idxmax()
        if not comparison.empty
        else None
    )

    largest_increase = (
        comparison["absolute_change"].max()
        if not comparison.empty
        else 0.0
    )

    evidence = {
        "service_name": service_name,
        "current_hour": current_hour,

        "current_usage_cost": total_current_cost,

        "top_account_share_pct":
            top_account_share_pct,

        "top_3_account_share_pct":
            top_3_share_pct,

        "new_account_share_pct":
            new_account_share_pct,

        "largest_increase_account":
            largest_increase_account,

        "largest_account_increase":
            largest_increase,
    }

    return evidence, comparison


if __name__ == "__main__":

    df = load_evidence_data()

    evidence, comparison = (
        check_service_breakdown(
            df,
            service_name=(
                "Amazon Simple Storage Service"
            ),
            current_hour="2024-09-18 22:00:00",
        )
    )

    print("\n----------------------------")
    print("REAL SERVICE BREAKDOWN")
    print("----------------------------")

    for key, value in evidence.items():
        print(f"{key}: {value}")

    print("\nTOP SUB-ACCOUNTS")

    print(
        comparison.head(10).to_string()
    )