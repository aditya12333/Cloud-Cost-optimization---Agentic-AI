# Reddit:

I am building an agent which will analyze the cost of clouds. It will decide whether the cost spikes are high enough to report, and it requires a serious examination before approval. Whether to ignore the costs or immediately inform the owner.

It can see the Billing data, resource usage, historical spending, service name, region, and environment before making any decisions, and what it cannot see is the future demand, internal discussion, customer impact, and business impact.

Here are some of the thought I came with:

what my agents cannot see:
- Normal
- Expected Pattern
- Legitimate Growth
- Cost Incident

Actions:

- Wait
- Get more evidence
- Human Permission
- Escalate

Actions:

Can someone please provide suggestions for what am I missings and what could be possible improvements? I am open to all suggestions

what are the major causes of cloud cost?

Some suggestions on optimizing cost, which i can consider while I build.

What are the other points I should considere.

How do engineers distinguish legitimate growth from incidents?

What kinds of cost anomalies are dangerous?

## Discussions: 
- User_response and disscussion: 
    - Major cost is only the database storage for me. That's why I used supabase.
    - Can you also build an agent that will predict what a specific code change costs before we approve it?
    - my question: Sounds interesting. Can you please give a simple idea from your recent experience?

    - hey there, the tricky bit with this kind of agent is usually the decision boundaries. when does a spike go from 'ignore' to 'report' when you don't have the business context to weigh it against

    - I am thinking ruled- based for now I am gathering all the possibilities and requirements
    - rule-based works to start but the thresholds go stale pretty fast, especially across different services and environments. a 30% spike on a dev environment is noise, same spike on prod during a quiet period could be a leaked resource burning money

    - That's great point, It gave idea about behavior on prod and dev which I can considered Also agree with the limitations of rule based. Initially I am considering it rule based, I can enhance it in future. At the moment training on historical data could be expensive

    - starting lean and layering on is the right call. fwiw the per-service baselines are where rule-based gets tricky fast though, compute and storage spike completely differently and a threshold that works for one service looks wrong on another