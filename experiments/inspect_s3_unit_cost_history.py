import pandas as pd


DATA_PATH = "data/real/aws_real_daily_alignment.csv"


df = pd.read_csv(
    DATA_PATH,
    parse_dates=["hour"],
)

valid = df[
    df["unit_cost_change_pct"].notna()
].copy()


EVENT_DATE = pd.Timestamp("2024-09-18")


event = valid[
    valid["hour"] == EVENT_DATE
].iloc[0]


event_unit_cost_change = (
    event["unit_cost_change_pct"]
)

event_gap = (
    event["cost_usage_gap_pct"]
)


# Only use observations BEFORE the event
history = valid[
    valid["hour"] < EVENT_DATE
].copy()


unit_cost_percentile = (
    (
        history["unit_cost_change_pct"]
        < event_unit_cost_change
    ).mean()
    * 100
)


gap_percentile = (
    (
        history["cost_usage_gap_pct"]
        < event_gap
    ).mean()
    * 100
)


print("\n----------------------------")
print("S3 STORAGE EVENT HISTORY")
print("----------------------------")

print(
    "Historical observations:",
    len(history)
)

print(
    "Event unit-cost change:",
    event_unit_cost_change
)

print(
    "Unit-cost-change percentile:",
    unit_cost_percentile
)

print(
    "Event cost/usage gap:",
    event_gap
)

print(
    "Cost/usage-gap percentile:",
    gap_percentile
)