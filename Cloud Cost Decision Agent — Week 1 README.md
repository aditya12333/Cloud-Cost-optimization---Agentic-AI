# Cloud Cost Decision Agent

## 1. Project Overview

This project builds a small decision-making agent for cloud cost monitoring.

The main problem is:

> **The agent observes cloud cost, usage, and recent operational information. It must select whether to wait, investigate, request more evidence, or escalate because the cause of an unusual cost increase is not known.**

The main challenge is that an increase in cloud cost does **not always mean there is a problem**.

For example:

- Cloud cost may increase because customer traffic increased.
- A scheduled workload may normally run at the end of the month.
- A deployment may accidentally increase compute usage.
- A cloud resource may have been left running.
- A system may simply have normal day-to-day variation.

The agent therefore needs to reason under uncertainty before selecting an action.

---

# 2. Hidden States

The real cause of the cost change is called the **hidden state**.

The agent currently considers four possible hidden states:

### `normal`

The cost change is normal variation and does not require investigation.

### `expected_pattern`

The cost increase is caused by known recurring behaviour, such as a scheduled batch process.

### `legitimate_growth`

The cost increase is caused by useful growth in workload, traffic, customers, or usage.

### `cost_incident`

The increase may be caused by unintended or inefficient cloud spending.

Examples include:

- resources left running
- over-provisioned compute
- unexpected logging
- configuration problems
- deployment-related problems

---

# 3. Agent Actions

The agent currently has four possible actions:

### `WAIT`

The available evidence does not suggest an immediate problem.

### `GET_MORE_EVIDENCE`

The situation is suspicious, but the agent is not confident enough to escalate.

### `ASK_HUMAN`

The probability of an incident is high enough that a human should review the case.

### `ESCALATE`

The agent believes there is strong evidence of a cloud cost incident.

---

# 4. Project Structure

The current project structure is:

```text
student-project/
│
├── src/
│   ├── features.py
│   ├── belief.py
│   ├── policy.py
│   └── agent.py
│
├── data/
│   └── test_cases.csv
│
├── experiments/
│   └── evaluate.py
│
├── results/
│   └── predictions.csv
│
└── README.md
```

Each file has a different responsibility.

---

# 5. `features.py`

The purpose of `features.py` is to convert raw cloud information into useful signals.

A sample input case looks like this:

```python
case = {
    "current_cost": 1450,
    "baseline_cost": 1000,
    "current_usage": 105000,
    "baseline_usage": 100000,
    "recent_deployment": True,
    "expected_pattern": False
}
```

For this case, the feature calculations are:

```text
Cost change:       +45.00%
Usage change:       +5.00%
Current unit cost:  0.01381
Baseline unit cost: 0.01000
Unit-cost change:  +38.10%
```

## Cost Change

Cost change is calculated as:

```text
(current cost - baseline cost) / baseline cost × 100
```

For the example:

```text
(1450 - 1000) / 1000 × 100
= 45%
```

This means cloud cost increased by 45%.

---

## Usage Change

Usage change is calculated as:

```text
(current usage - baseline usage) / baseline usage × 100
```

For the example:

```text
(105000 - 100000) / 100000 × 100
= 5%
```

Usage increased by only 5%.

This is important because cost increased much faster than usage.

---

## Unit Cost

Unit cost is:

```text
cloud cost / usage
```

For the current period:

```text
1450 / 105000
= 0.01381
```

For the baseline:

```text
1000 / 100000
= 0.01000
```

The unit cost therefore increased by approximately:

```text
38.10%
```

This provides more information than cost alone.

If cloud cost and workload both increase by similar percentages, the increase may represent legitimate growth.

If cloud cost increases strongly while workload remains almost unchanged, the situation may be more suspicious.

---

# 6. `belief.py`

The agent does not immediately decide that something is an incident.

Instead, it maintains a probability for each possible hidden state.

The initial belief is:

```python
prior_belief = {
    "normal": 0.25,
    "expected_pattern": 0.25,
    "legitimate_growth": 0.25,
    "cost_incident": 0.25
}
```

This means that before examining evidence, the agent gives each explanation a probability of 25%.

The probabilities always sum to:

```text
1.0 = 100%
```

---

# 7. Updating Beliefs

The agent changes its beliefs when new evidence is observed.

This represents the human reasoning function:

> **Change a belief after receiving new evidence.**

The current version uses simple hand-written rules.

These rules are intentionally simple because this is the first testable version of the agent.

---

## Evidence 1: Expected Pattern

For the example case:

```python
expected_pattern = False
```

The initial belief was:

```text
normal               25%
expected pattern     25%
legitimate growth    25%
cost incident        25%
```

Because the cost change does not match a known expected pattern, the belief changes to approximately:

```text
normal               30.0%
expected pattern     15.0%
legitimate growth    27.5%
cost incident        27.5%
```

The probability of `expected_pattern` decreases because the evidence says that the current behaviour is not known to be recurring.

---

## Evidence 2: Cost and Usage

The example has:

```text
Cost change  = +45%
Usage change = +5%
```

The agent currently uses the rule:

```text
If cost increases strongly
and usage increases only slightly,
increase the probability of a cost incident.
```

The belief becomes:

```text
normal               25.0%
expected pattern     12.5%
legitimate growth    25.0%
cost incident        37.5%
```

The cost incident becomes the most likely explanation.

---

## Evidence 3: Recent Deployment

The example also has:

```python
recent_deployment = True
```

A recent deployment does not prove that an incident occurred.

However, if a large cost increase happens near a deployment, it provides additional evidence that an operational change may have affected cloud spending.

After this evidence, the belief becomes:

```text
normal               20.0%
expected pattern     10.0%
legitimate growth    22.5%
cost incident        47.5%
```

The agent now believes there is a:

```text
47.5% probability of a cost incident.
```

The agent is suspicious, but still uncertain.

---

# 8. Important Limitation of the Belief Model

The probability changes used in the current version are **not learned from real cloud data**.

For example:

```text
+0.10 to cost_incident
-0.05 from normal
```

are currently design assumptions.

They are being used to create the smallest testable version of the agent.

Later stages of the project should investigate whether these values are realistic using:

- practitioner feedback
- historical cloud incidents
- experiments
- calibration analysis

These values should therefore not currently be presented as real-world probabilities.

---

# 9. `policy.py`

Once the agent has calculated its belief, it must select an action.

The current V1 policy uses the probability of `cost_incident`.

