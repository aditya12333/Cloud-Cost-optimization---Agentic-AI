# Cloud Cost Decision Agent — Real-Data FinOps Version

## Overview

This project extends a synthetic cloud-cost decision agent into a real-data FinOps investigation system using the FinOps Foundation FOCUS billing dataset.

The core problem is:

> When cloud cost increases significantly, is the increase caused by legitimate workload growth, expected behaviour, a new cost driver, accounting effects, pricing changes, or a genuine cost incident?

The project is deliberately designed as a sequential decision system rather than a simple threshold-based anomaly detector.

The agent can choose between four operational actions:

```text
WAIT
GET_MORE_EVIDENCE
ASK_HUMAN
ESCALATE
```

The main idea is that a large cost increase should not automatically result in escalation.

The agent should first determine whether the increase can be explained by actual resource usage, pricing, billing behaviour, historical patterns, or other evidence.

---

# Current Agent Flow

```text
Cloud billing observation
        ↓
Cost + usage features
        ↓
Historical comparison
        ↓
Initial belief
        ↓
Initial action
        ↓
────────────────────────────
If more evidence is required
────────────────────────────
        ↓
CHECK_COST_DRIVER
        ↓
Driver-level billing evidence
        ↓
Evidence interpretation
        ↓
Belief update
        ↓
Final action
        ↓
Alert episode clustering
        ↓
Human review
```

The current hidden explanations considered by the agent are:

```text
normal
expected_pattern
legitimate_growth
cost_incident
```

These beliefs are currently heuristic normalised scores and should not be interpreted as calibrated probabilities.

---

# Project Evolution

The project has been developed in two main phases.

## Phase 1 — Controlled Synthetic Environment

The first version used synthetic cloud-cost observations.

The purpose was to create an environment where the true hidden state was known during evaluation while remaining hidden from the agent during decision-making.

The synthetic agent was developed through several iterations:

```text
V1
Simple belief model + threshold policy

V2
Environment-aware policy

V3
Sequential evidence acquisition

V4
Entropy + expected information gain
```

The synthetic environment allowed experimentation with:

```text
belief updates
decision costs
uncertainty
human escalation
evidence acquisition
information gain
cost-sensitive evaluation
```

This phase was useful for understanding the decision architecture before moving onto real cloud billing data.

---

# Phase 2 — Real FinOps Data

The second phase replaces synthetic cost observations with real FinOps billing data.

The current dataset is the FinOps Foundation FOCUS sample dataset.

Full dataset:

```text
5,488,359 billing records
44 columns
```

AWS portion:

```text
5,181,336 records
```

The current dataset covers:

```text
September 2024
```

Because only one month of billing data is available, the current project focuses on short-term cost behaviour rather than long-term seasonal modelling.

---

# AWS Services Analysed

The current real-data implementation focuses on:

```text
Amazon Relational Database Service (RDS)
Amazon Elastic File System (EFS)
Amazon Simple Storage Service (S3)
Amazon Elastic Container Service for Kubernetes (EKS)
```

---

# Real Data Processing

The raw FOCUS dataset is transformed into several evidence layers.

## Hourly Service Cost

Raw AWS billing records are aggregated by:

```text
hour
service
```

The resulting dataset contains approximately:

```text
26,325 hourly-service observations
63 AWS services
720 possible hourly timestamps
```

---

# Cost Decomposition

The project separates:

```text
Usage Cost
Credits
Other Cost
EffectiveCost
BilledCost
```

This matters because a cloud service can have stable operational usage while credits or accounting adjustments significantly change its reported EffectiveCost.

---

# Usage-Cost Features

The feature pipeline calculates:

```text
24-hour usage cost
previous 7-day baseline
cost percentage change
usage percentage change
historical cost percentile
credit offset ratio
unit-cost behaviour
historical-pattern deviation
```

All rolling historical features are calculated using only past observations.

Future observations are never included in the current timestamp's baseline.

---

# Leakage-Safe Historical Percentiles

Historical percentiles are calculated using only observations available before the current timestamp.

For example:

```text
cost percentile = 98.8
```

means the current cost behaviour is more extreme than approximately 98.8% of prior observations available to the agent.

---

# Service-Specific Usage Evidence

