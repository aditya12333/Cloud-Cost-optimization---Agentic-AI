import pandas as pd


PATH = "results/real_episode_human_review.csv"


df = pd.read_csv(
    PATH,
    parse_dates=[
        "start_hour",
        "end_hour",
        "representative_hour",
    ],
)


# ==================================================
# MAP AGENT FEEDBACK TO HUMAN-LEVEL CATEGORY
# ==================================================

def map_feedback_to_label(feedback):

    if pd.isna(feedback):
        return "NO_AGENT_LABEL"

    feedback = str(feedback)

    # Episodes can contain multiple feedback values.
    values = {
        x.strip()
        for x in feedback.split(",")
        if x.strip()
    }

    if (
        "EFFECTIVE_COST_ACCOUNTING_SHIFT"
        in values
    ):
        return "ACCOUNTING_OR_BILLING_EFFECT"

    if (
        "USAGE_ALIGNED_DRIVER_GROWTH"
        in values
    ):
        return "LEGITIMATE_GROWTH"

    if (
        "NEW_COST_DRIVER"
        in values
    ):
        return "UNRESOLVED"

    if (
        "UNEXPLAINED_DRIVER_COST_INCREASE"
        in values
    ):
        return "SUSPICIOUS_COST_BEHAVIOR"

    if (
        "UNIT_COST_INCREASE"
        in values
    ):
        return "SUSPICIOUS_COST_BEHAVIOR"

    return "UNRESOLVED"


df["agent_review_label"] = (
    df["feedback_summary"]
    .apply(
        map_feedback_to_label
    )
)


# ==================================================
# AGREEMENT
# ==================================================

df["agreement"] = (
    df["agent_review_label"]
    ==
    df["human_label"]
)


total = len(df)

correct = (
    df["agreement"]
    .sum()
)

agreement_rate = (
    correct / total
)


print("\n----------------------------")
print("HUMAN-REVIEW EVALUATION")
print("----------------------------")

print(
    "Total episodes:",
    total
)

print(
    "Agreements:",
    correct
)

print(
    "Disagreements:",
    total - correct
)

print(
    "Agreement rate:",
    agreement_rate
)


# ==================================================
# HUMAN LABEL DISTRIBUTION
# ==================================================

print("\n----------------------------")
print("HUMAN LABEL DISTRIBUTION")
print("----------------------------")

print(
    df["human_label"]
    .value_counts()
    .to_string()
)


# ==================================================
# AGENT LABEL DISTRIBUTION
# ==================================================

print("\n----------------------------")
print("AGENT LABEL DISTRIBUTION")
print("----------------------------")

print(
    df["agent_review_label"]
    .value_counts()
    .to_string()
)


# ==================================================
# CONFUSION MATRIX
# ==================================================

print("\n----------------------------")
print("AGENT VS HUMAN")
print("----------------------------")

comparison = pd.crosstab(
    df["human_label"],
    df["agent_review_label"],
)

print(
    comparison.to_string()
)


# ==================================================
# DISAGREEMENTS
# ==================================================

errors = df[
    ~df["agreement"]
].copy()


print("\n----------------------------")
print("DISAGREEMENTS")
print("----------------------------")

print(
    "Total:",
    len(errors)
)


if len(errors) > 0:

    columns = [
        "ServiceName",
        "start_hour",
        "end_hour",
        "peak_action",
        "feedback_summary",
        "agent_review_label",
        "human_label",
        "human_confidence",
        "driver_description",
        "driver_cost_change_pct",
        "driver_usage_change_pct",
        "driver_unit_cost_change_pct",
        "review_notes",
    ]

    print(
        errors[
            columns
        ]
        .to_string(
            index=False
        )
    )


# ==================================================
# HIGH-CONFIDENCE HUMAN REVIEWS ONLY
# ==================================================

high = df[
    df["human_confidence"]
    == "HIGH"
].copy()

high_correct = (
    high["agreement"]
    .sum()
)

print("\n----------------------------")
print("HIGH-CONFIDENCE REVIEW")
print("----------------------------")

print(
    "Episodes:",
    len(high)
)

print(
    "Agreements:",
    high_correct
)

print(
    "Agreement rate:",
    high_correct
    / len(high)
)