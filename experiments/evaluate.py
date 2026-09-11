from pathlib import Path
import sys
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.metrics import brier_score_loss

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

from src.belief import (
    predicted_state_with_uncertainty,
    prior_belief,
    update_historical_pattern,
    update_cost_usage,
    update_deployment,
)

from src.features import (
    cost_change,
    usage_change,
)

from src.cost import (
    decision_cost,
    trajectory_cost,
    evidence_cost,
)

from src.information import (
    information_gain,
    information_gain_per_cost,
)


# --------------------------------------------------
# Load test data
# --------------------------------------------------

df = pd.read_csv(
    data_path / "test_cases_v2.csv"
)


# --------------------------------------------------
# Helper: reconstruct belief BEFORE extra evidence
# --------------------------------------------------

def build_initial_belief(case):

    belief = update_historical_pattern(
        prior_belief,
        case["matches_historical_pattern"]
    )

    belief = update_cost_usage(
        belief,
        cost_change(case),
        usage_change(case)
    )

    belief = update_deployment(
        belief,
        case["recent_deployment"]
    )

    return belief


# ==================================================
# RUN V3
# ==================================================

results = []

for index, row in df.iterrows():

    case = row.to_dict()

    (
        belief,
        initial_action,
        final_action,
        evidence,
        feedback
    ) = run_agent(
        case,
        version="v3"
    )

    predicted_state = predicted_state_with_uncertainty(
        belief
    )

    results.append({
        "case_id": index + 1,
        "true_state": case["true_state"],
        "predicted_state": predicted_state,

        "initial_action": initial_action,
        "final_action": final_action,

        # Kept for compatibility with older evaluation code
        "action": final_action,

        "selected_evidence": evidence,
        "feedback": feedback,

        "normal_prob": belief["normal"],
        "expected_pattern_prob": belief["expected_pattern"],
        "legitimate_growth_prob": belief["legitimate_growth"],
        "cost_incident_prob": belief["cost_incident"],
    })


results_df = pd.DataFrame(results)

v3_file = results_path / "predictions_v3.csv"

results_df.to_csv(
    v3_file,
    index=False
)

print("\nV3 predictions saved.")


# ==================================================
# RUN V4 — INFORMATION GAIN
# ==================================================

v4_results = []

for index, row in df.iterrows():

    case = row.to_dict()

    (
        belief,
        initial_action,
        final_action,
        evidence,
        feedback
    ) = run_agent(
        case,
        version="v4"
    )

    predicted_state = predicted_state_with_uncertainty(
        belief
    )

    v4_results.append({
        "case_id": index + 1,
        "true_state": case["true_state"],
        "predicted_state": predicted_state,

        "initial_action": initial_action,
        "final_action": final_action,
        "action": final_action,

        "selected_evidence": evidence,
        "feedback": feedback,

        "normal_prob": belief["normal"],
        "expected_pattern_prob": belief["expected_pattern"],
        "legitimate_growth_prob": belief["legitimate_growth"],
        "cost_incident_prob": belief["cost_incident"],
    })


v4_results_df = pd.DataFrame(v4_results)

v4_file = results_path / "predictions_v4.csv"

v4_results_df.to_csv(
    v4_file,
    index=False
)

print("V4 predictions saved.")


# ==================================================
# COST EVALUATION
# ==================================================

def calculate_decision_cost(file_path):

    data = pd.read_csv(file_path)

    data["decision_cost"] = data.apply(
        lambda row: decision_cost(
            row["true_state"],
            row["action"]
        ),
        axis=1
    )

    total_cost = data["decision_cost"].sum()
    average_cost = data["decision_cost"].mean()

    print(f"\n{file_path.name}")
    print("Total decision cost:", total_cost)
    print("Average decision cost:", average_cost)

    return total_cost, average_cost


