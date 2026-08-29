COST_MATRIX = {
    "normal": {
        "WAIT": 0,
        "GET_MORE_EVIDENCE": 1,
        "ASK_HUMAN": 2,
        "ESCALATE": 4
    },

    "expected_pattern": {
        "WAIT": 0,
        "GET_MORE_EVIDENCE": 1,
        "ASK_HUMAN": 2,
        "ESCALATE": 4
    },

    "legitimate_growth": {
        "WAIT": 0,
        "GET_MORE_EVIDENCE": 1,
        "ASK_HUMAN": 2,
        "ESCALATE": 4
    },

    "cost_incident": {
        "WAIT": 10,
        "GET_MORE_EVIDENCE": 2,
        "ASK_HUMAN": 1,
        "ESCALATE": 0
    }
}


def decision_cost(true_state, action):
    return COST_MATRIX[true_state][action]


EVIDENCE_COST = {
    "CHECK_HISTORY": 1,
    "CHECK_SERVICE_BREAKDOWN": 2,
    "CHECK_DEPLOYMENT_DETAILS": 2
}


def evidence_cost(selected_evidence):

    if selected_evidence is None:
        return 0

    return EVIDENCE_COST.get(selected_evidence, 0)


def trajectory_cost(true_state, final_action, selected_evidence=None):

    final_cost = decision_cost(
        true_state,
        final_action
    )

    investigation_cost = evidence_cost(
        selected_evidence
    )

    return final_cost + investigation_cost