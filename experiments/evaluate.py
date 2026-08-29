from pathlib import Path
import sys
import pandas as pd


# --------------------------------------------------
# Project paths
# --------------------------------------------------

project_root = Path(__file__).resolve().parents[1]

src_path = project_root / "src"
data_path = project_root / "data"
results_path = project_root / "results"

sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

results_path.mkdir(exist_ok=True)


# --------------------------------------------------
# Imports
# --------------------------------------------------

from src.agent import run_agent
from src.belief import predicted_state_with_uncertainty
from src.cost import decision_cost, trajectory_cost, evidence_cost


# --------------------------------------------------
# Run V3 on all test cases
# --------------------------------------------------

df = pd.read_csv(
    data_path / "test_cases_v2.csv"
)

results = []


for index, row in df.iterrows():

    case = row.to_dict()

    belief, initial_action, final_action, evidence, feedback = run_agent(
        case,
        version="v3"
    )

    # Predicted state based on FINAL belief,
    # after any additional evidence/feedback.
    predicted_state = predicted_state_with_uncertainty(
        belief
    )

    results.append({
        "case_id": index + 1,
        "true_state": case["true_state"],
        "predicted_state": predicted_state,

        "initial_action": initial_action,
        "final_action": final_action,

        # Keep this because older evaluation code
        # expects a column called "action".
        "action": final_action,

        "selected_evidence": evidence,
        "feedback": feedback,

        "normal_prob": belief["normal"],
        "expected_pattern_prob": belief["expected_pattern"],
        "legitimate_growth_prob": belief["legitimate_growth"],
        "cost_incident_prob": belief["cost_incident"],
    })


# --------------------------------------------------
# Save V3 predictions
# --------------------------------------------------

results_df = pd.DataFrame(results)

v3_file = results_path / "predictions_v3.csv"

results_df.to_csv(
    v3_file,
    index=False
)

print("\nV3 predictions saved.")


# --------------------------------------------------
# Decision cost evaluation
# --------------------------------------------------

def calculate_decision_cost(file_path):

    df = pd.read_csv(file_path)

    df["decision_cost"] = df.apply(
        lambda row: decision_cost(
            row["true_state"],
            row["action"]
        ),
        axis=1
    )

    total_cost = df["decision_cost"].sum()
    average_cost = df["decision_cost"].mean()

    print(f"\n{file_path.name}")
    print("Total decision cost:", total_cost)
    print("Average decision cost:", average_cost)

    return total_cost, average_cost


def calculate_v3_trajectory_cost(file_path):

    df = pd.read_csv(file_path)

    # Cost of the final decision only
    df["final_decision_cost"] = df.apply(
        lambda row: decision_cost(
            row["true_state"],
            row["final_action"]
        ),
        axis=1
    )

    # Cost of collecting evidence
    df["evidence_cost"] = df["selected_evidence"].apply(
        lambda evidence: evidence_cost(evidence)
        if pd.notna(evidence)
        else 0
    )

    # Total V3 trajectory cost
    df["trajectory_cost"] = df.apply(
        lambda row: trajectory_cost(
            row["true_state"],
            row["final_action"],
            row["selected_evidence"]
            if pd.notna(row["selected_evidence"])
            else None
        ),
        axis=1
    )

    total_cost = df["trajectory_cost"].sum()
    average_cost = df["trajectory_cost"].mean()

    print(f"\n{file_path.name}")
    print("Total trajectory cost:", total_cost)
    print("Average trajectory cost:", average_cost)
    print(
        "Final decision cost:",
        df["final_decision_cost"].sum()
    )
    print(
        "Evidence collection cost:",
        df["evidence_cost"].sum()
    )

    return total_cost, average_cost


# --------------------------------------------------
# Cost comparison
# --------------------------------------------------

print("\n----------------------------")
print("COST COMPARISON")
print("----------------------------")

calculate_decision_cost(
    results_path / "predictionsv1_on_v2.csv"
)

calculate_decision_cost(
    results_path / "predictions_v2.csv"
)

