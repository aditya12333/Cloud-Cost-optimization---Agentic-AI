import pandas as pd


INPUT_PATH = "results/real_agent_decisions.csv"

OUTPUT_PATH = "results/real_agent_episodes.csv"


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

    # Only decisions requiring some action
    alerts = df[
        df["action"] != "WAIT"
    ].copy()

    alerts = alerts.sort_values(
        [
            "ServiceName",
            "hour",
        ]
    )

    alerts["severity"] = (
        alerts["action"]
        .map(ACTION_SEVERITY)
    )

    # Previous alert timestamp for same service
    alerts["previous_hour"] = (
        alerts.groupby("ServiceName")["hour"]
        .shift(1)
    )

    alerts["gap_hours"] = (
        (
            alerts["hour"]
            - alerts["previous_hour"]
        )
        / pd.Timedelta(hours=1)
    )

    # New episode if:
    # - first alert for service
    # - previous alert was not the immediately preceding hour
    alerts["new_episode"] = (
        alerts["previous_hour"].isna()
        | (alerts["gap_hours"] > 1)
    )

    alerts["episode_number"] = (
        alerts.groupby("ServiceName")[
            "new_episode"
        ]
        .cumsum()
    )

    # --------------------------------------------------
    # EPISODE SUMMARY
    # --------------------------------------------------

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

            max_incident_belief=(
                "belief_cost_incident",
                "max",
            ),

            mean_incident_belief=(
                "belief_cost_incident",
                "mean",
            ),

            max_cost_change_pct=(
                "cost_change_pct",
                "max",
            ),

            max_usage_change_pct=(
                "usage_change_pct",
                "max",
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
        "Building real alert episodes..."
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
    print("REAL ALERT EPISODES")
    print("----------------------------")

    print(
        "Total episodes:",
        len(episodes)
    )

    print("\nEpisodes by service:")

    print(
        episodes["ServiceName"]
        .value_counts()
        .to_string()
    )

    print("\nEpisodes by peak action:")

    print(
        episodes["peak_action"]
        .value_counts()
        .to_string()
    )

    print("\n----------------------------")
    print("TOP 10 HIGHEST-RISK EPISODES")
    print("----------------------------")

    columns = [
        "ServiceName",
        "start_hour",
        "end_hour",
        "duration_hours",
        "decision_count",
        "max_incident_belief",
        "max_cost_change_pct",
        "peak_action",
    ]

    print(
        episodes
        .sort_values(
            "max_incident_belief",
            ascending=False,
        )
        [columns]
        .head(10)
        .to_string(index=False)
    )