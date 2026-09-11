from features import cost_change, usage_change
from belief import (
    prior_belief,
    update_historical_pattern,
    update_cost_usage,
    update_deployment,
    update_from_feedback,
)
from policy import select_action, select_action_v2
from evidence import select_evidence
from feedback import simulate_feedback
from information import select_evidence_by_information_gain

def run_agent(case, version="v1"):

    # 1. Calculate observable signals
    cost = cost_change(case)
    usage = usage_change(case)

    # 2. Update belief
    belief = update_historical_pattern(
        prior_belief,
        case["matches_historical_pattern"]
    )

    belief = update_cost_usage(
        belief,
        cost,
        usage
    )

    belief = update_deployment(
        belief,
        case["recent_deployment"]
    )

    # 3. Make initial decision
    if version in ["v2", "v3", "v4"]:
        initial_action = select_action_v2(
            belief,
            case["environment"]
        )
    else:
        initial_action = select_action(belief)

    # By default, final action is the same
    final_action = initial_action

    evidence = None
    feedback = None

    if version in ["v3", "v4"] and initial_action == "GET_MORE_EVIDENCE":

        if version == "v3":

            # Existing heuristic evidence selector
            evidence = select_evidence(
                case,
                belief
            )

        elif version == "v4":

            # Information-gain evidence selector
            evidence, evidence_scores = select_evidence_by_information_gain(
                case,
                belief
            )

        feedback = simulate_feedback(
            case,
            evidence
        )

        belief = update_from_feedback(
            belief,
            feedback
        )

        final_action = select_action_v2(
            belief,
            case["environment"]
        )

    return (
        belief,
        initial_action,
        final_action,
        evidence,
        feedback
)