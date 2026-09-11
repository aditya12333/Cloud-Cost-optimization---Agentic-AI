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
# FIX EMPTY TEXT COLUMN TYPES
# ==================================================

df["human_label"] = (
    df["human_label"]
    .astype("object")
)

df["human_confidence"] = (
    df["human_confidence"]
    .astype("object")
)

df["review_notes"] = (
    df["review_notes"]
    .astype("object")
)


# ==================================================
# HUMAN REVIEW LABELS
# ==================================================

labels = {

    # ==================================================
    # EKS — LEGITIMATE GROWTH
    # ==================================================

    "2024-09-16 11:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased by the same amount while unit cost remained unchanged. The higher cost is explained by increased use of the existing EKS extended-support driver."
    ),

    "2024-09-21 14:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased proportionally while unit cost remained unchanged. The higher cost is explained by increased EKS extended-support usage."
    ),

    "2024-09-22 00:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased proportionally while unit cost remained unchanged. The higher cost is explained by increased EKS extended-support usage."
    ),

    "2024-09-23 04:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased proportionally while unit cost remained unchanged. The higher cost is explained by increased EKS extended-support usage."
    ),

    "2024-09-23 11:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased proportionally while unit cost remained unchanged. The higher cost is explained by increased EKS extended-support usage."
    ),

    "2024-09-23 14:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased proportionally while unit cost remained unchanged. The higher cost is explained by increased EKS extended-support usage."
    ),

    "2024-09-23 22:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased proportionally while unit cost remained unchanged. The higher cost is explained by increased EKS extended-support usage."
    ),

    "2024-09-27 14:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased proportionally while unit cost remained unchanged. The higher cost is explained by increased EKS extended-support usage."
    ),

    "2024-09-30 17:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Cost and consumed usage increased proportionally while unit cost remained unchanged. The higher cost is explained by increased EKS extended-support usage."
    ),


    # ==================================================
    # EFS — ACCOUNTING / BILLING EFFECT
    # ==================================================

    "2024-09-21 08:00:00": (
        "ACCOUNTING_OR_BILLING_EFFECT",
        "HIGH",
        "Effective cost increased much faster than usage while billed unit cost remained unchanged. This is consistent with an EffectiveCost accounting or allocation effect rather than a true unit-price increase."
    ),

    "2024-09-23 10:00:00": (
        "ACCOUNTING_OR_BILLING_EFFECT",
        "HIGH",
        "Effective cost increased materially faster than usage while billed unit cost remained unchanged. This is consistent with an accounting or allocation effect."
    ),

    "2024-09-23 15:00:00": (
        "ACCOUNTING_OR_BILLING_EFFECT",
        "HIGH",
        "Effective cost increased materially faster than usage while billed unit cost remained unchanged. This is consistent with an accounting or allocation effect."
    ),

    "2024-09-29 12:00:00": (
        "ACCOUNTING_OR_BILLING_EFFECT",
        "HIGH",
        "Effective cost increased materially faster than usage while billed unit cost remained unchanged. This is consistent with an accounting or allocation effect."
    ),

    "2024-09-29 14:00:00": (
        "ACCOUNTING_OR_BILLING_EFFECT",
        "HIGH",
        "Effective cost increased materially faster than usage while billed unit cost remained unchanged. This is consistent with an accounting or allocation effect."
    ),


    # ==================================================
    # EFS — LEGITIMATE GROWTH
    # ==================================================

    "2024-09-29 07:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "Usage increased substantially while billed unit cost remained unchanged. Most of the higher cost is explained by increased use of the existing EFS throughput driver."
    ),


    # ==================================================
    # RDS — LEGITIMATE GROWTH
    # ==================================================

    "2024-09-15 23:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "RDS cost increased proportionally with consumed instance-hours while unit cost remained unchanged. The increase is explained by increased workload usage."
    ),

    "2024-09-16 11:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "RDS cost increased proportionally with consumed instance-hours while unit cost remained unchanged. The increase is explained by increased workload usage."
    ),

    "2024-09-17 11:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "RDS cost increased proportionally with consumed instance-hours while unit cost remained unchanged. The increase is explained by increased workload usage."
    ),

    "2024-09-17 21:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "RDS cost increased proportionally with consumed instance-hours while unit cost remained unchanged. The increase is explained by increased workload usage."
    ),

    "2024-09-18 21:00:00": (
        "LEGITIMATE_GROWTH",
        "HIGH",
        "RDS cost increased proportionally with consumed instance-hours while unit cost remained unchanged. The increase is explained by increased workload usage."
    ),


    # ==================================================
    # S3 — UNRESOLVED
    # ==================================================

    "2024-09-17 15:00:00": (
        "UNRESOLVED",
        "MEDIUM",
        "A new S3 storage cost driver appeared with substantial consumption and no historical baseline. Billing data alone cannot determine whether the new storage usage was expected or operationally legitimate."
    ),

    "2024-09-21 10:00:00": (
        "UNRESOLVED",
        "MEDIUM",
        "A new S3 data-transfer-out driver appeared with substantial usage and no prior baseline. Additional deployment, application traffic, or network-flow context is required."
    ),

    "2024-09-30 06:00:00": (
        "UNRESOLVED",
        "MEDIUM",
        "A new S3 storage-tier cost driver appeared with significant usage and no historical baseline. Additional workload or business context is required."
    ),
}


# ==================================================
# APPLY LABELS
# ==================================================

for start_hour, (
    human_label,
    human_confidence,
    review_notes,
) in labels.items():

    mask = (
        df["start_hour"]
        == pd.Timestamp(start_hour)
    )

    df.loc[
        mask,
        "human_label"
    ] = human_label

    df.loc[
        mask,
        "human_confidence"
    ] = human_confidence

    df.loc[
        mask,
        "review_notes"
    ] = review_notes


# ==================================================
# SAVE UPDATED REVIEW TABLE
# ==================================================

df.to_csv(
    PATH,
    index=False,
)


# ==================================================
# VALIDATION
# ==================================================

labelled_mask = (
    df["human_label"]
    .fillna("")
    != ""
)

labelled_count = (
    labelled_mask.sum()
)

unlabelled_count = (
    len(df)
    - labelled_count
)


print("\n----------------------------")
print("HUMAN LABELS APPLIED")
print("----------------------------")

print(
    "Total episodes:",
    len(df)
)

print(
    "Labelled episodes:",
    labelled_count
)

print(
    "Unlabelled episodes:",
    unlabelled_count
)


print("\nLabel distribution:")

print(
    df["human_label"]
    .value_counts(
        dropna=False
    )
    .to_string()
)


print("\nConfidence distribution:")

print(
    df["human_confidence"]
    .value_counts(
        dropna=False
    )
    .to_string()
)


# ==================================================
# CHECK FOR MISSING LABELS
# ==================================================

if unlabelled_count > 0:

    print("\n----------------------------")
    print("UNLABELLED EPISODES")
    print("----------------------------")

    print(
        df.loc[
            ~labelled_mask,
            [
                "ServiceName",
                "start_hour",
                "end_hour",
                "peak_action",
            ],
        ]
        .to_string(
            index=False
        )
    )

else:

    print(
        "\nAll episodes have human-review labels."
    )