calculate_v3_trajectory_cost(
    results_path / "predictions_v3.csv"
)


# --------------------------------------------------
# Top 5 highest-cost V3 cases
# --------------------------------------------------

v3_analysis = pd.read_csv(
    results_path / "predictions_v3.csv"
)

v3_analysis["trajectory_cost"] = v3_analysis.apply(
    lambda row: trajectory_cost(
        row["true_state"],
        row["final_action"],
        row["selected_evidence"]
        if pd.notna(row["selected_evidence"])
        else None
    ),
    axis=1
)

highest_cost_cases = v3_analysis.sort_values(
    "trajectory_cost",
    ascending=False
).head(5)

print("\n----------------------------")
print("TOP 5 HIGHEST-COST V3 CASES")
print("----------------------------")

print(
    highest_cost_cases[
        [
            "case_id",
            "true_state",
            "predicted_state",
            "initial_action",
            "selected_evidence",
            "feedback",
            "final_action",
            "cost_incident_prob",
            "trajectory_cost"
        ]
    ].to_string(index=False)
)


# --------------------------------------------------
# V3 evidence usage
# --------------------------------------------------

print("\n----------------------------")
print("V3 EVIDENCE USAGE")
print("----------------------------")

print("\nEvidence selected across ALL cases:")

print(
    results_df["selected_evidence"]
    .dropna()
    .value_counts()
)

print("\nEvidence by true state:")

print(
    results_df[
        results_df["selected_evidence"].notna()
    ].groupby(
        ["true_state", "selected_evidence"]
    ).size()
)


# --------------------------------------------------
# Evidence effectiveness
# --------------------------------------------------

evidence_cases = results_df[
    results_df["selected_evidence"].notna()
].copy()

evidence_cases["action_changed"] = (
    evidence_cases["initial_action"]
    != evidence_cases["final_action"]
)

print("\n----------------------------")
print("V3 EVIDENCE EFFECTIVENESS")
print("----------------------------")

print(
    "\nTotal evidence checks:",
    len(evidence_cases)
)

print("\nDid evidence change the action?")

print(
    evidence_cases[
        "action_changed"
    ].value_counts()
)

print("\nAction transitions:")

print(
    evidence_cases.groupby(
        [
            "initial_action",
            "final_action"
        ]
    ).size()
)


# --------------------------------------------------
# Evidence value
# --------------------------------------------------

evidence_value = evidence_cases.copy()

evidence_value["initial_decision_cost"] = evidence_value.apply(
    lambda row: decision_cost(
        row["true_state"],
        row["initial_action"]
    ),
    axis=1
)

evidence_value["final_decision_cost"] = evidence_value.apply(
    lambda row: decision_cost(
        row["true_state"],
        row["final_action"]
    ),
    axis=1
)

evidence_value["decision_improvement"] = (
    evidence_value["initial_decision_cost"]
    - evidence_value["final_decision_cost"]
)

evidence_value["collection_cost"] = evidence_value[
    "selected_evidence"
].apply(
    evidence_cost
)

evidence_value["net_value"] = (
    evidence_value["decision_improvement"]
    - evidence_value["collection_cost"]
)

print("\n----------------------------")
print("V3 EVIDENCE VALUE")
print("----------------------------")

print(
    evidence_value.groupby(
        "selected_evidence"
    ).agg(
        checks=("case_id", "count"),
        decision_improvement=(
            "decision_improvement",
            "sum"
        ),
        collection_cost=(
            "collection_cost",
            "sum"
        ),
        net_value=(
            "net_value",
            "sum"
        )
    )
)


# --------------------------------------------------
# No-change evidence cases
# --------------------------------------------------

no_change = evidence_cases[
    evidence_cases["action_changed"] == False
]

print("\n----------------------------")
print("V3 NO-CHANGE EVIDENCE CASES")
print("----------------------------")

print("\nBy evidence type:")

print(
    no_change[
        "selected_evidence"
    ].value_counts()
)

print("\nBy true state:")