```text
P(cost incident) < 0.30
→ WAIT

0.30 ≤ P(cost incident) < 0.50
→ GET_MORE_EVIDENCE

0.50 ≤ P(cost incident) < 0.70
→ ASK_HUMAN

P(cost incident) ≥ 0.70
→ ESCALATE
```

For the example case:

```text
P(cost incident) = 0.475
```

Therefore:

```text
0.30 ≤ 0.475 < 0.50
```

and the selected action is:

```text
GET_MORE_EVIDENCE
```

The agent does not immediately escalate because its confidence is not yet high enough.

---

# 10. `agent.py`

`agent.py` connects the different components together.

The complete flow is:

```text
Input case
    ↓
Calculate features
    ↓
Start with prior belief
    ↓
Update belief using expected pattern
    ↓
Update belief using cost and usage
    ↓
Update belief using deployment information
    ↓
Apply decision policy
    ↓
Select action
```

The main function is:

```python
run_agent(case)
```

It returns:

```text
belief
action
```

For the example case, the output is:

```text
Belief:

normal               0.20
expected_pattern     0.10
legitimate_growth    0.225
cost_incident        0.475

Action:

GET_MORE_EVIDENCE
```

---

# 11. Initial Test Cases

The agent was initially tested using five simulated cases.

The cases represent different hidden states:

```text
Case 1 → Cost incident
Case 2 → Normal
Case 3 → Legitimate growth
Case 4 → Expected pattern
Case 5 → Cost incident
```

The true state is stored in the test data only for evaluation.

The agent should not use `true_state` when making its decision.

---

# 12. Initial Agent Results

The current V1 agent produced:

```text
Case 1
True state: cost_incident
Action: GET_MORE_EVIDENCE

Case 2
True state: normal
Action: WAIT

Case 3
True state: legitimate_growth
Action: WAIT

Case 4
True state: expected_pattern
Action: GET_MORE_EVIDENCE

Case 5
True state: cost_incident
Action: GET_MORE_EVIDENCE
```

These are only early tests.

Five cases are not enough to make conclusions about agent performance.

The final experiment will require 30–50 cases.

---

# 13. Predicted State

In addition to selecting an action, the agent records the hidden state with the highest probability.

This is calculated using:

```python
predicted_state = max(belief, key=belief.get)
```

The results are saved to:

```text
results/predictions.csv
```

The file contains information such as:

```text
case_id
true_state
predicted_state
action
normal_prob
expected_pattern_prob
legitimate_growth_prob
cost_incident_prob
```

This allows the agent's decisions to be analysed later.

---

# 14. Baseline Policy

A simple baseline was also created.

The baseline does not reason about uncertainty.

It only looks at cost change.

The rule is:

```text
If cost increases by more than 30%
→ ESCALATE

Otherwise
→ WAIT
```

The baseline produced:

```text
Case 1: +45% → ESCALATE
Case 2:  +4% → WAIT
Case 3: +50% → ESCALATE
Case 4: +35% → ESCALATE
Case 5: +60% → ESCALATE
```

This shows an important weakness of a simple threshold.

For example:

```text
Case 3
True state = legitimate growth
Baseline = ESCALATE
```

and:

```text
Case 4
True state = expected pattern
Baseline = ESCALATE
```

The baseline escalates these cases because it only knows that cost increased.

It does not understand why the cost increased.

---

# 15. Why the Agent May Be Better Than the Baseline

The baseline asks:

> Did cloud cost increase by more than 30%?

The agent asks:

> How much did cost increase?

> Did usage increase at the same time?

> Did unit cost become worse?

> Is this a known expected pattern?

> Was there a recent operational change?

> How certain am I that this is actually an incident?

This gives the agent more context before making a decision.

The experiment will test whether this additional reasoning actually improves decisions.

It should not simply be assumed that the more complicated agent is better.

---

# 16. Current Research Question

A possible research question emerging from the current implementation is:

> **Can a belief-based cloud cost agent reduce unnecessary escalations compared with a simple cost-threshold policy while still identifying potentially costly incidents?**

This question will be refined as more practitioner feedback and experiment results become available.

---

# 17. Current Human Reasoning Function

The current agent implements one simple human-like reasoning capability:

> **Change beliefs when new evidence becomes available.**

For example:

```text
Initial incident probability
25%

No expected pattern
↓
27.5%

Large cost increase with small usage increase
↓
37.5%

Recent deployment
↓
47.5%
```

The agent does not try to reproduce complete human reasoning.

It performs only a small reasoning task that can be tested.

---

# 18. Current Limitations

The current system is only Agent V1.

Known limitations include:

- Belief updates are manually designed.
- Decision thresholds are manually selected.
- Only five initial test cases have been evaluated.
- Test cases are simulated rather than collected from real cloud systems.
- A deployment does not necessarily cause a cost incident.
- The agent currently uses limited operational context.
- Historical similarity has not yet been implemented.
- Costs of incorrect decisions have not yet been added.
- Probability calibration has not yet been tested.
- Reddit and X practitioner feedback has not yet been incorporated into the agent.

These limitations will be addressed or discussed in later stages.

---

# 19. Running the Agent

From the project root directory, run:

```bash
python src/agent.py
```

This runs the agent on the test cases and produces predictions.

The prediction results are saved to:

```text
results/predictions.csv
```

---

# 20. Running the Baseline Evaluation

Run:

```bash
python experiments/evaluate.py
```

The baseline currently checks whether cost increased by more than 30%.

It then selects:

```text
ESCALATE
```

or:

```text
WAIT
```

The baseline will later be compared with the agent using more complete evaluation metrics.

---

# 21. Next Steps

The next stage of the project is to expand the experiment from five cases to approximately 40 simulated cases.

The planned dataset will contain examples of:

```text
Normal variation
Expected patterns
Legitimate growth
Cost incidents
```

After that, the project will compare:

```text
Baseline threshold policy
vs.
Belief-based Agent V1
```

The evaluation will include more than simple accuracy.

Possible measurements include:

```text
False positives
False negatives
Human-review rate
Decision cost
Confusion matrix
Calibration
```

At least five incorrect decisions will also be examined and given named failure conditions.

---

# 22. Current Status

Completed so far:

```text
✓ Problem selected
✓ Hidden states defined
✓ Actions defined
✓ Feature calculations created
✓ Prior belief defined
✓ Evidence-based belief updates created
✓ Initial decision policy created
✓ Agent components connected
✓ Five simulated cases created
✓ Predictions saved
✓ Simple baseline created
✓ Initial baseline comparison performed
```

