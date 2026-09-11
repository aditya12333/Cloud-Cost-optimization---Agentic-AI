import math

from belief import update_from_feedback
from cost import evidence_cost


# --------------------------------------------------
# Shannon entropy
# --------------------------------------------------

def entropy(belief):
    """
    Calculate Shannon entropy of a belief distribution.
    """

    h = 0.0

    for probability in belief.values():

        if probability > 0:
            h -= probability * math.log2(probability)

    return h


# --------------------------------------------------
# Possible evidence outcomes
# --------------------------------------------------

def evidence_outcome_probabilities(belief, evidence):
    """
    Estimate probabilities of possible evidence outcomes
    using the current synthetic evidence model.
    """

    if evidence == "CHECK_SERVICE_BREAKDOWN":

        return {
            "CONCENTRATED_SERVICE_SPIKE":
                belief["cost_incident"],

            "USAGE_ALIGNED_GROWTH":
                belief["legitimate_growth"],

            "NO_CLEAR_SERVICE_CAUSE":
                belief["normal"]
                + belief["expected_pattern"]
        }

    elif evidence == "CHECK_DEPLOYMENT_DETAILS":

        return {
            "COST_RELEVANT_CHANGE_FOUND":
                belief["cost_incident"],

            "NO_COST_RELEVANT_CHANGE":
                belief["normal"]
                + belief["expected_pattern"]
                + belief["legitimate_growth"]
        }

    return {}


# --------------------------------------------------
# Expected posterior entropy
# --------------------------------------------------

def expected_posterior_entropy(belief, evidence):
    """
    Calculate expected uncertainty remaining
    after collecting a piece of evidence.
    """

    outcomes = evidence_outcome_probabilities(
        belief,
        evidence
    )

    expected_entropy = 0.0

    for feedback, outcome_probability in outcomes.items():

        posterior = update_from_feedback(
            belief,
            feedback
        )

        posterior_entropy = entropy(
            posterior
        )

        expected_entropy += (
            outcome_probability
            * posterior_entropy
        )

    return expected_entropy


# --------------------------------------------------
# Information gain
# --------------------------------------------------

def information_gain(belief, evidence):
    """
    Expected reduction in entropy from collecting evidence.
    """

    current_entropy = entropy(
        belief
    )

    future_entropy = expected_posterior_entropy(
        belief,
        evidence
    )

    return current_entropy - future_entropy


# --------------------------------------------------
# Information gain per cost
# --------------------------------------------------

def information_gain_per_cost(belief, evidence):
    """
    Expected information gained per unit
    of evidence-collection cost.
    """

    ig = information_gain(
        belief,
        evidence
    )

    cost = evidence_cost(
        evidence
    )

    if cost == 0:
        return 0

    return ig / cost


# --------------------------------------------------
# Select evidence using information gain
# --------------------------------------------------

def select_evidence_by_information_gain(case, belief):
    """
    Select the available evidence source with the highest
    expected information gain per unit cost.
    """

    evidence_options = [
        "CHECK_SERVICE_BREAKDOWN"
    ]

    # Deployment details are only available if
    # a recent deployment actually occurred.
    if case["recent_deployment"]:

        evidence_options.append(
            "CHECK_DEPLOYMENT_DETAILS"
        )

    scores = {}

    for evidence in evidence_options:

        scores[evidence] = information_gain_per_cost(
            belief,
            evidence
        )

    best_evidence = max(
        scores,
        key=scores.get
    )

    return best_evidence, scores


# --------------------------------------------------
# Tests
# --------------------------------------------------

if __name__ == "__main__":

    belief_1 = {
        "normal": 0.25,
        "expected_pattern": 0.25,
        "legitimate_growth": 0.25,
        "cost_incident": 0.25
    }

    belief_2 = {
        "normal": 0.97,
        "expected_pattern": 0.01,
        "legitimate_growth": 0.01,
        "cost_incident": 0.01
    }

    print(
        "Entropy of uniform belief:",
        entropy(belief_1)
    )

    print(
        "Entropy of confident belief:",
        entropy(belief_2)
    )


    test_belief = {
        "normal": 0.20,
        "expected_pattern": 0.20,
        "legitimate_growth": 0.25,
        "cost_incident": 0.35
    }

    print(
        "\nCurrent entropy:",
        entropy(test_belief)
    )

    print(
        "Expected entropy after service breakdown:",
        expected_posterior_entropy(
            test_belief,
            "CHECK_SERVICE_BREAKDOWN"
        )
    )

    print(
        "Expected entropy after deployment details:",
        expected_posterior_entropy(
            test_belief,
            "CHECK_DEPLOYMENT_DETAILS"
        )
    )

    print(
        "\nInformation gain from service breakdown:",
        information_gain(
            test_belief,
            "CHECK_SERVICE_BREAKDOWN"
        )
    )

    print(
        "Information gain from deployment details:",
        information_gain(
            test_belief,
            "CHECK_DEPLOYMENT_DETAILS"
        )
    )

    print(
        "\nIG per cost - service breakdown:",
        information_gain_per_cost(
            test_belief,
            "CHECK_SERVICE_BREAKDOWN"
        )
    )

    print(
        "IG per cost - deployment details:",
        information_gain_per_cost(
            test_belief,
            "CHECK_DEPLOYMENT_DETAILS"
        )
    )


    test_case = {
        "recent_deployment": True
    }

    best_evidence, scores = (
        select_evidence_by_information_gain(
            test_case,
            test_belief
        )
    )

    print(
        "\nEvidence scores:",
        scores
    )

    print(
        "Best evidence:",
        best_evidence
    )