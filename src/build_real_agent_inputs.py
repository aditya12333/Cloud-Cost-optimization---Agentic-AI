import pandas as pd


# ==================================================
# PATHS
# ==================================================

COST_PERCENTILE_PATH = (
    "data/real/aws_real_percentile_features.csv"
)

PATTERN_PATH = (
    "data/real/aws_real_pattern_features.csv"
)

ALIGNMENT_PATH = (
    "data/real/aws_real_alignment_features.csv"
)

UNIT_PERCENTILE_PATH = (
    "data/real/aws_real_unit_percentiles.csv"
)

COST_FEATURE_PATH = (
    "data/real/aws_real_features_v2.csv"
)

DAILY_ALIGNMENT_PATH = (
    "data/real/aws_real_daily_alignment.csv"
)

OUTPUT_PATH = (
    "data/real/aws_real_agent_inputs.csv"
)


# ==================================================
# PRIMARY HOURLY USAGE DIMENSION
# ==================================================

PRIMARY_UNITS = {

    "Amazon Elastic Container Service for Kubernetes":
        "Hours",

    "Amazon Elastic File System":
        "GB",

    "Amazon Relational Database Service":
        "Hours",

    "Amazon Simple Storage Service":
        "GB",
}


# ==================================================
# LOAD COST / EVIDENCE PERCENTILES
# ==================================================

def load_cost_evidence():

    df = pd.read_csv(
        COST_PERCENTILE_PATH,
        parse_dates=["hour"],
    )

    df = df.rename(
        columns={
            "usage_cost_change_pct_percentile":
                "cost_percentile",

            "new_account_share_pct_percentile":
                "new_account_percentile",

            "largest_increase_share_pct_percentile":
                "largest_increase_percentile",
        }
    )

    return df


# ==================================================
# LOAD HISTORICAL PATTERN
# ==================================================

def load_pattern():

    df = pd.read_csv(
        PATTERN_PATH,
        parse_dates=["hour"],
    )

    return df[
        [
            "hour",
            "ServiceName",
            "pattern_deviation_pct",
            "matches_historical_pattern",
        ]
    ]


# ==================================================
# LOAD PRIMARY USAGE SIGNAL
# ==================================================

def load_primary_usage():

    df = pd.read_csv(
        ALIGNMENT_PATH,
        parse_dates=["hour"],
    )

    return df[
        [
            "hour",
            "ServiceName",
            "primary_usage_unit",
            "current_usage",
            "baseline_usage",
            "usage_change_pct",
            "cost_usage_gap_pct",
        ]
    ].rename(
        columns={
            "usage_change_pct":
                "primary_usage_change_pct",

            "cost_usage_gap_pct":
                "service_cost_usage_gap_pct",
        }
    )


# ==================================================
# LOAD PRIMARY UNIT-COST PERCENTILE
# ==================================================

def load_primary_unit_cost():

    df = pd.read_csv(
        UNIT_PERCENTILE_PATH,
        parse_dates=["hour"],
    )

    df = df[
        df["cadence"] == "hourly"
    ].copy()

    selected = []

    for service, unit in PRIMARY_UNITS.items():

        subset = df[
            (df["ServiceName"] == service)
            & (df["ConsumedUnit"] == unit)
        ].copy()

        selected.append(subset)

    result = pd.concat(
        selected,
        ignore_index=True,
    )

    return result[
        [
            "hour",
            "ServiceName",
            "ConsumedUnit",
            "unit_cost_change_pct",
            "unit_cost_percentile",
        ]
    ].rename(
        columns={
            "ConsumedUnit":
                "primary_unit",

            "unit_cost_change_pct":
                "primary_unit_cost_change_pct",

            "unit_cost_percentile":
                "primary_unit_cost_percentile",
        }
    )


# ==================================================
# LOAD CREDIT / NET COST EVIDENCE
# ==================================================

def load_cost_components():

    df = pd.read_csv(
        COST_FEATURE_PATH,
        parse_dates=["hour"],
    )

    return df[
        [
            "hour",
            "ServiceName",
            "usage_cost_24h",
            "baseline_usage_cost_7d",
            "credit_cost_24h",
            "credit_offset_ratio",
            "net_cost_24h",
        ]
    ]


# ==================================================
# LOAD DAILY S3 STORAGE EVIDENCE
# ==================================================

