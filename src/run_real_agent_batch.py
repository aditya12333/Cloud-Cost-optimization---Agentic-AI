import pandas as pd
from pathlib import Path

from real_agent import (
    run_real_agent,
)

from real_driver_evidence import (
    load_driver_data,
)


INPUT_PATH = (
    "data/real/aws_real_agent_inputs.csv"
)

OUTPUT_PATH = (
    "results/real_two_stage_agent_decisions.csv"
)


def get_predicted_state(belief):

    return max(
        belief,
        key=belief.get,
    )


def run_batch():

    df = pd.read_csv(
        INPUT_PATH,
        parse_dates=["hour"],
    )

    df = df[
        df["agent_ready"] == True
    ].copy()

    print(
        "Loading driver evidence..."
    )

    driver_data = (
        load_driver_data()
    )

    results = []

    total = len(df)

    for i, row in enumerate(
        df.itertuples(index=False),
        start=1,
    ):

        # Convert namedtuple to Series because
        # run_real_agent expects dictionary-like access.
        row = pd.Series(
            row._asdict()
        )

        result = run_real_agent(
            row,
            driver_data=driver_data,
        )

        initial_belief = (
            result["initial_belief"]
        )

        final_belief = (
            result["final_belief"]
        )

        evidence = (
            result["driver_evidence"]
        )

        results.append(
            {
                "hour":
                    result["hour"],

                "ServiceName":
                    result["service_name"],

                # ------------------------------
                # INITIAL DECISION
                # ------------------------------

                "initial_normal":
                    initial_belief["normal"],

                "initial_expected_pattern":
                    initial_belief[
                        "expected_pattern"
                    ],

                "initial_legitimate_growth":
                    initial_belief[
                        "legitimate_growth"
                    ],

                "initial_cost_incident":
                    initial_belief[
                        "cost_incident"
                    ],

                "initial_predicted_state":
                    get_predicted_state(
                        initial_belief
                    ),

                "initial_action":
                    result[
                        "initial_action"
                    ],

                # ------------------------------
                # REAL EVIDENCE
                # ------------------------------

                "feedback":
                    result["feedback"],

                "driver_description":
                    (
                        evidence[
                            "charge_description"
                        ]
                        if evidence
                        else None
                    ),

                "driver_sub_account":
                    (
                        evidence[
                            "sub_account"
                        ]
                        if evidence
                        else None
                    ),

                "driver_cost_change_pct":
                    (
                        evidence[
                            "cost_change_pct"
                        ]
                        if evidence
                        else None
                    ),

                "driver_usage_change_pct":
                    (
                        evidence[
                            "usage_change_pct"
                        ]
                        if evidence
                        else None
                    ),

                "driver_unit_cost_change_pct":
                    (
                        evidence[
                            "unit_cost_change_pct"
                        ]
                        if evidence
                        else None
                    ),

                # ------------------------------
                # FINAL DECISION
                # ------------------------------

                "final_normal":
                    final_belief[
                        "normal"
                    ],

                "final_expected_pattern":
                    final_belief[
                        "expected_pattern"
                    ],

                "final_legitimate_growth":
                    final_belief[
                        "legitimate_growth"
                    ],

                "final_cost_incident":
                    final_belief[
                        "cost_incident"
                    ],

                "final_predicted_state":
                    get_predicted_state(
                        final_belief
                    ),

                "final_action":
                    result[
                        "final_action"
                    ],
            }
        )

        if i % 100 == 0:

            print(
                f"Processed {i}/{total}"
            )

    return pd.DataFrame(
        results
    )


if __name__ == "__main__":

    print(
        "Running two-stage real agent..."
    )

    results = run_batch()

    Path(
        "results"
    ).mkdir(
        exist_ok=True
    )

    results.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )


    # ==================================================
    # ACTION COMPARISON
    # ==================================================

    print("\n----------------------------")
    print("TWO-STAGE ACTION COMPARISON")
    print("----------------------------")

    print("\nINITIAL ACTIONS")

    print(
        results[
            "initial_action"
        ]
        .value_counts()
        .to_string()
    )

    print("\nFINAL ACTIONS")

    print(
        results[
            "final_action"
        ]
        .value_counts()
        .to_string()
    )


    # ==================================================
    # ACTION TRANSITIONS
    # ==================================================

    print("\n----------------------------")
    print("ACTION TRANSITIONS")
    print("----------------------------")

    transitions = pd.crosstab(
        results[
            "initial_action"
        ],
        results[
            "final_action"
        ],
    )

    print(
        transitions.to_string()
    )


    # ==================================================
    # FEEDBACK DISTRIBUTION
    # ==================================================

    print("\n----------------------------")
    print("REAL FEEDBACK DISTRIBUTION")
    print("----------------------------")

    print(
        results[
            "feedback"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )


    # ==================================================
    # CHANGED DECISIONS
    # ==================================================

    changed = results[
        results[
            "initial_action"
        ]
        !=
        results[
            "final_action"
        ]
    ]

    print("\n----------------------------")
    print("DECISION CHANGES")
    print("----------------------------")

    print(
        "Changed decisions:",
        len(changed)
    )

    print(
        "Change rate:",
        len(changed)
        / len(results)
    )


    print("\nChanges by service:")

    print(
        changed[
            "ServiceName"
        ]
        .value_counts()
        .to_string()
    )