print(
    no_change[
        "true_state"
    ].value_counts()
)

print("\nEvidence + true state:")

print(
    no_change.groupby(
        [
            "true_state",
            "selected_evidence"
        ]
    ).size()
)


# --------------------------------------------------
# V3 uncertainty analysis
# --------------------------------------------------

uncertain = results_df[
    results_df["predicted_state"] == "uncertain"
]

print("\n----------------------------")
print("V3 UNCERTAINTY ANALYSIS")
print("----------------------------")

print(
    "\nTotal uncertain cases:",
    len(uncertain)
)

print("\nActions:")

print(
    uncertain[
        "action"
    ].value_counts()
)

print("\nTrue states:")

print(
    uncertain[
        "true_state"
    ].value_counts()
)

print("\nSelected evidence:")

print(
    uncertain[
        "selected_evidence"
    ]
    .dropna()
    .value_counts()
)


# --------------------------------------------------
# Uncertain real cost incidents
# --------------------------------------------------

uncertain_incident = uncertain[
    uncertain["true_state"] == "cost_incident"
]

print("\nUncertain true cost incidents:")

if len(uncertain_incident) > 0:

    print(
        uncertain_incident[
            [
                "case_id",
                "true_state",
                "predicted_state",
                "action",
                "selected_evidence",
                "feedback",
                "cost_incident_prob"
            ]
        ].to_string(index=False)
    )

else:

    print("None")


# --------------------------------------------------
# Uncertain WAIT cases
# --------------------------------------------------

uncertain_wait = uncertain[
    uncertain["action"] == "WAIT"
]

print("\nUncertain cases where agent chose WAIT:")

if len(uncertain_wait) > 0:

    print(
        uncertain_wait[
            [
                "case_id",
                "true_state",
                "predicted_state",
                "action",
                "cost_incident_prob"
            ]
        ].to_string(index=False)
    )

else:

    print("None")

print("\n----------------------------")
print("DETAILS FOR CASE 38 AND CASE 14")
print("----------------------------")

cases_to_inspect = df.iloc[[37, 13]]

print(
    cases_to_inspect[
        [
            "current_cost",
            "baseline_cost",
            "current_usage",
            "baseline_usage",
            "recent_deployment",
            "matches_historical_pattern",
            "environment",
            "service_type",
            "true_state"
        ]
    ].to_string()
)

print("\n----------------------------")
print("ADDITIONAL FAILURE CANDIDATES")
print("----------------------------")

failure_candidates = v3_analysis[
    (
        (v3_analysis["predicted_state"] != v3_analysis["true_state"])
        |
        (v3_analysis["final_action"] == "GET_MORE_EVIDENCE")
    )
    &
    (~v3_analysis["case_id"].isin([14, 38]))
].copy()

failure_candidates = failure_candidates.sort_values(
    "trajectory_cost",
    ascending=False
).head(5)

print(
    failure_candidates[
        [
            "case_id",
            "true_state",
            "predicted_state",
            "initial_action",
            "selected_evidence",
            "feedback",
            "final_action",
            "cost_incident_prob",
            "trajectory_cost"
        ]
    ].to_string(index=False)
)

print("\n----------------------------")
print("DETAILS FOR CASES 6, 34, AND 2")
print("----------------------------")

cases_to_inspect = df.iloc[[5, 33, 1]]

print(
    cases_to_inspect[
        [
            "current_cost",
            "baseline_cost",
            "current_usage",
            "baseline_usage",
            "recent_deployment",
            "matches_historical_pattern",
            "environment",
            "service_type",
            "true_state"
        ]
    ].to_string()
)

print("\n----------------------------")
print("CASE 34 AFTER FEEDBACK FIX")
print("----------------------------")

print(
    v3_analysis[
        v3_analysis["case_id"] == 34
    ][
        [
            "case_id",
            "true_state",
            "predicted_state",
            "initial_action",
            "selected_evidence",
            "feedback",
            "final_action",
            "cost_incident_prob",
            "trajectory_cost"
        ]
    ].to_string(index=False)
)