Still to do:

```text
→ Expand to 30–50 cases
→ Evaluate two agent policies
→ Calculate decision costs
→ Analyse incorrect decisions
→ Add probability decision record
→ Incorporate Reddit/X feedback
→ Perform AI reviews
→ Write the IJCAI-style preprint
→ Prepare final social posts
```

This README describes the current implementation only. The agent design, probability model, and policies may change based on experiments and practitioner feedback.






# V3 — Evidence Gathering, Feedback, Uncertainty, and Decision Cost

## 1. Overview

V3 extends the earlier cloud-cost decision agent by introducing an **evidence-gathering and feedback loop**.

The overall problem remains:

> The agent observes cloud cost, usage, and recent operational information. It must decide whether to wait, investigate, ask a human, or escalate because the true cause of an unusual cost increase is unknown.

The agent cannot directly observe the real hidden state.

The possible hidden states are:

- `normal`
- `expected_pattern`
- `legitimate_growth`
- `cost_incident`

The possible actions are:

- `WAIT`
- `GET_MORE_EVIDENCE`
- `ASK_HUMAN`
- `ESCALATE`

V3 builds on the ideas implemented in V1 and V2.

---

# 2. Evolution from V1 to V3

## V1 — Belief-Based Agent

V1 introduced the basic reasoning pipeline:

```text
Cloud observations
        ↓
Feature calculation
        ↓
Belief update
        ↓
Estimate hidden state
        ↓
Choose action
```

The agent maintains a probability distribution over:

```text
normal
expected_pattern
legitimate_growth
cost_incident
```

An example belief might be:

```text
normal              = 0.20
expected_pattern    = 0.10
legitimate_growth   = 0.225
cost_incident       = 0.475
```

The V1 policy then converts the `cost_incident` probability into an action.

Current V1 thresholds:

```text
P(cost_incident) < 0.30
→ WAIT

0.30 <= P(cost_incident) < 0.50
→ GET_MORE_EVIDENCE

0.50 <= P(cost_incident) < 0.70
→ ASK_HUMAN

P(cost_incident) >= 0.70
→ ESCALATE
```

The purpose of V1 was to establish the basic pipeline:

```text
Evidence
→ Belief
→ Decision
```

---

# 3. V2 — Environment-Aware Decision Policy

Feedback from public discussion highlighted an important issue:

> The same percentage increase in cloud cost may have different consequences depending on whether it occurs in production or development.

For example:

```text
30% increase in development
```

may be less urgent than:

```text
30% increase in production
```

Therefore V2 introduced:

```text
environment
```

with values such as:

```text
production
development
```

V2 does not fundamentally change the hidden-state belief calculation.

Instead, it changes the action thresholds.

## Production thresholds

```text
P(cost_incident) < 0.25
→ WAIT

0.25 <= P(cost_incident) < 0.45
→ GET_MORE_EVIDENCE

0.45 <= P(cost_incident) < 0.65
→ ASK_HUMAN

P(cost_incident) >= 0.65
→ ESCALATE
```

## Development thresholds

```text
P(cost_incident) < 0.35
→ WAIT

0.35 <= P(cost_incident) < 0.55
→ GET_MORE_EVIDENCE

0.55 <= P(cost_incident) < 0.75
→ ASK_HUMAN

P(cost_incident) >= 0.75
→ ESCALATE
```

Therefore the same belief can result in a different action depending on operational context.

---

# 4. Why V3 Was Needed

V1 and V2 could return:

```text
GET_MORE_EVIDENCE
```

but that decision was incomplete.

The agent did not answer:

> What evidence should actually be collected?

For example, after detecting an unusual cost increase, a human analyst might ask:

- Which cloud service caused the increase?
- Did a recent deployment introduce an expensive resource?
- Is usage growth sufficient to explain the cost growth?
- Is one service behaving differently from the rest of the infrastructure?

Therefore V3 introduces an active evidence-gathering loop.

---

# 5. V3 Architecture

The current V3 flow is:

```text
Cloud observations
        ↓
Calculate features
        ↓
Initial belief update
        ↓
Initial action
        ↓
Is action GET_MORE_EVIDENCE?
        ↓
       Yes
        ↓
Choose evidence
        ↓
Receive evidence result
        ↓
Update belief again
        ↓
Make final decision
```

The important difference is that V3 now records both:

```text
initial_action
```

and:

```text
final_action
```

For example:

```text
Initial action:
GET_MORE_EVIDENCE

Selected evidence:
CHECK_SERVICE_BREAKDOWN

Feedback:
CONCENTRATED_SERVICE_SPIKE

Final action:
ASK_HUMAN
```

This allows us to analyse the complete reasoning trajectory.

---

# 6. Test Dataset

The current experiment uses:

```text
data/test_cases_v2.csv
```

There are 40 synthetic cases.

The dataset contains approximately:

```text
10 normal
10 expected_pattern
10 legitimate_growth
10 cost_incident
```

The same cases are reused across V1, V2, and V3 so that comparisons remain fair.

Each case contains:

```text
current_cost
baseline_cost

current_usage
baseline_usage

recent_deployment

matches_historical_pattern

environment

service_type

true_state
```

Example:

```text
current_cost = 2250
baseline_cost = 1500

current_usage = 151000
baseline_usage = 150000

recent_deployment = False

matches_historical_pattern = True

environment = production

service_type = database

true_state = cost_incident
```

---

# 7. Hidden State vs Observable Information

The agent must never directly observe:

```text
true_state
```

The `true_state` column exists only so that the synthetic experiment can be evaluated.

The agent is allowed to see:

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

The hidden state remains one of:

```text
normal
expected_pattern
legitimate_growth
cost_incident
```

This separation is important because the agent is trying to infer the hidden cause from incomplete evidence.

---

# 8. Feature Engineering

The agent calculates additional features from the raw observations.

## Cost change

```text
(current_cost - baseline_cost)
-------------------------------- × 100
baseline_cost
```

Example:

```text
current_cost = 1450
baseline_cost = 1000

cost_change = +45%
```

---

## Usage change

```text
(current_usage - baseline_usage)
---------------------------------- × 100
baseline_usage
```

Example:

```text
current_usage = 105000
baseline_usage = 100000

usage_change = +5%
```

---

## Unit cost

```text
unit_cost = cost / usage
```

Example:

