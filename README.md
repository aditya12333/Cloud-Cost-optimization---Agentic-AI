# Cloud Cost Decision Agent

An AI-native decision agent for reasoning about unusual cloud-cost behaviour under uncertainty.

Rather than using a simple rule such as:

> "Cost increased by 30% → send an alert"

the system maintains a belief over possible explanations, decides whether enough evidence exists to act, requests additional evidence when necessary, and accounts for the cost of unnecessary investigation or delayed incident response.

The project is being developed incrementally:

- **V1** — belief-based decision agent
- **V2** — environment-aware decision policy
- **V3** — active evidence gathering and feedback loop
- **Next phase** — validation on real FinOps cloud billing data

---

## Problem

Cloud-cost increases are not automatically incidents.

A cost increase could represent:

- normal variation,
- a recurring historical pattern,
- legitimate business growth,
- or an actual cost incident.

A simple threshold-based alerting system cannot distinguish between these explanations.

The agent therefore answers a more useful question:

> Given the evidence currently available, should we wait, investigate further, ask a human, or escalate?

---

## Agent Design

The system is modelled around six components:

```text
Observations
     ↓
Belief over hidden states
     ↓
Decision policy
     ↓
Action
     ↓
Optional evidence collection
     ↓
Feedback
     ↓
Updated belief
     ↓
Final action
```

### Observable Inputs

The controlled experiment currently provides:

- current cloud cost
- historical baseline cost
- current usage
- historical baseline usage
- whether the behaviour matches a historical pattern
- whether a recent deployment occurred
- environment (`production` / `development`)
- service type

The agent also derives:

- percentage cost change
- percentage usage change
- unit cost
- unit-cost change

---

## Hidden States

The actual cause of the cost behaviour is treated as hidden.

The agent maintains a probability distribution over four possible states:

| Hidden State | Meaning |
|---|---|
| `normal` | Ordinary cost variation |
| `expected_pattern` | Cost behaviour matches a known recurring pattern |
| `legitimate_growth` | Cost increased because usage/business activity increased |
| `cost_incident` | Cost increased unexpectedly and may require intervention |

Example initial belief:

```python
{
    "normal": 0.25,
    "expected_pattern": 0.25,
    "legitimate_growth": 0.25,
    "cost_incident": 0.25
}
```

The agent never receives the hidden state while making its decision.

The hidden label is used only for offline evaluation.

---

## Available Actions

The agent can choose between four operational actions:

| Action | Meaning |
|---|---|
| `WAIT` | Take no intervention and continue monitoring |
| `GET_MORE_EVIDENCE` | Investigate before making a stronger decision |
| `ASK_HUMAN` | Send the case for human review |
| `ESCALATE` | Treat the situation as a high-confidence cost incident |

`WAIT` does not mean ignoring the event permanently.

In a production system it would mean:

```text
Record decision
      ↓
Take no corrective action
      ↓
Continue monitoring
      ↓
Evaluate again later
```

---

# Version 1 — Belief-Based Decision Agent

V1 introduced the basic reasoning architecture.

Instead of making a decision directly from cost change, the agent first updates its belief about the hidden cause.

## Initial Belief

The system begins with an equal prior:

```text
normal               25%
expected_pattern     25%
legitimate_growth    25%
cost_incident        25%
```

The belief is then updated using available evidence.

---

## Historical Pattern Evidence

If the current behaviour matches a historical pattern, probability is shifted toward:

```text
expected_pattern
```

If it does not match historical behaviour, probability is moved away from that explanation.

---

## Cost vs Usage Evidence

One of the main signals is whether cost and usage move together.

Example:

```text
Cost:  +45%
Usage:  +5%
```

A large cost increase without a corresponding usage increase provides evidence for:

```text
cost_incident
```

while:

```text
Cost:  +40%
Usage: +35%
```

provides stronger evidence for:

```text
legitimate_growth
```

---

## Deployment Evidence

A recent deployment increases the possibility that an operational change caused the cost increase.

The deployment signal therefore modifies the incident belief.

---

## V1 Policy

V1 makes its action decision using the probability of `cost_incident`.

```text
P(incident) < 0.30
    → WAIT

0.30 ≤ P(incident) < 0.50
    → GET_MORE_EVIDENCE

0.50 ≤ P(incident) < 0.70
    → ASK_HUMAN

P(incident) ≥ 0.70
    → ESCALATE
```

These thresholds are manually defined experimental assumptions rather than learned production thresholds.

---

## Baseline Policy

To evaluate whether probabilistic reasoning added value, I also implemented a simple threshold baseline:

```text
Cost increase > 30%
       ↓
ESCALATE

Otherwise
       ↓
WAIT
```

This baseline is intentionally simple.