Different AWS services use different billing units.

Examples include:

```text
Hours
GB
GB-Months
IOs
```

Current primary signals include:

```text
EKS → Hours
RDS → Hours
EFS → GB
S3 → GB
```

For S3 storage behaviour, daily `GB-Months` evidence is also used because storage usage does not behave like a normal hourly metric.

---

# Historical Pattern Detection

The system also checks whether the current cost behaviour resembles recent historical behaviour.

For a given service and hour of day, the current 24-hour cost is compared with previous values observed at the same hour.

The current pattern threshold is heuristic and is used only as supporting evidence.

---

# Real Belief Model

The real agent maintains scores for:

```text
normal
expected_pattern
legitimate_growth
cost_incident
```

The initial belief currently considers evidence such as:

```text
cost change
historical cost percentile
usage change
unit-cost percentile
new-account behaviour
historical-pattern match
```

The scores are manually designed heuristic weights.

They are not trained probabilities.

---

# Initial Policy

The current action policy uses the incident score:

```text
incident < 0.30
    → WAIT

0.30 ≤ incident < 0.50
    → GET_MORE_EVIDENCE

0.50 ≤ incident < 0.70
    → ASK_HUMAN

incident ≥ 0.70
    → ESCALATE
```

These thresholds are currently heuristic.

---

# Real Evidence Acquisition

A major improvement in the real-data phase is that the agent can collect additional evidence directly from the FOCUS billing data.

The driver-level dataset is grouped by:

```text
hour
service
charge description
consumed unit
sub-account
```

The resulting dataset contains:

```text
147,052 driver-level observations
346 distinct charge descriptions
78 sub-accounts
```

---

# CHECK_COST_DRIVER

The main second-stage evidence action is:

```text
CHECK_COST_DRIVER
```

The system investigates the dominant driver responsible for the current cost increase.

The evidence includes:

```text
charge description
sub-account
EffectiveCost
BilledCost
ConsumedQuantity
ConsumedUnit
billed unit cost
ListUnitPrice
ContractedUnitPrice
historical baseline
```

The agent then asks questions such as:

```text
Which charge caused the increase?

Did usage increase?

Did billed cost increase proportionally?

Did the actual billing unit price change?

Did a completely new cost driver appear?

Is the abnormal movement only present in EffectiveCost?
```

---

# Structured Real Feedback

Driver-level evidence is converted into structured feedback states.

The current evidence categories are:

```text
USAGE_ALIGNED_DRIVER_GROWTH

NEW_COST_DRIVER

EFFECTIVE_COST_ACCOUNTING_SHIFT

UNEXPLAINED_DRIVER_COST_INCREASE

UNIT_COST_INCREASE

MIXED_DRIVER_EVIDENCE

INSUFFICIENT_DRIVER_EVIDENCE
```

These feedback states are then used to update the agent's belief before the final action is selected.

---

# Example 1 — RDS Initial Escalation

One of the highest-risk RDS observations initially produced:

```text
cost_incident ≈ 0.765

Initial action:
ESCALATE
```

The dominant driver was:

```text
RDS db.m5.4xlarge Multi-AZ MySQL
Sub-account: Nimbus Orion
```

The deeper investigation showed:

```text
Cost change       +122.7%
Usage change      +122.7%
Unit-cost change      0%
```

After incorporating the driver evidence:

```text
cost_incident       ≈ 0.417
legitimate_growth   ≈ 0.455
```

The final action changed from:

```text
ESCALATE
```

to:

```text
GET_MORE_EVIDENCE
```

---

# Example 2 — EffectiveCost Failure Mode

One of the most important findings in the project came from a failure in the original evidence implementation.

The first version calculated:

```text
EffectiveCost / ConsumedQuantity
```

and treated this as a unit-price signal.

For one representative EFS observation:

```text
EffectiveCost increase      +270.6%
BilledCost increase         +107.2%
Usage increase              +107.2%

Billed unit-cost change        ~0%
List-price change                0%
```

The actual billing rate remained:

```text
$0.07 / GB
```

The evidence layer was redesigned to separate:

```text
EffectiveCost
    → economic / accounting signal

BilledCost
    → billed-cost signal

BilledCost / ConsumedQuantity
    → actual billed unit-cost signal

ListUnitPrice
    → explicit pricing evidence
```