```text
current unit cost
= 1450 / 105000
≈ 0.01381

baseline unit cost
= 1000 / 100000
= 0.01000
```

Unit cost helps distinguish between:

```text
Cost ↑
Usage ↑ similarly
→ possibly legitimate growth
```

and:

```text
Cost ↑ significantly
Usage stays similar
→ possibly inefficient or abnormal spending
```

A `unit_cost_change()` function also exists.

However, unit-cost change is not yet directly used in the current belief update rules.

This remains a limitation.

---

# 9. Initial Prior Belief

The agent currently starts with a uniform prior:

```text
normal              = 0.25
expected_pattern    = 0.25
legitimate_growth   = 0.25
cost_incident       = 0.25
```

The belief is then modified as evidence is observed.

The current belief updates are manually designed heuristics.

They are not learned from historical cloud data.

---

# 10. Historical Pattern Belief Update

The observable feature is:

```text
matches_historical_pattern
```

This is deliberately different from the hidden state:

```text
expected_pattern
```

If:

```text
matches_historical_pattern = True
```

the belief in:

```text
expected_pattern
```

is increased.

If:

```text
matches_historical_pattern = False
```

the belief in `expected_pattern` is reduced and probability is redistributed toward the other hypotheses.

---

# 11. Cost and Usage Belief Update

The agent reasons about how cost and usage change together.

One current heuristic is:

```text
cost_change > 20%
AND
usage_change < 10%
```

This increases belief in:

```text
cost_incident
```

because cloud spending is increasing much faster than workload usage.

Another case is:

```text
cost_change > 20%
AND
usage_change > 20%
```

This increases belief in:

```text
legitimate_growth
```

because increased usage may explain increased cost.

Small changes in both cost and usage increase belief in:

```text
normal
```

The thresholds and update magnitudes are manually selected assumptions for the experiment.

They are not calibrated probabilities.

---

# 12. Deployment Belief Update

If:

```text
recent_deployment = True
```

the agent currently increases belief in:

```text
cost_incident
```

slightly.

The reasoning is:

> If a deployment happened near the time of a cost increase, the deployment may have introduced an inefficient resource or configuration.

However:

```text
recent_deployment = False
```

does not prove that the cost increase is safe.

Therefore the current logic does not strongly decrease incident probability when no deployment occurred.

---

# 13. Explicit Uncertainty

During testing we discovered cases such as:

```text
expected_pattern ≈ 0.325
cost_incident    ≈ 0.325
```

Originally Python could select one of these values because of tiny floating-point differences.

That created false confidence.

We introduced:

```python
predicted_state_with_uncertainty()
```

The function sorts the probabilities and compares the two highest values.

If:

```text
top_probability - second_probability < 0.02
```

the predicted result becomes:

```text
uncertain
```

instead of forcing one of the hidden states.

Important:

```text
uncertain
```

is not a fifth hidden state.

It is a behavioural output indicating that the available evidence does not clearly distinguish the most likely explanations.

---

# 14. Why Uncertainty Matters

The agent should not pretend to know the answer when the belief distribution is ambiguous.

For example:

```text
expected_pattern = 32.5%
cost_incident    = 32.5%
```

should not automatically become:

```text
cost_incident
```

or:

```text
expected_pattern
```

Instead:

```text
predicted_state = uncertain
```

is more appropriate.

This makes the agent's behaviour more realistic.

---

# 15. Original V3 Evidence Options

The first V3 design included:

```text
CHECK_HISTORY
CHECK_SERVICE_BREAKDOWN
CHECK_DEPLOYMENT_DETAILS
```

However, `CHECK_HISTORY` later caused an important failure.

The agent already observes:

```text
matches_historical_pattern
```

during its initial reasoning.

Calling:

```text
CHECK_HISTORY
```

after that could provide essentially the same information again.

The repeated evidence could therefore be double-counted.

---

# 16. Duplicate-Evidence Overconfidence Bug

Case 34 exposed this issue.

The case had:

```text
true_state = cost_incident
matches_historical_pattern = True
```

The earlier flow was:

```text
matches_historical_pattern=True
        ↓
expected_pattern belief increases
        ↓
agent chooses CHECK_HISTORY
        ↓
SIMILAR_PATTERN_FOUND
        ↓
expected_pattern increases again
        ↓
agent predicts expected_pattern
        ↓
WAIT
```

The real hidden state was:

```text
cost_incident
```

The agent therefore waited on a genuine incident.

We called this failure:

> Duplicate-evidence overconfidence

The agent effectively treated correlated/repeated evidence as if it were independent information.

---

# 17. Fix for Duplicate Evidence

`CHECK_HISTORY` was removed from active V3 evidence gathering.

Historical information is now consumed once through:

```text
matches_historical_pattern
```

The current active evidence options are:

```text
CHECK_SERVICE_BREAKDOWN
CHECK_DEPLOYMENT_DETAILS
```

This prevents the same historical evidence from being counted twice.

---

# 18. Case 34 Before and After the Fix

## Before

```text
true_state:
cost_incident

selected_evidence:
CHECK_HISTORY

feedback:
SIMILAR_PATTERN_FOUND

predicted_state:
expected_pattern

final_action:
WAIT
```

This was dangerous.

---

## After removing CHECK_HISTORY

Case 34 became:

```text
true_state:
cost_incident

predicted_state:
cost_incident

initial_action:
GET_MORE_EVIDENCE

selected_evidence:
CHECK_SERVICE_BREAKDOWN

feedback:
CONCENTRATED_SERVICE_SPIKE

final_action:
ASK_HUMAN

cost_incident_prob:
≈ 0.477

trajectory_cost:
3
```

This was a significant improvement.

The error analysis directly caused an architectural change to the agent.

---

# 19. Current Evidence Options

The current evidence options are:

```text
CHECK_SERVICE_BREAKDOWN
CHECK_DEPLOYMENT_DETAILS
```

---

# 20. CHECK_SERVICE_BREAKDOWN

This evidence tries to determine whether the cost increase is concentrated in a particular cloud service and whether the increase is consistent with usage.

Possible synthetic outcomes include:

```text
CONCENTRATED_SERVICE_SPIKE
USAGE_ALIGNED_GROWTH
NO_CLEAR_SERVICE_CAUSE
```

Interpretation:

```text
CONCENTRATED_SERVICE_SPIKE
→ supports cost_incident
```

```text
USAGE_ALIGNED_GROWTH
→ supports legitimate_growth
```