It demonstrates the weakness of treating every large cost increase as an incident.

For example, a 40% cost increase caused by a 40% increase in legitimate usage should not necessarily trigger the same response as a 40% cost increase with no usage growth.

---

# Version 2 — Environment-Aware Decision Policy

V1 treated all environments equally.

In practice, however, the operational cost of making the wrong decision differs between environments.

For example:

```text
Production incident
```

may require faster intervention than:

```text
Development cost anomaly
```

V2 therefore separates:

> What does the agent believe?

from:

> How aggressively should the agent act on that belief?

The belief model remains the same.

Only the action policy changes.

---

## Production Policy

```text
P(incident) < 0.25
    → WAIT

0.25 ≤ P(incident) < 0.45
    → GET_MORE_EVIDENCE

0.45 ≤ P(incident) < 0.65
    → ASK_HUMAN

P(incident) ≥ 0.65
    → ESCALATE
```

Production uses lower intervention thresholds because the cost of missing an incident is assumed to be higher.

---

## Development Policy

```text
P(incident) < 0.35
    → WAIT

0.35 ≤ P(incident) < 0.55
    → GET_MORE_EVIDENCE

0.55 ≤ P(incident) < 0.75
    → ASK_HUMAN

P(incident) ≥ 0.75
    → ESCALATE
```

Development is deliberately more conservative about escalation.

This introduces an important architectural distinction:

```text
Belief model
    ↓
"What is probably happening?"

Policy
    ↓
"What should I do about it?"
```

---

# Version 3 — Active Evidence Gathering

The biggest limitation of V1 and V2 was that:

```text
GET_MORE_EVIDENCE
```

was only an action label.

The agent did not actually decide:

> What evidence should I collect?

V3 adds an evidence-gathering loop.

---

## V3 Decision Flow

```text
Initial observations
        ↓
Build belief
        ↓
Initial action
        ↓
Is action GET_MORE_EVIDENCE?
        ↓
       Yes
        ↓
Select evidence
        ↓
Receive feedback
        ↓
Update belief
        ↓
Choose final action
```

This turns the system from a one-shot classifier into a sequential decision process.

---

## Evidence Types

V3 can investigate:

### 1. Service Breakdown

```text
CHECK_SERVICE_BREAKDOWN
```

The purpose is to determine whether the increase is concentrated within a particular cloud service.

Possible feedback includes:

```text
CONCENTRATED_SERVICE_SPIKE
USAGE_ALIGNED_GROWTH
NO_CLEAR_SERVICE_CAUSE
```

---

### 2. Deployment Details

```text
CHECK_DEPLOYMENT_DETAILS
```

The purpose is to investigate whether a recent deployment contains a cost-relevant infrastructure change.

Possible feedback:

```text
COST_RELEVANT_CHANGE_FOUND
NO_COST_RELEVANT_CHANGE
```

---

## Evidence Selection

V3 initially uses a heuristic evidence-selection policy.

For example:

```python
if (
    belief["cost_incident"] >= 0.25
    or belief["legitimate_growth"] >= 0.25
):
    CHECK_SERVICE_BREAKDOWN += 4

if recent_deployment:
    CHECK_DEPLOYMENT_DETAILS += 3
```

Evidence options also have an investigation cost.

```text
CHECK_SERVICE_BREAKDOWN     = 2
CHECK_DEPLOYMENT_DETAILS    = 2
```

The evidence score is divided by its cost before selection.

This is a heuristic value-per-cost approach.

It is **not yet a statistically learned information-value model in V3**.

---

# Feedback-Based Belief Updating

Evidence does not directly determine the answer.

Instead, it changes the belief distribution.

For example:

```text
Initial belief:

cost_incident = 0.375
```

The agent requests:

```text
CHECK_SERVICE_BREAKDOWN
```

and receives:

```text
CONCENTRATED_SERVICE_SPIKE
```

The incident probability increases.

The updated belief is then passed through the action policy again.

This allows the system to move through trajectories such as:

```text
GET_MORE_EVIDENCE
       ↓
CHECK_SERVICE_BREAKDOWN
       ↓
CONCENTRATED_SERVICE_SPIKE
       ↓
ASK_HUMAN
```

rather than treating investigation as the end of the decision.

---

# Uncertainty Handling

The system also distinguishes between:

```text
confident prediction
```

and:

```text
uncertain prediction
```

The two highest hidden-state probabilities are compared.

If their difference is smaller than a tolerance:

```text
top_probability - second_probability < 0.02
```

the predicted state becomes:

```text
uncertain
```

`uncertain` is not a fifth hidden state.

It represents the agent choosing not to confidently commit to one explanation.

This is useful because:

> An agent recognising uncertainty can be safer than an agent confidently selecting the wrong explanation.

