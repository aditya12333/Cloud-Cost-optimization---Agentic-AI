def normalize(scores):

    total = sum(scores.values())

    return {
        state: score / total
        for state, score in scores.items()
    }


def build_real_belief(
    cost_change_pct,
    cost_percentile,
    usage_change_pct,
    unit_cost_percentile,
    new_account_percentile,
    matches_historical_pattern,
):
    """
    Build a heuristic belief from real FinOps evidence.

    These are normalized decision scores, NOT calibrated
    real-world probabilities.
    """

    scores = {
        "normal": 1.0,
        "expected_pattern": 1.0,
        "legitimate_growth": 1.0,
        "cost_incident": 1.0,
    }

    # ==================================================
    # HISTORICAL PATTERN
    # ==================================================

    if matches_historical_pattern:

        scores["expected_pattern"] += 2.0
        scores["normal"] += 0.5

    else:

        scores["expected_pattern"] *= 0.5


    # ==================================================
    # COST ANOMALY
    # ==================================================

    if cost_percentile >= 95:

        scores["cost_incident"] += 2.0
        scores["normal"] *= 0.5

    elif cost_percentile >= 80:

        scores["cost_incident"] += 1.0


    # ==================================================
    # USAGE GROWTH
    # ==================================================

    if usage_change_pct >= 50:

        scores["legitimate_growth"] += 2.0

    elif usage_change_pct >= 20:

        scores["legitimate_growth"] += 1.0


    # ==================================================
    # COST / USAGE ALIGNMENT
    # ==================================================

    if cost_change_pct > 0 and usage_change_pct > 0:

        relative_gap = abs(
            cost_change_pct - usage_change_pct
        ) / max(
            abs(cost_change_pct),
            1,
        )

        # Cost increase is largely explained by
        # usage growth.
        if relative_gap <= 0.35:

            scores["legitimate_growth"] += 2.0

        # Cost is growing much faster than usage.
        elif cost_change_pct > usage_change_pct:

            scores["cost_incident"] += 1.0


    # ==================================================
    # UNIT COST
    # ==================================================

    if unit_cost_percentile >= 95:

        scores["cost_incident"] += 1.5

    elif unit_cost_percentile >= 80:

        scores["cost_incident"] += 0.5


    # ==================================================
    # NEW ACCOUNT ACTIVITY
    # ==================================================

    if new_account_percentile >= 95:

        scores["cost_incident"] += 1.0

    elif new_account_percentile >= 80:

        scores["cost_incident"] += 0.25


    # ==================================================
    # NORMAL BEHAVIOUR
    # ==================================================

    # If cost is not particularly unusual and usage
    # behaviour is also moderate, normal becomes more
    # plausible.
    if (
        cost_percentile < 70
        and abs(cost_change_pct) < 20
        and abs(usage_change_pct) < 20
    ):

        scores["normal"] += 1.0


    return normalize(scores)

def update_real_belief_from_feedback(
    belief,
    feedback,
):
    """
    Update the existing real-data belief after
    collecting driver-level evidence.

    These updates are heuristic experimental weights,
    not learned probabilities.
    """

    scores = belief.copy()

    if feedback == "USAGE_ALIGNED_DRIVER_GROWTH":

        scores["legitimate_growth"] += 0.30
        scores["cost_incident"] *= 0.50

    elif feedback == "UNIT_COST_INCREASE":

        scores["cost_incident"] += 0.30
        scores["legitimate_growth"] *= 0.70

    elif feedback == "UNEXPLAINED_DRIVER_COST_INCREASE":

        scores["cost_incident"] += 0.35
        scores["normal"] *= 0.50

    elif feedback == "NEW_COST_DRIVER":

        scores["cost_incident"] += 0.20
        scores["expected_pattern"] *= 0.70

    elif feedback == "EFFECTIVE_COST_ACCOUNTING_SHIFT":

        # Billed cost follows usage and the actual
        # unit price is stable. The unusual movement
        # is primarily in EffectiveCost accounting.

        scores["legitimate_growth"] += 0.20
        scores["expected_pattern"] += 0.05

        scores["cost_incident"] *= 0.60

    elif feedback == "MIXED_DRIVER_EVIDENCE":

        # Keep meaningful uncertainty.
        scores["cost_incident"] += 0.05
        scores["legitimate_growth"] += 0.05

    elif feedback == "INSUFFICIENT_DRIVER_EVIDENCE":

        # No belief change.
        pass

    return normalize(scores)

# ==================================================
# TEST CASE
# ==================================================

if __name__ == "__main__":

    belief = build_real_belief(

        cost_change_pct=141.37931,

        cost_percentile=98.809524,

        usage_change_pct=106.746981,

        unit_cost_percentile=90.0,

        new_account_percentile=86.904762,

        matches_historical_pattern=False,
    )

    print("\n----------------------------")
    print("S3 REAL BELIEF")
    print("----------------------------")

    for state, probability in belief.items():

        print(
            f"{state}: {probability:.4f}"
        )

    print("\n----------------------------")
    print("RDS FEEDBACK BELIEF TEST")
    print("----------------------------")

    rds_initial_belief = {
        "normal": 0.05,
        "expected_pattern": 0.05,
        "legitimate_growth": 0.117647,
        "cost_incident": 0.764706,
    }

    rds_updated_belief = (
        update_real_belief_from_feedback(
            rds_initial_belief,
            "USAGE_ALIGNED_DRIVER_GROWTH",
        )
    )

    for state, probability in rds_updated_belief.items():
        print(
            f"{state}: {probability:.4f}"
        )