import pandas as pd

from real_belief import (
    build_real_belief,
    update_real_belief_from_feedback,
)

from real_driver_evidence import (
    load_driver_data,
    check_cost_driver,
)

from real_feedback import (
    interpret_driver_evidence,
)


INPUT_PATH = "data/real/aws_real_agent_inputs.csv"


# ==================================================
# SELECT MOST RELEVANT USAGE SIGNAL
# ==================================================

def select_usage_evidence(row):

    # S3 storage is daily and was the dominant
    # explanatory signal for the observed S3 event.
    if (
        row["ServiceName"]
        == "Amazon Simple Storage Service"
        and pd.notna(
            row["storage_usage_change_pct"]
        )
    ):

        return {
            "usage_unit": "GB-Months",

            "usage_change_pct":
                row["storage_usage_change_pct"],

            "unit_cost_percentile":
                row["storage_unit_cost_percentile"],
        }

    return {
        "usage_unit":
            row["primary_usage_unit"],

        "usage_change_pct":
            row["primary_usage_change_pct"],

        "unit_cost_percentile":
            row["primary_unit_cost_percentile"],
    }


# ==================================================
# ACTION POLICY
# ==================================================

def select_real_action(belief):

    incident_score = (
        belief["cost_incident"]
    )

    if incident_score < 0.30:

        return "WAIT"

    elif incident_score < 0.50:

        return "GET_MORE_EVIDENCE"

    elif incident_score < 0.70:

        return "ASK_HUMAN"

    else:

        return "ESCALATE"


# ==================================================
# RUN TWO-STAGE REAL AGENT
# ==================================================

def run_real_agent(
    row,
    driver_data=None,
):

    # ==================================================
    # STAGE 1 — INITIAL EVIDENCE
    # ==================================================

    usage_evidence = (
        select_usage_evidence(row)
    )

    initial_belief = build_real_belief(

        cost_change_pct=
            row["usage_cost_change_pct"],

        cost_percentile=
            row["cost_percentile"],

        usage_change_pct=
            usage_evidence[
                "usage_change_pct"
            ],

        unit_cost_percentile=
            usage_evidence[
                "unit_cost_percentile"
            ],

        new_account_percentile=
            row["new_account_percentile"],

        matches_historical_pattern=
            row[
                "matches_historical_pattern"
            ],
    )

    initial_action = (
        select_real_action(
            initial_belief
        )
    )


    # Default final state
    final_belief = (
        initial_belief.copy()
    )

    final_action = initial_action

    driver_evidence = None

    feedback = None


    # ==================================================
    # STAGE 2 — REAL DRIVER INVESTIGATION
    # ==================================================

    if (
        initial_action != "WAIT"
        and driver_data is not None
    ):

        driver_evidence, _ = (
            check_cost_driver(

                driver_data,

                service_name=
                    row["ServiceName"],

                current_hour=
                    row["hour"],
            )
        )

        feedback = (
            interpret_driver_evidence(
                driver_evidence
            )
        )

        final_belief = (
            update_real_belief_from_feedback(
                initial_belief,
                feedback,
            )
        )

        final_action = (
            select_real_action(
                final_belief
            )
        )


    # ==================================================
    # RESULT
    # ==================================================

    return {

        "service_name":
            row["ServiceName"],

        "hour":
            row["hour"],

        "cost_change_pct":
            row["usage_cost_change_pct"],

        "cost_percentile":
            row["cost_percentile"],

        "selected_usage_unit":
            usage_evidence[
                "usage_unit"
            ],

        "usage_change_pct":
            usage_evidence[
                "usage_change_pct"
            ],

        "unit_cost_percentile":
            usage_evidence[
                "unit_cost_percentile"
            ],

        "new_account_percentile":
            row[
                "new_account_percentile"
            ],

        "matches_historical_pattern":
            row[
                "matches_historical_pattern"
            ],

        "initial_belief":
            initial_belief,

        "initial_action":
            initial_action,

        "driver_evidence":
            driver_evidence,

        "feedback":
            feedback,

        "final_belief":
            final_belief,

        "final_action":
            final_action,
    }


# ==================================================
# TEST ON HIGH-RISK RDS CASE
# ==================================================

if __name__ == "__main__":

    print(
        "Loading agent input data..."
    )

    df = pd.read_csv(
        INPUT_PATH,
        parse_dates=["hour"],
    )

    print(
        "Loading driver evidence data..."
    )

    driver_data = (
        load_driver_data()
    )


    # High-risk RDS observation from previous run
    event = df[
        (
            df["ServiceName"]
            == "Amazon Elastic File System"
        )
        &
        (
            df["hour"]
            == pd.Timestamp(
                "2024-09-22 01:00:00"
            )
        )
    ].iloc[0]


    result = run_real_agent(
        event,
        driver_data=driver_data,
    )


    print("\n----------------------------")
    print("REAL TWO-STAGE AGENT")
    print("----------------------------")

    print(
        "Service:",
        result["service_name"]
    )

    print(
        "Hour:",
        result["hour"]
    )


    print("\nINITIAL BELIEF")

    for state, probability in (
        result["initial_belief"]
        .items()
    ):

        print(
            f"{state}: {probability:.4f}"
        )


    print(
        "\nINITIAL ACTION:",
        result["initial_action"]
    )


    print("\nDRIVER FEEDBACK")

    print(
        result["feedback"]
    )


    if (
        result["driver_evidence"]
        is not None
    ):

        evidence = (
            result[
                "driver_evidence"
            ]
        )

        print(
            "Driver:",
            evidence[
                "charge_description"
            ]
        )

        print(
            "Sub-account:",
            evidence[
                "sub_account"
            ]
        )

        print(
            "Driver cost change:",
            evidence[
                "cost_change_pct"
            ]
        )

        print(
            "Driver usage change:",
            evidence[
                "usage_change_pct"
            ]
        )

        print(
            "Driver unit-cost change:",
            evidence[
                "unit_cost_change_pct"
            ]
        )


    print("\nFINAL BELIEF")

    for state, probability in (
        result["final_belief"]
        .items()
    ):

        print(
            f"{state}: {probability:.4f}"
        )


    print(
        "\nFINAL ACTION:",
        result["final_action"]
    )