---

# Decision Cost

Evaluation is not based only on classification accuracy.

Different mistakes have different operational consequences.

For example:

```text
True state = cost_incident
Action     = WAIT
```

is much more costly than:

```text
True state = normal
Action     = GET_MORE_EVIDENCE
```

The project therefore uses a decision-cost matrix.

| True State | WAIT | GET_MORE_EVIDENCE | ASK_HUMAN | ESCALATE |
|---|---:|---:|---:|---:|
| normal | 0 | 1 | 2 | 4 |
| expected_pattern | 0 | 1 | 2 | 4 |
| legitimate_growth | 0 | 1 | 2 | 4 |
| cost_incident | 10 | 2 | 1 | 0 |

These are relative experimental costs, not monetary values.

Their purpose is to represent the asymmetric consequences of different actions.

---

# Evidence Cost

Investigation is also not free.

V3 therefore includes evidence-collection cost:

| Evidence | Relative Cost |
|---|---:|
| `CHECK_SERVICE_BREAKDOWN` | 2 |
| `CHECK_DEPLOYMENT_DETAILS` | 2 |

The complete V3 trajectory cost is:

```text
Trajectory Cost
    =
Final Decision Cost
    +
Evidence Collection Cost
```

This prevents the agent from appearing successful simply by requesting unlimited investigation.

---

# Controlled Evaluation Dataset

V1–V3 were evaluated on a controlled synthetic benchmark.

The dataset contains:

```text
40 cases
```

with balanced hidden states:

```text
10 normal
10 expected_pattern
10 legitimate_growth
10 cost_incident
```

Each case contains observable information such as:

```text
current_cost
baseline_cost

current_usage
baseline_usage

recent_deployment
matches_historical_pattern

environment
service_type
```

and one hidden evaluation label:

```text
true_state
```

The agent never sees `true_state` during decision making.

Synthetic data was used deliberately because it provides known ground truth and allows controlled evaluation of whether the decision logic behaves as intended.

It should **not** be interpreted as evidence of production performance.

---

# Experimental Results

The same 40 controlled cases were reused across versions to make the comparison consistent.

## Decision Cost

| Version | Decision Cost |
|---|---:|
| V1 | 34 |
| V2 | 32 |
| V3 final decisions | **12** |

V2 reduced decision cost by introducing environment-sensitive action thresholds.

V3 further improved the quality of the final decisions after additional evidence was incorporated.

However, V3 also pays for evidence collection.

---

## V3 Evidence Cost

```text
Evidence checks performed: 22

Evidence collection cost: 44

Final decision cost: 12

Total trajectory cost: 56
```

Therefore:

```text
12 + 44 = 56
```

This highlights an important result:

> More investigation can improve the final decision while still making the complete decision process more expensive.

This means the agent must learn not only which evidence is useful, but whether the expected value of collecting it justifies its cost.

---

# Evidence Effectiveness

Across the 22 cases where V3 requested additional evidence:

```text
20 / 22
```

resulted in a change to the final action.

Observed transitions included:

```text
GET_MORE_EVIDENCE → ASK_HUMAN
GET_MORE_EVIDENCE → WAIT
GET_MORE_EVIDENCE → GET_MORE_EVIDENCE
```

This demonstrated that feedback was actively influencing decisions rather than simply being logged.

---

# Failure Analysis

An important objective of this project is not only to measure success but also to identify situations where the agent's reasoning fails.

Several useful failure modes emerged.

---

## Failure 1 — Duplicate-Evidence Overconfidence

An earlier V3 design allowed:

```text
CHECK_HISTORY
```

even though:

```text
matches_historical_pattern
```

had already been included in the initial observations.

This caused historical-pattern information to be effectively counted twice.

In one real test case within the synthetic experiment:

```text
true state = cost_incident
```

but repeated historical-pattern evidence pushed the belief toward:

```text
expected_pattern
```

and produced:

```text
WAIT
```

This was a serious failure because the evidence was not independent.

### Fix

`CHECK_HISTORY` was removed from the active evidence selector.

The lesson was:

> Additional evidence is useful only when it provides genuinely new information.

---

## Failure 2 — Post-Confirmation Hesitation

Another case produced:

```text
Cost change  = +34%
Usage change = -2%
Environment  = development
True state   = cost_incident
```

The initial incident belief was:

```text
37.5%
```

The agent selected:

```text
CHECK_SERVICE_BREAKDOWN
```

and received:

```text
CONCENTRATED_SERVICE_SPIKE
```

Incident belief increased to approximately:

```text
52.3%
```

However, the development threshold for `ASK_HUMAN` was:

```text
55%
```

The final action therefore remained:

```text
GET_MORE_EVIDENCE
```

