hidden_states = [
    "normal",
    "expected_pattern",
    "legitimate_growth",
    "cost_incident"
]


prior_belief = {
    "normal": 0.25,
    "expected_pattern": 0.25,
    "legitimate_growth": 0.25,
    "cost_incident": 0.25
}

def update_historical_pattern(belief, matches_historical_pattern):
    """
    Update the belief for the 'expected_pattern' state based on the historical pattern.

    Parameters:
    belief (dict): A dictionary containing the current belief for each state.
    matches_historical_pattern (bool): A boolean indicating whether the current case matches the historical pattern.

    Returns:
    dict: The updated belief for each state.
    """
    belief = belief.copy()
    if matches_historical_pattern:
        belief["expected_pattern"] += 0.1
        belief["normal"] -= 0.05
        belief["legitimate_growth"] -= 0.025
        belief["cost_incident"] -= 0.025
    else:
        belief["expected_pattern"] -= 0.1
        belief["normal"] += 0.05
        belief["legitimate_growth"] += 0.025
        belief["cost_incident"] += 0.025

    # Normalize the beliefs to ensure they sum to 1
    total_belief = sum(belief.values())
    for state in hidden_states:
        belief[state] /= total_belief

    return belief

def update_cost_usage(belief, cost_change, usage_change):
    """
    Update beliefs based on how cost and usage changed.

    Parameters:
    belief (dict): Current belief probabilities.
    cost_change (float): Percentage change in cost.
    usage_change (float): Percentage change in usage.

    Returns:
    dict: Updated belief probabilities.
    """
    belief = belief.copy()

    # Cost rises strongly, but usage does not rise much
    if cost_change > 20 and usage_change < 10:
        belief["cost_incident"] += 0.10
        belief["normal"] -= 0.05
        belief["legitimate_growth"] -= 0.025
        belief["expected_pattern"] -= 0.025

    # Cost and usage both rise strongly
    elif cost_change > 20 and usage_change > 20:
        belief["legitimate_growth"] += 0.10
        belief["normal"] -= 0.05
        belief["expected_pattern"] -= 0.025
        belief["cost_incident"] -= 0.025

    # Cost and usage are both relatively stable
    elif abs(cost_change) <= 10 and abs(usage_change) <= 10:
        belief["normal"] += 0.10
        belief["expected_pattern"] -= 0.025
        belief["legitimate_growth"] -= 0.025
        belief["cost_incident"] -= 0.05

    # Normalize probabilities
    total_belief = sum(belief.values())

    for state in hidden_states:
        belief[state] /= total_belief

    return belief

def update_deployment(belief, recent_deployment):
    belief = belief.copy()

    if recent_deployment:
        belief["cost_incident"] += 0.10
        belief["normal"] -= 0.05
        belief["expected_pattern"] -= 0.025
        belief["legitimate_growth"] -= 0.025

    # if no recent deployment, leave belief unchanged

    total_belief = sum(belief.values())

    for state in hidden_states:
        belief[state] /= total_belief

    return belief

def predicted_state_with_uncertainty(belief, tolerance=0.02):

    ranked = sorted(
        belief.items(),
        key=lambda x: x[1],
        reverse=True
    )

    first_state, first_prob = ranked[0]
    second_state, second_prob = ranked[1]

    if first_prob - second_prob < tolerance:
        return "uncertain"

    return first_state

def update_from_feedback(belief, feedback):
    belief = belief.copy()

    if feedback == "SIMILAR_PATTERN_FOUND":
        belief["expected_pattern"] += 0.20
        belief["cost_incident"] -= 0.10

    elif feedback == "CONCENTRATED_SERVICE_SPIKE":
        belief["cost_incident"] += 0.20
        belief["normal"] -= 0.10

    elif feedback == "USAGE_ALIGNED_GROWTH":
        belief["legitimate_growth"] += 0.20
        belief["cost_incident"] -= 0.10

    elif feedback == "COST_RELEVANT_CHANGE_FOUND":
        belief["cost_incident"] += 0.20
        belief["normal"] -= 0.10

    # normalize
    total = sum(belief.values())

    for state in belief:
        belief[state] /= total

    return belief

# updated = update_expected_pattern(prior_belief, False)
# updated_cost_usage = update_cost_usage(updated, 45, 5)
# updated_deployment = update_deployment(updated_cost_usage, True)

# print(prior_belief)
# print(updated)
# print(updated_cost_usage)
# print(updated_deployment)