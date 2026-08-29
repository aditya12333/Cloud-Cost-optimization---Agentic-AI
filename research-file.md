# Problem Statement

### The agent observes cloud cost, usage, and recent operational information. It must select whether to wait, investigate, request more evidence, or escalate because the cause of an unusual cost increase is not known.

## Hidden Information
- Normal
- Expected Pattern
- Legitimate Growth
- Cost Incident

## Action
- Wait
- Get more evidence
- Human Permission
- Escalate

### Use of Clouds based on cmpany size:
 - Small Startups - prefere to spends less on clouds and try to optimize the cost.
 - Mid- sized company - Have tenedency to spend more than early startups.
 - Large scaled company - Have huge budget and their cost fluctuations varied alot.

 ### some of the causes for high costs:
  - Use of resources recklessly without proper monitering.
  - Continuous running of resources which shouldn't be. OR forgot to shut down the resources which are not require anymore.
  - Allocation of compute resources more than requirements or proper calculations.

### The cost of Success Optimize Cloud Costs With The Right Software (source: https://www.cloudzero.com/blog/cloud-costs/)

 **Metrics in context –** The right cloud cost optimization platform should be able to connect engineering decisions with business outcomes. The primary focus is helping engineers understand the cost of their actions. This way, they can see breaking something as an opportunity to learn.

 **Cloud cost telemetry –** A core capability of your cloud cost optimization software should be combining application metrics with cost data so you can understand your unit cost, cost per customer, and cost per feature, as well as what happens to your costs as your customer base grows or shrinks.

 **Rapid and early anomaly detection –** Going beyond just performance monitoring, this software needs to have speed as a key feature. If your developers start logging more data, this comes at a great cost. If they forget to turn off data logging, they will generate thousands in additional costs per day. To manage this kind of activity, this platform needs to be able to keep up with the changes in your organization and detect anomalies right away. “If you wait days to be notified — like you would with traditional cloud optimization solutions — you will already have spent more than you intended,”

 **Output direction –** There are many teams involved in cloud cost optimization — engineers, finance, executives, and more. The software you use needs to be able to direct notifications to the people who can take action. With CloudZero, you can see your cloud spend in metrics that matter most to the different teams in your organization — and use that cost intelligence to make informed product, engineering, and business decisions.













 # Problem Statement

The agent observes cloud cost, usage, and recent operational information.
It must select whether to wait, investigate, request more evidence,
or escalate because the cause of an unusual cost increase is not known.

## Hidden States

- Normal variation
- Expected recurring pattern
- Legitimate workload growth
- Cost incident

## Actions

- Wait
- Get more evidence
- Ask a human
- Escalate

## Initial Research Findings

### Cost alone may not be sufficient

Cloud cost should be interpreted together with workload and business
metrics. Useful measures may include:

- Cost per request
- Cost per customer
- Cost per service
- Cost per feature
- Resource utilization

Source: CloudZero, "Optimize Cloud Costs With The Right Software"

### Possible causes of unexpected cloud cost

Current hypotheses:

- Resources left running unintentionally
- Over-provisioned compute
- Unexpected increases in logging or data processing
- Increased workload
- Recurring batch or scheduled workloads

These are hypotheses and need verification from additional sources
and practitioner discussions.

### Detection latency may have a cost

A cloud cost incident can continue accumulating expenditure while it
remains undetected. Therefore, waiting for more evidence also has a
potential cost.

Source: CloudZero

### Escalation depends on stakeholder

Possible stakeholders include:

- Engineering
- FinOps / cloud operations
- Finance
- Product or business teams

The appropriate recipient may depend on the suspected cause.

## Open Research Questions

- How should "normal" cloud cost be defined?
- Should the agent compare absolute cost or unit cost?
- How much historical data is needed?
- How should recurring patterns such as month-end workloads be handled?
- Which signals distinguish legitimate growth from waste?
- When is the cost of waiting greater than the cost of investigating?
- Which incidents should automatically escalate to a human?
- Should thresholds depend on service or workload?