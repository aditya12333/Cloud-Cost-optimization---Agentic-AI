import sys
sys.path.append("src")
import pandas as pd
from cost import decision_cost

evidence_options = [
    "CHECK_SERVICE_BREAKDOWN",
    "CHECK_DEPLOYMENT_DETAILS"
]


def select_evidence(case, belief):

    scores = {
        "CHECK_SERVICE_BREAKDOWN": 0,
        "CHECK_DEPLOYMENT_DETAILS": 0
    }

    # If incident vs legitimate growth is plausible,
    # service-level evidence is useful.
    if (
        belief["cost_incident"] >= 0.25
        or belief["legitimate_growth"] >= 0.25
    ):
        scores["CHECK_SERVICE_BREAKDOWN"] += 4

    # If there was a recent deployment,
    # deployment details may explain the cost change.
    if case["recent_deployment"]:
        scores["CHECK_DEPLOYMENT_DETAILS"] += 3

    # Relative evidence-collection costs
    costs = {
        "CHECK_SERVICE_BREAKDOWN": 2,
        "CHECK_DEPLOYMENT_DETAILS": 2
    }

    value = {
        evidence: scores[evidence] / costs[evidence]
        for evidence in scores
    }

    return max(value, key=value.get)

def calculate_total_cost(file_path):

    df = pd.read_csv(file_path)

    df["decision_cost"] = df.apply(
        lambda row: decision_cost(
            row["true_state"],
            row["action"]
        ),
        axis=1
    )

    print(file_path)
    print("Total decision cost:", df["decision_cost"].sum())
    print("Average decision cost:", df["decision_cost"].mean())
    print()

calculate_total_cost("results/predictionsv1_on_v2.csv")
calculate_total_cost("results/predictions_v2.csv")
calculate_total_cost("results/predictions_v3.csv")