A new feedback category was introduced:

```text
EFFECTIVE_COST_ACCOUNTING_SHIFT
```

This correction removed the earlier false `UNIT_COST_INCREASE` behaviour.

---

# Current Real-Agent Experiment

Current agent-ready observations:

```text
1,444
```

## Initial Decisions

```text
WAIT                 1021
GET_MORE_EVIDENCE     192
ASK_HUMAN             206
ESCALATE                25
```

## Final Decisions

```text
WAIT                 1300
GET_MORE_EVIDENCE      83
ASK_HUMAN              61
ESCALATE                 0
```

Total decisions changed:

```text
395 / 1,444
≈ 27.35%
```

This demonstrates that additional evidence materially changes the initial decision.

It does not prove that every final decision is correct.

---

# Real Feedback Distribution

The latest real-data run produced:

```text
USAGE_ALIGNED_DRIVER_GROWTH        301
NEW_COST_DRIVER                     65
EFFECTIVE_COST_ACCOUNTING_SHIFT     57
```

After correcting the EffectiveCost interpretation:

```text
UNEXPLAINED_DRIVER_COST_INCREASE = 0
```

This should not be interpreted as evidence that no genuine incidents exist.

---

# Alert Episode Clustering

Rolling 24-hour windows can create repeated alerts for the same underlying event.

The system therefore groups consecutive alerts from the same service into operational episodes.

Latest result:

```text
23 alert episodes
```

Peak action:

```text
GET_MORE_EVIDENCE    20
ASK_HUMAN             3
ESCALATE              0
```

Episodes by service:

```text
EKS    9
EFS    6
RDS    5
S3     3
```

---

# Human Review Dataset

A human-review dataset was created for all 23 alert episodes.

The current review produced:

```text
LEGITIMATE_GROWTH               15
ACCOUNTING_OR_BILLING_EFFECT     5
UNRESOLVED                       3
```

Confidence:

```text
HIGH      20
MEDIUM     3
```

The three unresolved cases are all S3 episodes involving new cost drivers with no reliable historical baseline.

---

# Important Evaluation Limitation

An early comparison showed:

```text
23 / 23 agreement
```

between the agent's evidence interpretation and the human-review labels.

This must NOT be interpreted as:

```text
100% real-world accuracy
```

The human review was created using many of the same evidence patterns used by the agent.

Therefore the result is currently treated only as:

> Internal consistency between the agent's evidence interpretation and the manual review framework.

It is not an independent validation benchmark.

---

# Current Architecture

```text
FinOps Foundation FOCUS data
        ↓
AWS filtering
        ↓
Cost decomposition
        ↓
Hourly service aggregation
        ↓
24-hour rolling windows
        ↓
Previous 7-day baseline
        ↓
Leakage-safe historical percentiles
        ↓
Usage alignment
        ↓
Historical-pattern evidence
        ↓
Initial belief
        ↓
Initial action
        ↓
────────────────────────────────
If more evidence is required
────────────────────────────────
        ↓
CHECK_COST_DRIVER
        ↓
Charge-level investigation
        ↓
Sub-account investigation
        ↓
Usage comparison
        ↓
Billed-cost comparison
        ↓
Actual unit-price comparison
        ↓
Structured evidence feedback
        ↓
Belief update
        ↓
Final action
        ↓
Alert episode clustering
        ↓
Human review
```

---

# Tech Stack

The current implementation uses:

```text
Python
Pandas
NumPy
FinOps Foundation FOCUS dataset
AWS cost-and-usage billing records
Custom belief-state model
Custom decision policy
Time-series feature engineering
Rolling windows
Leakage-safe historical baselines
Historical percentile features
Entropy
Expected information gain
Cost-sensitive evaluation
Driver-level evidence retrieval
Human-in-the-loop review
```

The project currently does not use LangChain or LangGraph for the core decision logic.

The core agent behaviour comes from:

```text
state
uncertainty
sequential decision-making
evidence acquisition
belief revision
human escalation
```

---

# Key Engineering Lessons

## 1. A large cost increase does not necessarily mean an incident

Cloud spend may increase simply because workloads are consuming more resources.

## 2. Evidence semantics matter

