import pandas as pd


INPUT_PATH = (
    "results/real_two_stage_agent_decisions.csv"
)

OUTPUT_PATH = (
    "results/real_two_stage_episodes.csv"
)


ACTION_SEVERITY = {
    "WAIT": 0,
    "GET_MORE_EVIDENCE": 1,
    "ASK_HUMAN": 2,
    "ESCALATE": 3,
}


def build_episodes():

    df = pd.read_csv(
        INPUT_PATH,
        parse_dates=["hour"],
    )

    # Keep only final decisions requiring action
    alerts = df[
        df["final_action"] != "WAIT"
    ].copy()

    alerts = alerts.sort_values(
        [
            "ServiceName",
            "hour",
        ]
    )

    alerts["severity"] = (
        alerts["final_action"]
        .map(ACTION_SEVERITY)
    )

    alerts["previous_hour"] = (
        alerts
        .groupby("ServiceName")["hour"]
        .shift(1)
    )

    alerts["gap_hours"] = (
        (
            alerts["hour"]
            - alerts["previous_hour"]
        )
        / pd.Timedelta(hours=1)
    )

    # Start a new episode if alerts are
    # not consecutive.
    alerts["new_episode"] = (
        alerts["previous_hour"].isna()
        | (alerts["gap_hours"] > 1)
    )

    alerts["episode_number"] = (
        alerts
        .groupby("ServiceName")[
            "new_episode"
        ]
        .cumsum()
    )

    episodes = (
        alerts.groupby(
            [
                "ServiceName",
                "episode_number",
            ],
            as_index=False,
        )
        .agg(
            start_hour=("hour", "min"),
            end_hour=("hour", "max"),

            decision_count=("hour", "size"),

            max_severity=("severity", "max"),

            max_initial_incident_belief=(
                "initial_cost_incident",
                "max",
            ),

            max_final_incident_belief=(
                "final_cost_incident",
                "max",
            ),

            feedback=(
                "feedback",
                lambda x: ",".join(
                    sorted(set(x.dropna()))
                ),
            ),
        )
    )

    severity_to_action = {
        value: key
        for key, value
        in ACTION_SEVERITY.items()
    }

    episodes["peak_action"] = (
        episodes["max_severity"]
        .map(severity_to_action)
    )

    episodes["duration_hours"] = (
        (
            episodes["end_hour"]
            - episodes["start_hour"]
        )
        / pd.Timedelta(hours=1)
        + 1
    )

    return episodes


if __name__ == "__main__":

    print(
        "Building two-stage alert episodes..."
    )

    episodes = build_episodes()

    episodes.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    print("\n----------------------------")
    print("TWO-STAGE ALERT EPISODES")
    print("----------------------------")

    print(
        "Total episodes:",
        len(episodes)
    )

    print("\nEpisodes by peak action:")

    print(
        episodes["peak_action"]
        .value_counts()
        .to_string()
    )

    print("\nEpisodes by service:")

    print(
        episodes["ServiceName"]
        .value_counts()
        .to_string()
    )

    print("\n----------------------------")
    print("FINAL ESCALATION EPISODES")
    print("----------------------------")

    escalations = episodes[
        episodes["peak_action"]
        == "ESCALATE"
    ]

    print(
        escalations[
            [
                "ServiceName",
                "start_hour",
                "end_hour",
                "duration_hours",
                "decision_count",
                "max_initial_incident_belief",
                "max_final_incident_belief",
                "feedback",
            ]
        ]
        .to_string(index=False)
    )