```text
NO_CLEAR_SERVICE_CAUSE
→ does not clearly confirm a service-level incident
```

---

# 21. CHECK_DEPLOYMENT_DETAILS

This evidence investigates whether a recent deployment contains a change that plausibly explains increased cloud cost.

Possible synthetic outcomes include:

```text
COST_RELEVANT_CHANGE_FOUND
NO_COST_RELEVANT_CHANGE
```

Interpretation:

```text
COST_RELEVANT_CHANGE_FOUND
→ supports cost_incident
```

```text
NO_COST_RELEVANT_CHANGE
→ deployment does not clearly explain the increase
```

---

# 22. Synthetic Feedback Simulator

Evidence feedback is generated in:

```text
src/feedback.py
```

Because the experiment is synthetic, the simulator is allowed to use:

```text
true_state
```

to generate an observation.

However, the agent itself never receives `true_state`.

Example:

```text
Agent selects:
CHECK_SERVICE_BREAKDOWN

Simulator internally sees:
true_state = cost_incident

Simulator returns:
CONCENTRATED_SERVICE_SPIKE
```

The agent only receives:

```text
CONCENTRATED_SERVICE_SPIKE
```

It never receives:

```text
cost_incident
```

directly.

---

# 23. Feedback for Service Breakdown

Current synthetic behaviour:

```text
true_state = cost_incident
→ CONCENTRATED_SERVICE_SPIKE
```

```text
true_state = legitimate_growth
→ USAGE_ALIGNED_GROWTH
```

Otherwise:

```text
→ NO_CLEAR_SERVICE_CAUSE
```

This is deliberately simplified.

Real service evidence would be noisy and would not map perfectly to hidden states.

---

# 24. Feedback for Deployment Details

Current synthetic behaviour:

```text
true_state = cost_incident
→ COST_RELEVANT_CHANGE_FOUND
```

Otherwise:

```text
→ NO_COST_RELEVANT_CHANGE
```

Again, this is a simplified simulation.

---

# 25. Belief Update After Feedback

V3 includes:

```python
update_from_feedback()
```

This allows the belief distribution to change after new evidence is collected.

Examples:

```text
CONCENTRATED_SERVICE_SPIKE
→ increase cost_incident probability
```

```text
USAGE_ALIGNED_GROWTH
→ increase legitimate_growth probability
→ reduce cost_incident suspicion
```

```text
COST_RELEVANT_CHANGE_FOUND
→ increase cost_incident probability
```

The update magnitudes are manually chosen.

They are not learned probabilities.

---

# 26. Complete V3 Feedback Loop

A complete V3 trajectory can now look like:

```text
Initial cloud observations
        ↓
Initial belief
        ↓
Initial action:
GET_MORE_EVIDENCE
        ↓
Evidence:
CHECK_SERVICE_BREAKDOWN
        ↓
Feedback:
CONCENTRATED_SERVICE_SPIKE
        ↓
Updated belief
        ↓
Final action:
ASK_HUMAN
```

This is the main behavioural difference between V2 and V3.

V2 stops at:

```text
GET_MORE_EVIDENCE
```

V3 actually performs one investigation step.

---

# 27. Action History

Originally the agent returned only:

```text
action
```

after feedback.

This meant a trajectory such as:

```text
GET_MORE_EVIDENCE
→ CHECK_SERVICE_BREAKDOWN
→ ASK_HUMAN
```

was saved only as:

```text
ASK_HUMAN
```

That lost information about the cost and reasoning involved in the investigation.

We changed V3 so that it records:

```text
initial_action
final_action
selected_evidence
feedback
```

---

# 28. Current V3 Output Columns

The V3 results file contains:

```text
case_id
true_state
predicted_state

initial_action
final_action
action

selected_evidence
feedback

normal_prob
expected_pattern_prob
legitimate_growth_prob
cost_incident_prob
```

Currently:

```text
action = final_action
```

is kept for compatibility with older evaluation code.

---

# 29. Decision Cost

Accuracy alone is not sufficient.

Some mistakes are much more expensive than others.

For example:

```text
WAIT on a real cost incident
```

should have a higher cost than:

```text
GET_MORE_EVIDENCE on a normal case
```

Therefore we introduced a relative decision-cost matrix.

---

# 30. Current Decision-Cost Matrix

## True state = normal

```text
WAIT                 = 0
GET_MORE_EVIDENCE    = 1
ASK_HUMAN            = 2
ESCALATE             = 4
```

## True state = expected_pattern

```text
WAIT                 = 0
GET_MORE_EVIDENCE    = 1
ASK_HUMAN            = 2
ESCALATE             = 4
```

## True state = legitimate_growth

```text
WAIT                 = 0
GET_MORE_EVIDENCE    = 1
ASK_HUMAN            = 2
ESCALATE             = 4
```

## True state = cost_incident

```text
WAIT                 = 10
GET_MORE_EVIDENCE    = 2
ASK_HUMAN            = 1
ESCALATE             = 0
```

These numbers are:

> relative experimental costs

They are not real GBP values.

They are not calibrated against production cloud incidents.

---

# 31. Why Missed Incidents Cost More

A missed cost incident can continue consuming money without intervention.

Therefore:

```text
cost_incident + WAIT
```

has the highest current cost:

```text
10
```

By comparison:

```text
normal + WAIT
```

has:

```text
0
```

because waiting was the correct decision.

---

# 32. Evidence Cost

Evidence collection itself also has a cost.

Current assumptions:

```text
CHECK_HISTORY               = 1
CHECK_SERVICE_BREAKDOWN     = 2
CHECK_DEPLOYMENT_DETAILS    = 2
```

`CHECK_HISTORY` remains in the cost configuration for compatibility with earlier experiments, even though it is no longer part of the active V3 evidence selector.

These are again relative experimental costs.

---

# 33. Trajectory Cost

For V3 we calculate:

```text
trajectory_cost
=
final_decision_cost
+
evidence_collection_cost
```

For example:

```text
CHECK_SERVICE_BREAKDOWN
cost = 2

Final action:
ASK_HUMAN
cost = 1

Total trajectory cost:
3
```

This prevents V3 from receiving evidence for free.

---

# 34. Why Trajectory Cost Was Added

Initially V3 was evaluated using only the final action.

For example:

```text
GET_MORE_EVIDENCE
→ CHECK_HISTORY
→ WAIT
```

was evaluated only as:

```text
WAIT
```

That made the investigation disappear from the cost calculation.

We therefore added:

```text
initial_action
selected_evidence
feedback
final_action
```

and evaluate the whole reasoning path.

---

# 35. Evidence Usage Analysis

The evaluation script counts:

- how many cases gathered evidence,
- which evidence was selected,
- which true states received which evidence.

This helps identify over-investigation.

---

# 36. Evidence Effectiveness Analysis

We also measure whether collecting evidence changed the action.

For example:

```text
GET_MORE_EVIDENCE
→ WAIT
```

means evidence resolved the uncertainty.

Likewise:

```text
GET_MORE_EVIDENCE
→ ASK_HUMAN
```

means evidence increased the perceived risk.

However:

```text
GET_MORE_EVIDENCE
→ GET_MORE_EVIDENCE
```

means the agent paid for information but still remained unresolved.

---

# 37. Current Frozen V3 Evidence Results

Current run:

```text
Total evidence checks = 22
```

All 22 active checks currently selected:

```text
CHECK_SERVICE_BREAKDOWN
```

Evidence by true state:

```text
cost_incident       = 8
expected_pattern    = 5
legitimate_growth   = 8
normal              = 1
```

This shows that the current heuristic evidence selector strongly favours:

```text
CHECK_SERVICE_BREAKDOWN
```

This is a known limitation.

---

# 38. Evidence Effectiveness

Among the 22 evidence checks:

```text
15 changed the final action
7 did not change the final action
```

Action transitions:

```text
GET_MORE_EVIDENCE
→ ASK_HUMAN
7 cases
```

```text
GET_MORE_EVIDENCE
→ WAIT
8 cases
```

```text
GET_MORE_EVIDENCE
→ GET_MORE_EVIDENCE
7 cases
```

Therefore some evidence was useful, but 7 investigations still did not resolve the decision.

---

# 39. Evidence Non-Resolution

An example unresolved trajectory is:

```text
GET_MORE_EVIDENCE
→ CHECK_SERVICE_BREAKDOWN
→ NO_CLEAR_SERVICE_CAUSE
→ GET_MORE_EVIDENCE
```

The agent paid for evidence but remained in the same operational state.

We call this:

> Evidence non-resolution loop

This is one of the main current V3 weaknesses.

---

# 40. Evidence Value Analysis

We also calculate:

```text
decision_improvement
=
initial_decision_cost
-
final_decision_cost
```

Then:

```text
net_value
=
decision_improvement
-
evidence_collection_cost
```

For the latest frozen service-breakdown experiment:

```text
checks = 22
decision improvement = 15
collection cost = 44
net value = -29
```

This indicates that under the current cost assumptions, evidence improves decisions but costs too much overall.

---

# 41. Important Clarification: Evidence Value Is Not Information Gain

The current:

```text
decision improvement
-
evidence cost
```

metric measures practical decision value after the experiment.

It is NOT Shannon information gain.

It does not measure reduction in uncertainty in bits.

---

# 42. V1 vs V2 vs V3 Results

The current structured comparison is:

## V1

```text
Total decision cost = 34
Average decision cost = 0.85
```

## V2

```text
Total decision cost = 32
Average decision cost = 0.80
```

## V3

```text
Final decision cost = 17

Evidence collection cost = 44

Total trajectory cost = 61

Average trajectory cost = 1.525
```

---

# 43. Interpretation of V3 Cost

This is an important result.

V3 produces better final decisions:

```text
V1 decision cost = 34
V2 decision cost = 32
V3 final decision cost = 17
```

However:

```text
V3 evidence cost = 44
```

Therefore:

```text
V3 total trajectory cost = 61
```

So:

> Better final decisions do not necessarily mean lower total operating cost.

V3 currently investigates too often or uses evidence that is too expensive relative to the improvement it provides.

This is a useful research finding.

The goal is not to artificially tune V3 until it beats V1 and V2.

---

# 44. Uncertainty Results After V3 Feedback

Current V3 results show:

```text
Total uncertain cases = 10
```

Their true states are:

```text
expected_pattern     = 8
legitimate_growth    = 2
```

Actions among uncertain cases:

```text
WAIT                 = 6
GET_MORE_EVIDENCE    = 4
```

Importantly:

```text
uncertain true cost incidents = 0
```

Therefore no true incident remained classified as uncertain in the current frozen V3 run.

---

# 45. Failure Analysis

We inspected individual cases rather than relying only on aggregate statistics.

This produced several named failure modes.

---

# 46. Failure 1 — Post-Confirmation Hesitation

## Case 38

Input:

```text
baseline_cost = 1000
current_cost = 1340

cost_change ≈ +34%

baseline_usage = 100000
current_usage = 98000

usage_change ≈ -2%

recent_deployment = False

matches_historical_pattern = False

environment = development

service_type = database

true_state = cost_incident
```

The pattern is suspicious:

```text
Cost increased significantly
while usage actually decreased
```

The agent chose:

```text
CHECK_SERVICE_BREAKDOWN
```

Feedback:

```text
CONCENTRATED_SERVICE_SPIKE
```

The final incident belief became approximately:

```text
0.522727
```

However, because the case was in:

```text
development
```

the policy still returned:

```text
GET_MORE_EVIDENCE
```

rather than human review.

Failure name:

> Post-confirmation hesitation

Meaning:

> Strong confirming evidence was obtained, but the action threshold remained too conservative.

---

# 47. Failure 2 — Deployment-Driven Over-Investigation

## Case 6

Input:

```text
baseline_cost = 2000
current_cost = 2060

cost_change ≈ +3%

baseline_usage = 200000
current_usage = 205000

usage_change ≈ +2.5%

recent_deployment = True

matches_historical_pattern = False

environment = production

service_type = compute

true_state = normal
```

The cost and usage changes were small.

However, the agent chose:

```text
GET_MORE_EVIDENCE
```

then:

```text
CHECK_SERVICE_BREAKDOWN
```

Feedback:

```text
NO_CLEAR_SERVICE_CAUSE
```

Final action:

```text
GET_MORE_EVIDENCE
```

Failure name:

> Deployment-driven over-investigation

Meaning:

> The existence of a recent deployment contributed too strongly to suspicion even though cost and usage behaviour were close to normal.

---

# 48. Failure 3 — Evidence Non-Resolution Loop

Several `expected_pattern` cases behave like:

```text
GET_MORE_EVIDENCE
→ CHECK_SERVICE_BREAKDOWN
→ NO_CLEAR_SERVICE_CAUSE
→ GET_MORE_EVIDENCE
```

