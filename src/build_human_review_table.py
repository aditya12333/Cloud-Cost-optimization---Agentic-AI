import pandas as pd


EPISODES_PATH = (
    "results/real_two_stage_episodes.csv"
)

DECISIONS_PATH = (
    "results/real_two_stage_agent_decisions.csv"
)

OUTPUT_PATH = (
    "results/real_episode_human_review.csv"
)


def build_review_table():

    episodes = pd.read_csv(
        EPISODES_PATH,
        parse_dates=[
            "start_hour",
            "end_hour",
        ],
    )

    decisions = pd.read_csv(
        DECISIONS_PATH,
        parse_dates=["hour"],
    )


    review_rows = []


    for _, episode in episodes.iterrows():

        service = (
            episode["ServiceName"]
        )

        start = (
            episode["start_hour"]
        )

        end = (
            episode["end_hour"]
        )


        # ------------------------------------------
        # GET ALL DECISIONS INSIDE THIS EPISODE
        # ------------------------------------------

        rows = decisions[
            (
                decisions["ServiceName"]
                == service
            )
            &
            (
                decisions["hour"] >= start
            )
            &
            (
                decisions["hour"] <= end
            )
        ].copy()


        if rows.empty:
            continue


        # ------------------------------------------
        # REPRESENTATIVE / MOST SEVERE OBSERVATION
        #
        # Use highest final incident belief.
        # ------------------------------------------

        representative = (
            rows.sort_values(
                "final_cost_incident",
                ascending=False,
            )
            .iloc[0]
        )


        # ------------------------------------------
        # FEEDBACK VALUES ACROSS EPISODE
        # ------------------------------------------

        feedback_values = (
            rows["feedback"]
            .dropna()
            .unique()
            .tolist()
        )


        feedback_summary = (
            ", ".join(
                sorted(
                    feedback_values
                )
            )
        )


        # ------------------------------------------
        # BUILD REVIEW ROW
        # ------------------------------------------

        review_rows.append(
            {
                "ServiceName":
                    service,

                "start_hour":
                    start,

                "end_hour":
                    end,

                "duration_hours":
                    episode[
                        "duration_hours"
                    ],

                "decision_count":
                    episode[
                        "decision_count"
                    ],

                "peak_action":
                    episode[
                        "peak_action"
                    ],

                "max_initial_incident_belief":
                    episode[
                        "max_initial_incident_belief"
                    ],

                "max_final_incident_belief":
                    episode[
                        "max_final_incident_belief"
                    ],

                "representative_hour":
                    representative[
                        "hour"
                    ],

                "initial_action":
                    representative[
                        "initial_action"
                    ],

                "final_action":
                    representative[
                        "final_action"
                    ],

                "feedback_summary":
                    feedback_summary,

                "driver_description":
                    representative[
                        "driver_description"
                    ],

                "driver_sub_account":
                    representative[
                        "driver_sub_account"
                    ],

                "driver_cost_change_pct":
                    representative[
                        "driver_cost_change_pct"
                    ],

                "driver_usage_change_pct":
                    representative[
                        "driver_usage_change_pct"
                    ],

                "driver_unit_cost_change_pct":
                    representative[
                        "driver_unit_cost_change_pct"
                    ],

                # ----------------------------------
                # HUMAN REVIEW FIELDS
                # ----------------------------------

                "human_label":
                    "",

                "human_confidence":
                    "",

                "review_notes":
                    "",
            }
        )


    return pd.DataFrame(
        review_rows
    )


if __name__ == "__main__":

    print(
        "Building human-review table..."
    )

    review = build_review_table()

    review.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("HUMAN REVIEW TABLE")
    print("----------------------------")

    print(
        "Episodes:",
        len(review)
    )

    print("\nBy service:")

    print(
        review[
            "ServiceName"
        ]
        .value_counts()
        .to_string()
    )

    print("\nBy final action:")

    print(
        review[
            "peak_action"
        ]
        .value_counts()
        .to_string()
    )

    print("\nColumns:")

    print(
        review.columns.tolist()
    )