def calculate_trajectory_cost(file_path):

    data = pd.read_csv(file_path)

    # Final decision cost
    data["final_decision_cost"] = data.apply(
        lambda row: decision_cost(
            row["true_state"],
            row["final_action"]
        ),
        axis=1
    )

    # Evidence cost
    data["evidence_cost"] = data[
        "selected_evidence"
    ].apply(
        lambda selected:
            evidence_cost(selected)
            if pd.notna(selected)
            else 0
    )

    # Total trajectory cost
    data["trajectory_cost"] = data.apply(
        lambda row: trajectory_cost(
            row["true_state"],
            row["final_action"],
            row["selected_evidence"]
            if pd.notna(row["selected_evidence"])
            else None
        ),
        axis=1
    )

    total_cost = data["trajectory_cost"].sum()
    average_cost = data["trajectory_cost"].mean()

    print(f"\n{file_path.name}")
    print("Total trajectory cost:", total_cost)
    print("Average trajectory cost:", average_cost)

    print(
        "Final decision cost:",
        data["final_decision_cost"].sum()
    )

    print(
        "Evidence collection cost:",
        data["evidence_cost"].sum()
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

print("\nV3 — Heuristic Evidence Selection")

calculate_trajectory_cost(
    results_path / "predictions_v3.csv"
)

print("\nV4 — Information Gain Evidence Selection")

calculate_trajectory_cost(
    results_path / "predictions_v4.csv"
)


# ==================================================
# TOP 5 HIGHEST-COST V3 CASES
# ==================================================

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
            "trajectory_cost",
        ]
    ].to_string(index=False)
)


# ==================================================
# V3 EVIDENCE USAGE
# ==================================================

print("\n----------------------------")
print("V3 EVIDENCE USAGE")
print("----------------------------")

print("\nEvidence selected across ALL cases:")

print(
    results_df[
        "selected_evidence"
    ]
    .dropna()
    .value_counts()
)

print("\nEvidence by true state:")

print(
    results_df[
        results_df["selected_evidence"].notna()
    ]
    .groupby(
        [
            "true_state",
            "selected_evidence"
        ]
    )
    .size()
)


# ==================================================
# V3 EVIDENCE EFFECTIVENESS
# ==================================================

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


# ==================================================
# V3 EVIDENCE VALUE
# ==================================================

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
        checks=(
            "case_id",
            "count"
        ),
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


# ==================================================
# V3 NO-CHANGE EVIDENCE CASES
# ==================================================

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


# ==================================================
# V3 UNCERTAINTY ANALYSIS
# ==================================================

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
# Uncertain real incidents
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
                "cost_incident_prob",
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
                "cost_incident_prob",
            ]
        ].to_string(index=False)
    )

else:

    print("None")


# ==================================================
# DETAILS FOR CASE 38 AND CASE 14
# ==================================================

print("\n----------------------------")
print("DETAILS FOR CASE 38 AND CASE 14")
print("----------------------------")

cases_to_inspect = df.iloc[
    [37, 13]
]

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
            "true_state",
        ]
    ].to_string()
)


# ==================================================
# ADDITIONAL FAILURE CANDIDATES
# ==================================================

print("\n----------------------------")
print("ADDITIONAL FAILURE CANDIDATES")
print("----------------------------")

failure_candidates = v3_analysis[
    (
        (
            v3_analysis["predicted_state"]
            != v3_analysis["true_state"]
        )
        |
        (
            v3_analysis["final_action"]
            == "GET_MORE_EVIDENCE"
        )
    )
    &
    (
        ~v3_analysis[
            "case_id"
        ].isin(
            [14, 38]
        )
    )
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
            "trajectory_cost",
        ]
    ].to_string(index=False)
)


# ==================================================
# DETAILS FOR CASES 6, 34, AND 2
# ==================================================

print("\n----------------------------")
print("DETAILS FOR CASES 6, 34, AND 2")
print("----------------------------")

cases_to_inspect = df.iloc[
    [5, 33, 1]
]

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
            "true_state",
        ]
    ].to_string()
)


# ==================================================
# CASE 34 AFTER FEEDBACK FIX
# ==================================================

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
            "trajectory_cost",
        ]
    ].to_string(index=False)
)


# ==================================================
# V4 SINGLE CASE TEST — CASE 14
# ==================================================

print("\n----------------------------")
print("V4 SINGLE CASE TEST")
print("----------------------------")

v4_test_case = df.iloc[13].to_dict()

(
    v4_test_belief,
    v4_test_initial_action,
    v4_test_final_action,
    v4_test_evidence,
    v4_test_feedback
) = run_agent(
    v4_test_case,
    version="v4"
)

print(
    "True state:",
    v4_test_case["true_state"]
)

print(
    "Initial action:",
    v4_test_initial_action
)

print(
    "Selected evidence:",
    v4_test_evidence
)

print(
    "Feedback:",
    v4_test_feedback
)