Examples include:

```text
Case 11
Case 16
Case 17
Case 19
```

The evidence was collected but did not resolve the agent's uncertainty.

Failure name:

> Evidence non-resolution loop

This increases investigation cost without producing a new action.

---

# 49. Failure 4 — Harmless Hidden-State Misclassification

## Case 2

Input:

```text
baseline_cost = 900
current_cost = 918

cost_change ≈ +2%

baseline_usage = 80000
current_usage = 81000

matches_historical_pattern = True

environment = development

service_type = database

true_state = normal
```

The agent predicted:

```text
expected_pattern
```

rather than:

```text
normal
```

However, the final action was:

```text
WAIT
```

which was still operationally appropriate.

Decision cost:

```text
0
```

Failure name:

> Harmless hidden-state misclassification

This shows that:

```text
hidden-state accuracy
```

and:

```text
decision quality
```

are not the same thing.

A wrong diagnosis can still result in an appropriate operational action.

---

# 50. Failure 5 — Duplicate-Evidence Overconfidence

This occurred in an earlier V3 design.

Case 34 already had:

```text
matches_historical_pattern = True
```

The agent then selected:

```text
CHECK_HISTORY
```

and received:

```text
SIMILAR_PATTERN_FOUND
```

This effectively counted the same historical evidence twice.

The agent became too confident in:

```text
expected_pattern
```

and selected:

```text
WAIT
```

even though:

```text
true_state = cost_incident
```

Failure name:

> Duplicate-evidence overconfidence

This was a high-cost error.

It directly resulted in the removal of:

```text
CHECK_HISTORY
```

from the V3 evidence options.

---

# 51. Error Analysis Changed the Architecture

Case 34 is important because it demonstrates that evaluation was not only used to calculate metrics.

It changed the system design.

The original design:

```text
matches_historical_pattern
+
CHECK_HISTORY
```

created duplicated evidence.

The revised design removed `CHECK_HISTORY`.

After the change, Case 34 became:

```text
GET_MORE_EVIDENCE
→ CHECK_SERVICE_BREAKDOWN
→ CONCENTRATED_SERVICE_SPIKE
→ cost_incident
→ ASK_HUMAN
```

This reduced the trajectory cost from a dangerous missed incident to a much safer investigation.

---

# 52. Current Repository Structure

Approximate project structure:

```text
student-project/
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
└── results/
    ├── predictionsv1_on_v2.csv
    ├── predictions_v2.csv
    └── predictions_v3.csv
```

---

# 53. `features.py`

Responsibilities:

```text
cost_change()
usage_change()
unit_cost()
unit_cost_change()
```

It converts raw cloud observations into signals used by the belief system.

---

# 54. `belief.py`

Responsibilities include:

```text
prior_belief

update_historical_pattern()

update_cost_usage()

update_deployment()

update_from_feedback()

predicted_state_with_uncertainty()
```

It contains the current manually defined belief-update logic.

---

# 55. `policy.py`

Contains:

```text
select_action()
```

for V1 and:

```text
select_action_v2()
```

for environment-aware decisions.

V3 currently reuses `select_action_v2()` after receiving additional evidence.

---

# 56. `evidence.py`

Responsible for deciding which additional evidence V3 should collect.

Current active options:

```text
CHECK_SERVICE_BREAKDOWN
CHECK_DEPLOYMENT_DETAILS
```

The current evidence-selection mechanism is still heuristic.

---

# 57. `feedback.py`

Responsible for simulating the result of collecting evidence.

It uses `true_state` internally only because the current experiment is synthetic.

The hidden state is never directly passed to the agent.

---

# 58. `cost.py`

Contains:

```text
COST_MATRIX

EVIDENCE_COST

decision_cost()

evidence_cost()

trajectory_cost()
```

It allows evaluation based on operational consequences rather than accuracy alone.

---

# 59. `agent.py`

Coordinates the complete V3 reasoning loop:

```text
features
→ initial belief
→ initial action
→ evidence selection
→ feedback
→ belief update
→ final action
```

The function currently returns:

```text
belief
initial_action
final_action
evidence
feedback
```

---

# 60. `evaluate.py`

The evaluation script currently performs:

```text
Run V3 on 40 cases

Save predictions_v3.csv

Calculate V1 cost

Calculate V2 cost

Calculate V3 final decision cost

Calculate V3 evidence cost

Calculate V3 trajectory cost

Inspect evidence usage

Inspect evidence effectiveness

Calculate evidence value

Inspect no-change evidence cases

Inspect uncertainty

Find highest-cost cases

Inspect failure candidates

Inspect specific problematic cases
```

---

# 61. Current Limitations

## Synthetic data

The experiment currently uses synthetic cases.

No real AWS, GCP, or Azure billing dataset is currently used.

---

## Synthetic labels

The synthetic data provides:

```text
true_state
```

Real cloud incidents generally do not come with perfect hidden-state labels.

---

## Manual belief updates

The belief-update values are manually chosen.

They are not learned from real incident data.

---

## Manual policy thresholds

The action thresholds are experimental assumptions.

They do not currently represent a real organisation's risk tolerance.

---

## Manual cost matrix

Values such as:

```text
missed incident = 10
false escalation = 4
```

are relative research assumptions.

They are not real financial values.

---

## Deterministic feedback

The current evidence simulator is simplified.

For example:

```text
true_state = cost_incident
→ CONCENTRATED_SERVICE_SPIKE
```

Real evidence would be uncertain and noisy.

---

## One evidence round

V3 currently performs only one evidence-gathering iteration.

For example:

```text
GET_MORE_EVIDENCE
→ CHECK_SERVICE_BREAKDOWN
→ GET_MORE_EVIDENCE
```

currently stops there.

The agent does not perform a second evidence-gathering step.

---

## Evidence selector bias

The current frozen version selected:

```text
CHECK_SERVICE_BREAKDOWN
```

for all 22 evidence cases.

This indicates that the evidence-selection logic is still too simplistic.

---

## Unit cost is not fully integrated

`unit_cost_change()` exists but is not yet directly incorporated into the belief update.

---

# 62. Information Gain and Entropy Status

V3 was inspired by the idea that an agent should choose evidence based on how much uncertainty that evidence is expected to remove.

However, **actual information gain has not yet been implemented**.

The current evidence selector uses heuristic rules.

For example:

```python
if belief["cost_incident"] >= threshold:
    favour CHECK_SERVICE_BREAKDOWN
```

