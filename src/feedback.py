def simulate_feedback(case, selected_evidence):

    """
    Synthetic evaluation only.

    true_state is used by the simulator to generate
    the result of collecting evidence.

    The agent never receives true_state directly.
    """

    true_state = case["true_state"]

    if selected_evidence == "CHECK_SERVICE_BREAKDOWN":

        if true_state == "cost_incident":
            return "CONCENTRATED_SERVICE_SPIKE"

        elif true_state == "legitimate_growth":
            return "USAGE_ALIGNED_GROWTH"

        else:
            return "NO_CLEAR_SERVICE_CAUSE"


    elif selected_evidence == "CHECK_DEPLOYMENT_DETAILS":

        if true_state == "cost_incident":
            return "COST_RELEVANT_CHANGE_FOUND"

        else:
            return "NO_COST_RELEVANT_CHANGE"


    return None