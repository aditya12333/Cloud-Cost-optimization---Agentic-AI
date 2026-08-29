belief = {
    "normal": 0.20,
    "expected_pattern": 0.10,
    "legitimate_growth": 0.225,
    "cost_incident": 0.475
}

def select_action(belief):
    '''
    < 0.30   → WAIT
    0.30–0.50 → GET_MORE_EVIDENCE
    0.50–0.70 → ASK_HUMAN
    > 0.70   → ESCALATE
    '''
    if belief["cost_incident"] < 0.30:
        return "WAIT"
    elif 0.30 <= belief["cost_incident"] < 0.50:
        return "GET_MORE_EVIDENCE"
    elif 0.50 <= belief["cost_incident"] < 0.70:
        return "ASK_HUMAN"
    else:
        return "ESCALATE"

def select_action_v2(belief, environment):
    """
    Select an action using incident probability and environment.

    Production uses lower thresholds because an incorrect decision
    may have a higher operational/business cost.

    Development uses higher thresholds because small anomalies may
    be less urgent.

    These thresholds are V2 assumptions and should be tested.
    """

    incident_prob = belief["cost_incident"]

    if environment == "production":

        if incident_prob < 0.25:
            return "WAIT"
        elif incident_prob < 0.45:
            return "GET_MORE_EVIDENCE"
        elif incident_prob < 0.65:
            return "ASK_HUMAN"
        else:
            return "ESCALATE"

    elif environment == "development":

        if incident_prob < 0.35:
            return "WAIT"
        elif incident_prob < 0.55:
            return "GET_MORE_EVIDENCE"
        elif incident_prob < 0.75:
            return "ASK_HUMAN"
        else:
            return "ESCALATE"

    else:
        # Fallback to original V1 thresholds
        return select_action(belief)

# action = select_action(belief)
# print(action)  # Output: GET_MORE_EVIDENCE