def load_s3_storage_evidence():

    daily = pd.read_csv(
        DAILY_ALIGNMENT_PATH,
        parse_dates=["hour"],
    )

    daily = daily[
        (
            daily["ServiceName"]
            == "Amazon Simple Storage Service"
        )
        & (
            daily["ConsumedUnit"]
            == "GB-Months"
        )
    ].copy()

    daily_percentiles = pd.read_csv(
        UNIT_PERCENTILE_PATH,
        parse_dates=["hour"],
    )

    daily_percentiles = daily_percentiles[
        (
            daily_percentiles["ServiceName"]
            == "Amazon Simple Storage Service"
        )
        & (
            daily_percentiles["ConsumedUnit"]
            == "GB-Months"
        )
        & (
            daily_percentiles["cadence"]
            == "daily"
        )
    ].copy()

    daily = daily.merge(
        daily_percentiles[
            [
                "hour",
                "ServiceName",
                "unit_cost_percentile",
            ]
        ],
        on=[
            "hour",
            "ServiceName",
        ],
        how="left",
    )

    daily["day"] = (
        daily["hour"]
        .dt.floor("D")
    )

    return daily[
        [
            "day",
            "ServiceName",
            "usage_change_pct",
            "cost_change_pct",
            "cost_usage_gap_pct",
            "unit_cost_change_pct",
            "unit_cost_percentile",
        ]
    ].rename(
        columns={
            "usage_change_pct":
                "storage_usage_change_pct",

            "cost_change_pct":
                "storage_cost_change_pct",

            "cost_usage_gap_pct":
                "storage_cost_usage_gap_pct",

            "unit_cost_change_pct":
                "storage_unit_cost_change_pct",

            "unit_cost_percentile":
                "storage_unit_cost_percentile",
        }
    )


# ==================================================
# BUILD AGENT INPUT TABLE
# ==================================================

def build_agent_inputs():

    print(
        "Loading real FinOps evidence..."
    )

    base = load_cost_evidence()

    pattern = load_pattern()

    usage = load_primary_usage()

    unit_cost = load_primary_unit_cost()

    cost_components = load_cost_components()

    storage = load_s3_storage_evidence()


    # ----------------------------------------------
    # MERGE HOURLY SIGNALS
    # ----------------------------------------------

    agent = base.merge(
        pattern,
        on=[
            "hour",
            "ServiceName",
        ],
        how="left",
    )

    agent = agent.merge(
        usage,
        on=[
            "hour",
            "ServiceName",
        ],
        how="left",
    )

    agent = agent.merge(
        unit_cost,
        on=[
            "hour",
            "ServiceName",
        ],
        how="left",
    )

    agent = agent.merge(
        cost_components,
        on=[
            "hour",
            "ServiceName",
        ],
        how="left",
    )


    # ----------------------------------------------
    # ADD DAILY S3 STORAGE SIGNAL
    # ----------------------------------------------

    agent["day"] = (
        agent["hour"]
        .dt.floor("D")
    )

    agent = agent.merge(
        storage,
        on=[
            "day",
            "ServiceName",
        ],
        how="left",
    )


    # ----------------------------------------------
    # AGENT-READY FLAG
    # ----------------------------------------------

    required = [
        "cost_percentile",
        "new_account_percentile",
        "primary_usage_change_pct",
        "primary_unit_cost_percentile",
        "pattern_deviation_pct",
    ]

    agent["agent_ready"] = (
        agent[required]
        .notna()
        .all(axis=1)
    )

    return agent


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    agent = build_agent_inputs()

    agent.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("REAL AGENT INPUT DATA")
    print("----------------------------")

    print(
        "Shape:",
        agent.shape
    )

    print(
        "Agent-ready observations:",
        agent["agent_ready"].sum()
    )

    print("\nAgent-ready by service:")

    print(
        agent[
            agent["agent_ready"]
        ]
        .groupby(
            "ServiceName"
        )
        .size()
        .to_string()
    )


    # ==================================================
    # CHECK S3 EVENT
    # ==================================================

    print("\n----------------------------")
    print("S3 REAL AGENT INPUT")
    print("----------------------------")

    event = agent[
        (
            agent["ServiceName"]
            == "Amazon Simple Storage Service"
        )
        &
        (
            agent["hour"]
            == pd.Timestamp(
                "2024-09-18 22:00:00"
            )
        )
    ]

    columns = [
        "hour",

        "usage_cost_change_pct",
        "cost_percentile",

        "primary_usage_unit",
        "primary_usage_change_pct",

        "primary_unit_cost_percentile",

        "new_account_share_pct",
        "new_account_percentile",

        "pattern_deviation_pct",
        "matches_historical_pattern",

        "credit_offset_ratio",

        "storage_usage_change_pct",
        "storage_cost_change_pct",
        "storage_cost_usage_gap_pct",
        "storage_unit_cost_percentile",

        "agent_ready",
    ]

    print(
        event[
            columns
        ].to_string(index=False)
    )