print(
    "Final belief:",
    v4_test_belief
)

print(
    "Final action:",
    v4_test_final_action
)


# ==================================================
# COMPARE V3 VS V4 EVIDENCE SELECTION
# ==================================================

v3_compare = pd.read_csv(
    results_path / "predictions_v3.csv"
)

v4_compare = pd.read_csv(
    results_path / "predictions_v4.csv"
)

comparison = v3_compare.merge(
    v4_compare,
    on="case_id",
    suffixes=("_v3", "_v4")
)

comparison["evidence_v3"] = (
    comparison[
        "selected_evidence_v3"
    ].fillna(
        "NONE"
    )
)

comparison["evidence_v4"] = (
    comparison[
        "selected_evidence_v4"
    ].fillna(
        "NONE"
    )
)

different_evidence = comparison[
    comparison["evidence_v3"]
    != comparison["evidence_v4"]
]

print("\n----------------------------")
print("V3 VS V4 EVIDENCE DIFFERENCES")
print("----------------------------")

print(
    "Cases with different evidence:",
    len(different_evidence)
)

if len(different_evidence) > 0:

    print(
        different_evidence[
            [
                "case_id",
                "true_state_v3",
                "evidence_v3",
                "evidence_v4",
                "final_action_v3",
                "final_action_v4",
            ]
        ].to_string(index=False)
    )

else:

    print("No evidence-selection differences.")


print("\nV4 evidence usage:")

print(
    v4_results_df[
        "selected_evidence"
    ]
    .dropna()
    .value_counts()
)


# ==================================================
# V4 INFORMATION GAIN DETAILS
# ==================================================

print("\n----------------------------")
print("V4 INFORMATION GAIN DETAILS")
print("----------------------------")

for case_number in [
    14,
    37
]:

    # IMPORTANT:
    # Use a separate variable so we do not overwrite
    # another case used elsewhere in the evaluation.
    ig_case = df.iloc[
        case_number - 1
    ].to_dict()

    # Reconstruct belief BEFORE additional evidence
    ig_belief = build_initial_belief(
        ig_case
    )

    print(
        f"\nCase {case_number}"
    )

    print(
        "True state:",
        ig_case["true_state"]
    )

    print(
        "Recent deployment:",
        ig_case["recent_deployment"]
    )

    print(
        "Initial belief:",
        ig_belief
    )

    evidence_options = [
        "CHECK_SERVICE_BREAKDOWN"
    ]

    # Deployment evidence only exists when
    # a recent deployment occurred.
    if ig_case["recent_deployment"]:

        evidence_options.append(
            "CHECK_DEPLOYMENT_DETAILS"
        )

    for evidence_option in evidence_options:

        ig = information_gain(
            ig_belief,
            evidence_option
        )

        ig_per_cost = information_gain_per_cost(
            ig_belief,
            evidence_option
        )

        print(
            evidence_option,
            "| IG:",
            ig,
            "| IG/cost:",
            ig_per_cost
        )

# ==================================================
# V4 CONFUSION MATRIX
# ==================================================

print("\n----------------------------")
print("V4 CONFUSION MATRIX")
print("----------------------------")

v4_confusion = pd.crosstab(
    v4_results_df["true_state"],
    v4_results_df["predicted_state"],
    rownames=["True State"],
    colnames=["Predicted State"]
)

print(v4_confusion)

# ==================================================
# V4 PRECISION / RECALL / F1
# ==================================================

print("\n----------------------------")
print("V4 CLASSIFICATION REPORT")
print("----------------------------")

hidden_states = [
    "normal",
    "expected_pattern",
    "legitimate_growth",
    "cost_incident"
]

report = classification_report(
    v4_results_df["true_state"],
    v4_results_df["predicted_state"],
    labels=hidden_states,
    zero_division=0
)

print(report)

uncertain_count = (
    v4_results_df["predicted_state"] == "uncertain"
).sum()

uncertain_rate = uncertain_count / len(v4_results_df)

print("Uncertain cases:", uncertain_count)
print("Uncertain rate:", uncertain_rate)

# ==================================================
# V4 COST-INCIDENT ERROR ANALYSIS
# ==================================================

print("\n----------------------------")
print("V4 COST INCIDENT ERROR ANALYSIS")
print("----------------------------")

true_incident = (
    v4_results_df["true_state"] == "cost_incident"
)