This is not information gain.

---

# 63. Shannon Entropy Has Not Yet Been Implemented

The mathematical uncertainty measure:

```text
H(b) = - Σ p_i log2(p_i)
```

has not yet been added.

The current agent therefore does not currently calculate uncertainty in bits.

---

# 64. Current `uncertain` Logic Is Not Entropy

The current uncertainty behaviour checks:

```text
difference between top two probabilities
```

For example:

```text
expected_pattern = 0.325
cost_incident    = 0.325
```

If their difference is less than:

```text
0.02
```

the result becomes:

```text
uncertain
```

This is useful operationally but it is not equivalent to Shannon entropy.

Entropy considers the entire probability distribution.

---

# 65. Expected Posterior Entropy Has Not Yet Been Implemented

For true information-gain selection, the agent would need to evaluate:

```text
If I collect this evidence,
what possible results could I receive?
```

Then for every possible evidence result:

```text
update belief
calculate posterior entropy
```

The agent would then calculate the expected remaining uncertainty.

This has not yet been implemented.

---

# 66. Information Gain Has Not Yet Been Implemented

The intended future calculation is conceptually:

```text
Information Gain
=
Current Entropy
-
Expected Posterior Entropy
```

This would measure how many bits of uncertainty an evidence action is expected to remove.

The current V3 evidence rules do not perform this calculation.

---

# 67. Information Gain Per Cost Has Not Yet Been Implemented

The intended evidence-selection strategy is:

```text
Information Gain / Evidence Cost
```

For example:

```text
CHECK_SERVICE_BREAKDOWN
Information Gain = 0.8 bits
Cost = 2

Value = 0.4 bits per cost unit
```

versus:

```text
CHECK_DEPLOYMENT_DETAILS
Information Gain = 0.5 bits
Cost = 1

Value = 0.5 bits per cost unit
```

The second evidence source would then be preferred.

This has not yet been implemented.

---

# 68. Mutual Information Has Not Yet Been Implemented

Mutual information was also discussed as a way of measuring how informative a clue is about a particular hidden variable.

This has not yet been implemented.

---

# 69. Current Evidence Value Is Different From Information Gain

The current experiment calculates:

```text
net_value
=
decision improvement
-
evidence cost
```

This asks:

> Did collecting the evidence improve the operational decision enough to justify its cost?

Information gain asks a different question:

> How much uncertainty did this evidence remove?

These are related but different concepts.

Both can eventually be evaluated.

---

# 70. Planned Information-Gain Architecture

The next planned evidence-selection system is:

```text
Current belief
      ↓
Calculate Shannon entropy
      ↓
For each possible evidence source:
      ↓
Enumerate possible outcomes
      ↓
Estimate probability of each outcome
      ↓
Calculate posterior belief
      ↓
Calculate posterior entropy
      ↓
Calculate expected posterior entropy
      ↓
Calculate information gain
      ↓
Divide by evidence cost
      ↓
Select evidence with highest value
```

Conceptually:

```text
best evidence
=
highest expected information gain
per unit of evidence cost
```

This would replace the current heuristic evidence selector.

---

# 71. Main Lessons From V3 So Far

## Lesson 1 — An agent should be allowed to admit uncertainty

Forcing every probability distribution into a confident hidden-state prediction can create false confidence.

---

## Lesson 2 — GET_MORE_EVIDENCE must specify what evidence is needed

A useful agent should not simply say:

```text
investigate
```

It should identify the next useful information source.

---

## Lesson 3 — Evidence has an operational cost

More investigation does not automatically produce a better system.

V3 demonstrates:

```text
better final decisions
≠
lower total cost
```

---

## Lesson 4 — Correlated evidence can produce overconfidence

The earlier `CHECK_HISTORY` failure demonstrated that repeated evidence must not be treated as independent information.

---

## Lesson 5 — Decision quality and classification accuracy are different

Case 2 showed:

```text
wrong hidden state
+
correct action
=
zero decision cost
```

Therefore accuracy alone is not enough.

---

## Lesson 6 — Error analysis should modify the architecture

Case 34 directly led to removal of `CHECK_HISTORY`.

This demonstrates why individual failure analysis matters.

---

## Lesson 7 — Evidence that does not change behaviour may be wasteful

Seven evidence checks in the current run did not change the agent's final action.

This creates unnecessary investigation cost.

---

## Lesson 8 — Better final decisions can still be economically worse

V3 reduced final decision cost:

```text
V2 = 32
V3 final decisions = 17
```

but spent:

```text
44
```

on evidence.

Therefore:

```text
V3 total = 61
```

The evidence acquisition strategy is therefore the next important research problem.

---

# 72. Current V3 Status

Implemented:

```text
✓ Hidden-state belief distribution

✓ Cost and usage features

✓ Historical-pattern observation

✓ Deployment observation

✓ Environment-aware policy

✓ Explicit uncertain prediction

✓ Initial action

✓ Evidence selection

✓ Evidence costs

✓ Synthetic feedback

✓ Posterior belief update

✓ Final action after evidence

✓ Initial/final action tracking

✓ Trajectory cost

✓ Evidence-effectiveness analysis

✓ Evidence-value analysis

✓ Highest-cost case inspection

✓ Failure analysis

✓ Architectural change based on failure analysis
```

Not yet implemented:

```text
✗ Shannon entropy

✗ Expected posterior entropy

✗ Information gain

✗ Information gain per cost

✗ Mutual information

✗ Calibrated probabilities

✗ Real cloud billing data

✗ Noisy evidence likelihood models

✗ Multi-round investigation

✗ Real human feedback

✗ Real monetary evidence costs
```

---

# 73. Current Experimental Conclusion

The current V3 experiment shows that adding evidence gathering can improve final operational decisions.

The final decision-cost comparison is:

```text
V1 = 34
V2 = 32
V3 final decision cost = 17
```

However, collecting evidence introduces additional cost:

```text
V3 evidence cost = 44
```

giving:

```text
V3 total trajectory cost = 61
```

Therefore the current result is:

> V3 makes better final decisions but investigates too aggressively, causing its total decision trajectory to become more expensive.

This suggests that the next important improvement is not simply changing action thresholds.

The next improvement should focus on:

> selecting evidence more intelligently.

The planned method is to use:

```text
Shannon entropy
+
expected information gain
+
evidence cost
```

so that the agent asks:

> Which piece of evidence is expected to reduce my uncertainty the most relative to the cost of obtaining it?