This failure mode was named:

> **Post-confirmation hesitation**

The evidence strongly supported an incident, but the manually selected policy threshold prevented the agent from progressing to human review.

Potential future improvements include:

- calibrated thresholds,
- evidence-sensitive stopping rules,
- learned action policies,
- preventing repeated investigation loops.

---

## Failure 3 — Harmless Hidden-State Misclassification

Not every incorrect hidden-state prediction creates a bad operational decision.

For example, one case had:

```text
True state      = normal
Predicted state = expected_pattern
Final action    = WAIT
Decision cost   = 0
```

The explanation was technically incorrect, but the operational decision was still appropriate.

This illustrates an important principle:

> Classification accuracy and decision quality are not the same metric.

For decision agents, evaluating the consequences of the action can be more meaningful than evaluating state classification alone.

---

# Key Engineering Lessons

Building V1–V3 exposed several important lessons.

### 1. Threshold alerts are not enough

```text
cost spike ≠ automatically an incident
```

Context such as usage growth and historical behaviour matters.

### 2. Belief and policy should be separate

The system should distinguish:

```text
What do I believe is happening?
```

from:

```text
What should I do about it?
```

### 3. Environment changes decision risk

The same belief may justify different actions in production and development.

### 4. Evidence has a cost

Requesting more information can improve decisions but still make the complete system less efficient.

### 5. Evidence must be independent

Reusing information that has already influenced the belief can create artificial confidence.

### 6. Uncertainty should be explicit

Sometimes:

```text
"I am uncertain"
```

is preferable to confidently selecting the wrong explanation.

### 7. Accuracy alone is insufficient

The system should also measure:

- false positives,
- false negatives,
- decision cost,
- investigation cost,
- human-review burden,
- unsafe decisions,
- and complete decision trajectories.

---

# Repository Structure

```text
student_project/
│
├── src/
│   ├── features.py
│   ├── belief.py
│   ├── policy.py
│   ├── evidence.py
│   ├── feedback.py
│   ├── cost.py
│   └── agent.py
│
├── data/
│   └── test_cases_v2.csv
│
├── experiments/
│   └── evaluate.py
│
├── results/
│   ├── predictionsv1_on_v2.csv
│   ├── predictions_v2.csv
│   └── predictions_v3.csv
│
├── probability-decision-record.md
└── README.md
```

---

# Running the Experiment

From the project root:

```bash
python experiments/evaluate.py
```

The evaluation pipeline:

```text
Loads the controlled cases
        ↓
Runs V1
        ↓
Runs V2
        ↓
Runs V3
        ↓
Records beliefs and actions
        ↓
Calculates decision costs
        ↓
Measures evidence usage
        ↓
Identifies high-cost failures
        ↓
Saves prediction outputs
```

---

# Current Limitations

V1–V3 are intentionally experimental.

Current limitations include:

- evaluation uses synthetic rather than production-labelled cloud incidents,
- belief-update weights are manually specified,
- decision thresholds are manually selected,
- evidence feedback is simulated,
- evidence outcomes are deterministic,
- service-specific behaviour is not yet learned,
- long-term seasonal patterns are not yet modelled,
- real deployment metadata is not yet integrated,
- costs are relative decision costs rather than financial estimates.

These limitations are important because the current probabilities should not yet be interpreted as calibrated real-world incident probabilities.

---

# Next Phase — Real Cloud Billing Data

The controlled experiment established the reasoning architecture.

The next phase moves from:

```text
Synthetic observations
        ↓
Known hidden labels
```

to:

```text
Real cloud billing records
        ↓
Historical baselines
        ↓
Observed cost anomalies
        ↓
Agent decisions under real data uncertainty
```

The real-data extension uses anonymized cloud billing data following the **FinOps FOCUS** specification.

The goal is to replace synthetic variables such as:

```text
current_cost
baseline_cost
matches_historical_pattern
```

with quantities calculated directly from historical cloud billing records.

This next phase will test whether the reasoning framework remains useful once the controlled assumptions of the synthetic experiment are removed.

---

## Project Status

```text
V1  Belief-based decision agent               
V2  Environment-aware decision policy         
V3  Evidence gathering + feedback loop        
Real FinOps billing-data integration           
Production-calibrated decision system           Future work
```

---

## Why This Project?

The broader goal is to explore how AI agents can make decisions when:

- the true cause is hidden,
- evidence is incomplete,
- investigation has a cost,
- actions have asymmetric consequences,
- and the system must know when to act versus when to gather more information.

Cloud-cost management provides a practical environment for studying these problems while combining:

- probabilistic reasoning,
- sequential decision making,
- data engineering,
- cost-sensitive evaluation,
- agent design,
- and human-in-the-loop decision systems.