A mathematically valid feature can still represent the wrong business concept.

## 3. Usage and pricing should be investigated separately

A FinOps system should distinguish between:

```text
more usage
higher pricing
new cost drivers
credits
discounts
accounting allocations
```

## 4. Agentic behaviour does not require an LLM

The current agent behaves sequentially:

```text
observe
reason
decide
request evidence
update belief
decide again
```

## 5. Alert rows are not the same as incidents

Rolling windows can create many repeated alerts from a single underlying event.

## 6. Real evaluation requires independent ground truth

The FOCUS dataset contains billing data but does not provide definitive incident labels.

## 7. Human evaluation can also overfit

If the reviewer uses the same decision rules as the agent, agreement is not an independent performance measure.

---

# Current Limitations

```text
Only one month of real billing data

No reliable incident ground-truth labels

Heuristic belief-update weights

Heuristic decision thresholds

Belief scores are not calibrated probabilities

Historical-pattern thresholds are manually chosen

No reliable deployment information

No reliable production/development environment signal

Tags are heterogeneous and incomplete

New cost drivers require external operational context

Current manual review is not independent

Long-term seasonality cannot yet be evaluated
```

---

# Next Work

## Blinded Human Evaluation

The next evaluation will remove agent-generated information from the human-review interface.

The reviewer should NOT see:

```text
agent feedback
initial belief
final belief
initial action
final action
```

The reviewer will instead see only raw evidence such as:

```text
service
time period
cost movement
billed-cost movement
usage movement
unit-price movement
charge description
sub-account
historical baseline
```

The human judgement will then be compared against the frozen agent only after the labels have been created.

---

## External Operational Evidence

The unresolved S3 events show that billing data alone is not always enough.

Future evidence sources could include:

```text
deployment history
CloudWatch metrics
application traffic
network-flow information
business growth indicators
change-management systems
service ownership metadata
incident-management records
```

---

## Learned and Calibrated Beliefs

Future reviewed outcomes could be used to replace parts of the manually designed belief model.

Possible methods include:

```text
logistic regression
gradient boosting
Bayesian models
Platt scaling
isotonic calibration
```

---

## Evidence-Value Learning

The synthetic version already experimented with:

```text
entropy
expected information gain
evidence cost
```

Future work could learn the real value of different evidence sources from historical investigations.

---

## Agent Observability

A production system should store the complete decision trajectory:

```text
initial observation
initial belief
initial action
evidence requested
reason evidence was selected
evidence returned
belief change
final action
human override
final outcome
```

---

# Future Production Architecture

A production version could evolve toward:

```text
Cloud billing APIs
        ↓
Scheduled / streaming ingestion
        ↓
Feature pipeline
        ↓
Decision agent
        ↓
Evidence tools
        ↓
Decision API
        ↓
PostgreSQL / event store
        ↓
Slack / PagerDuty / ticketing
        ↓
Human review
        ↓
Feedback store
        ↓
Model / policy improvement
```

Potential supporting technologies could include:

```text
AWS
Kafka
Airflow
PostgreSQL
Docker
FastAPI
MLflow
CloudWatch
CI/CD
```

These are future production-integration targets and should not be interpreted as components already implemented in the current version unless explicitly added later.

---

# Current Status

The project has progressed through:

```text
Synthetic uncertainty model
        ↓
Cost-sensitive decision policy
        ↓
Environment-aware thresholds
        ↓
Sequential evidence acquisition
        ↓
Entropy / information-gain experiments
        ↓
Real FOCUS billing data
        ↓
Leakage-safe feature engineering
        ↓
Usage-cost alignment
        ↓
Real driver-level investigation
        ↓
EffectiveCost failure discovery
        ↓
Billing-price correction
        ↓
Two-stage real agent
        ↓
Alert episode clustering
        ↓
Manual episode review
        ↓
Blinded independent evaluation next
```

The current focus is on building an agent whose decisions are:

```text
evidence-driven
auditable
uncertainty-aware
safe to escalate
easy to investigate
honest about what is still unknown
```

The long-term goal is a FinOps agent that can investigate unusual cloud spending, gather additional evidence when needed, explain why its decision changed, involve humans when uncertainty remains, and improve from reviewed operational outcomes.
