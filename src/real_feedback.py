import math


def is_missing(value):

    return (
        value is None
        or (
            isinstance(value, float)
            and math.isnan(value)
        )
    )


def relative_difference(a, b):
    """
    Measure how different two percentage changes are.

    Example:
        billed cost +100%
        usage       +105%

    These are closely aligned.
    """

    return abs(a - b) / max(
        abs(a),
        abs(b),
        1.0,
    )


def interpret_driver_evidence(evidence):
    """
    Convert measured FinOps driver evidence into
    a structured feedback signal.

    These rules are heuristic and experimental.
    They are not learned or calibrated probabilities.
    """

    if evidence is None:

        return "INSUFFICIENT_DRIVER_EVIDENCE"


    # ==================================================
    # READ EVIDENCE
    # ==================================================

    effective_cost_change = (
        evidence.get(
            "cost_change_pct"
        )
    )

    billed_cost_change = (
        evidence.get(
            "billed_cost_change_pct"
        )
    )

    usage_change = (
        evidence.get(
            "usage_change_pct"
        )
    )

    billed_unit_change = (
        evidence.get(
            "unit_cost_change_pct"
        )
    )

    list_price_change = (
        evidence.get(
            "list_unit_price_change_pct"
        )
    )

    is_new_driver = (
        evidence.get(
            "is_new_driver",
            False,
        )
    )


    # ==================================================
    # NEW DRIVER
    # ==================================================

    if is_new_driver:

        return "NEW_COST_DRIVER"


    # ==================================================
    # REQUIRED EVIDENCE
    # ==================================================

    if (
        is_missing(
            effective_cost_change
        )
        or
        is_missing(
            usage_change
        )
    ):

        return (
            "INSUFFICIENT_DRIVER_EVIDENCE"
        )


    # ==================================================
    # IS ACTUAL PRICE STABLE?
    # ==================================================

    billed_price_stable = (
        not is_missing(
            billed_unit_change
        )
        and
        abs(
            billed_unit_change
        ) <= 10
    )


    list_price_stable = (
        is_missing(
            list_price_change
        )
        or
        abs(
            list_price_change
        ) <= 10
    )


    # ==================================================
    # DO BILLED COST AND USAGE MOVE TOGETHER?
    #
    # Important:
    # They can both rise, both fall, or move only
    # moderately.
    #
    # We no longer require both to be > +20%.
    # ==================================================

    billed_usage_aligned = False

    if (
        not is_missing(
            billed_cost_change
        )
        and
        not is_missing(
            usage_change
        )
    ):

        billed_usage_gap = (
            relative_difference(
                billed_cost_change,
                usage_change,
            )
        )

        billed_usage_aligned = (
            billed_usage_gap <= 0.20
        )


    # ==================================================
    # EFFECTIVE COST ACCOUNTING SHIFT
    #
    # If:
    #
    # billed cost follows usage
    # actual unit price is stable
    # list price is stable
    #
    # BUT EffectiveCost behaves very differently,
    #
    # then the unusual signal is likely coming from
    # EffectiveCost accounting representation.
    # ==================================================

    if (
        billed_usage_aligned
        and
        billed_price_stable
        and
        list_price_stable
        and
        not is_missing(
            billed_cost_change
        )
    ):

        effective_billed_gap = (
            relative_difference(
                effective_cost_change,
                billed_cost_change,
            )
        )

        if (
            abs(
                effective_cost_change
            ) >= 20
            and
            effective_billed_gap >= 0.30
        ):

            return (
                "EFFECTIVE_COST_ACCOUNTING_SHIFT"
            )


    # ==================================================
    # USAGE-ALIGNED GROWTH
    #
    # Billed cost and usage increase together,
    # pricing remains stable, and EffectiveCost is
    # reasonably consistent with the same story.
    # ==================================================

    if (
        billed_usage_aligned
        and
        billed_price_stable
        and
        list_price_stable
        and
        not is_missing(
            billed_cost_change
        )
        and
        billed_cost_change > 20
        and
        usage_change > 20
    ):

        return (
            "USAGE_ALIGNED_DRIVER_GROWTH"
        )


    # ==================================================
    # REAL UNIT-PRICE INCREASE
    # ==================================================

    if (
        not is_missing(
            billed_unit_change
        )
        and
        billed_unit_change >= 20
    ):

        return "UNIT_COST_INCREASE"


    # ==================================================
    # EFFECTIVE COST / USAGE ALIGNMENT
    #
    # Fallback when billed evidence is unavailable.
    # ==================================================

    effective_usage_gap = (
        relative_difference(
            effective_cost_change,
            usage_change,
        )
    )


    if (
        effective_cost_change > 20
        and
        usage_change > 20
        and
        effective_usage_gap <= 0.20
        and
        billed_price_stable
    ):

        return (
            "USAGE_ALIGNED_DRIVER_GROWTH"
        )


    # ==================================================
    # UNEXPLAINED COST INCREASE
    #
    # Only use this after checking that the divergence
    # cannot be explained by billing/accounting
    # representation or actual price changes.
    # ==================================================

    if (
        effective_cost_change > 20
        and
        (
            usage_change < 10
            or
            effective_usage_gap >= 0.50
        )
    ):

        return (
            "UNEXPLAINED_DRIVER_COST_INCREASE"
        )


    # ==================================================
    # OTHERWISE KEEP UNCERTAINTY
    # ==================================================

    return "MIXED_DRIVER_EVIDENCE"