predicted_incident = (
    v4_results_df["predicted_state"] == "cost_incident"
)

true_positive = (
    true_incident & predicted_incident
).sum()

false_positive = (
    ~true_incident & predicted_incident
).sum()

false_negative = (
    true_incident & ~predicted_incident
).sum()

true_negative = (
    ~true_incident & ~predicted_incident
).sum()

print("True Positives:", true_positive)
print("False Positives:", false_positive)
print("False Negatives:", false_negative)
print("True Negatives:", true_negative)

# ==================================================
# V4 ACTION ANALYSIS
# ==================================================

print("\n----------------------------")
print("V4 ACTION ANALYSIS")
print("----------------------------")

action_table = pd.crosstab(
    v4_results_df["true_state"],
    v4_results_df["final_action"],
    rownames=["True State"],
    colnames=["Final Action"]
)

print(action_table)

# ==================================================
# V4 OPERATIONAL METRICS
# ==================================================

print("\n----------------------------")
print("V4 OPERATIONAL METRICS")
print("----------------------------")

incident_cases = v4_results_df[
    v4_results_df["true_state"] == "cost_incident"
]

non_incident_cases = v4_results_df[
    v4_results_df["true_state"] != "cost_incident"
]


# Real incidents incorrectly left at WAIT
unsafe_waits = (
    incident_cases["final_action"] == "WAIT"
).sum()


# Real incidents receiving intervention
incident_interventions = (
    incident_cases["final_action"].isin(
        ["ASK_HUMAN", "ESCALATE"]
    )
).sum()


# Non-incidents that were still investigated/reviewed/escalated
unnecessary_actions = (
    non_incident_cases["final_action"] != "WAIT"
).sum()


# Human review usage
human_reviews = (
    v4_results_df["final_action"] == "ASK_HUMAN"
).sum()


# Escalations
escalations = (
    v4_results_df["final_action"] == "ESCALATE"
).sum()


print(
    "Unsafe WAITs on incidents:",
    unsafe_waits
)

print(
    "Incident intervention rate:",
    incident_interventions / len(incident_cases)
)

print(
    "Unnecessary action rate on non-incidents:",
    unnecessary_actions / len(non_incident_cases)
)

print(
    "Human review rate:",
    human_reviews / len(v4_results_df)
)

print(
    "Escalation rate:",
    escalations / len(v4_results_df)
)

# ==================================================
# V4 PROBABILITY CALIBRATION
# ==================================================

print("\n----------------------------")
print("V4 PROBABILITY CALIBRATION")
print("----------------------------")

actual_incident = (
    v4_results_df["true_state"] == "cost_incident"
).astype(int)

predicted_incident_probability = (
    v4_results_df["cost_incident_prob"]
)

brier_score = brier_score_loss(
    actual_incident,
    predicted_incident_probability
)

print("Brier score:", brier_score)

print(
    "Average predicted incident probability:",
    predicted_incident_probability.mean()
)

print(
    "Actual incident rate:",
    actual_incident.mean()
)

# ==================================================
# V4 CALIBRATION BINS
# ==================================================

print("\n----------------------------")
print("V4 CALIBRATION BINS")
print("----------------------------")

calibration_df = pd.DataFrame({
    "predicted_probability": predicted_incident_probability,
    "actual_incident": actual_incident
})

calibration_df["probability_bin"] = pd.cut(
    calibration_df["predicted_probability"],
    bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    include_lowest=True
)

calibration_summary = calibration_df.groupby(
    "probability_bin",
    observed=False
).agg(
    cases=("actual_incident", "count"),
    avg_predicted_probability=("predicted_probability", "mean"),
    actual_incident_rate=("actual_incident", "mean")
)

print(calibration_summary)

# ==================================================
# V4 EXPECTED CALIBRATION ERROR
# ==================================================

print("\n----------------------------")
print("V4 EXPECTED CALIBRATION ERROR")
print("----------------------------")

total_cases = len(calibration_df)

ece = 0.0

for _, row in calibration_summary.dropna().iterrows():
    weight = row["cases"] / total_cases

    calibration_gap = abs(
        row["avg_predicted_probability"]
        - row["actual_incident_rate"]
    )

    ece += weight * calibration_gap

print("Expected Calibration Error:", ece)

# ==================================================
# END
# ==================================================

print("\n----------------------------")
print("EVALUATION COMPLETE")
print("----------------------------")
