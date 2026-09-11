import pandas as pd


DATA_PATH = "data/real/aws_hourly_service_cost.csv"

df = pd.read_csv(
    DATA_PATH,
    parse_dates=["hour"]
)

total_hours = (
    int(
        (df["hour"].max() - df["hour"].min())
        / pd.Timedelta(hours=1)
    )
    + 1
)

print("\n----------------------------")
print("TOTAL POSSIBLE HOURS")
print("----------------------------")

print(total_hours)


service_coverage = (
    df.groupby("ServiceName")
    .agg(
        observed_hours=("hour", "nunique"),
        total_cost=("effective_cost", "sum")
    )
    .reset_index()
)

service_coverage["coverage_pct"] = (
    service_coverage["observed_hours"]
    / total_hours
    * 100
)

service_coverage = service_coverage.sort_values(
    "observed_hours",
    ascending=False
)


print("\n----------------------------")
print("TOP SERVICES BY HOURLY COVERAGE")
print("----------------------------")

print(
    service_coverage.head(20).to_string(index=False)
)


print("\n----------------------------")
print("SERVICES WITH >= 80% COVERAGE")
print("----------------------------")

high_coverage = service_coverage[
    service_coverage["coverage_pct"] >= 80
]

print(
    high_coverage.to_string(index=False)
)

print(
    "\nNumber of services with >=80% coverage:",
    len(high_coverage)
)

# ==================================================
# HOURLY COST DISTRIBUTION
# ==================================================

print("\n----------------------------")
print("HOURLY COST DISTRIBUTION")
print("----------------------------")

service_stats = (
    df.groupby("ServiceName")
    .agg(
        observed_hours=("hour", "nunique"),
        total_cost=("effective_cost", "sum"),
        mean_hourly_cost=("effective_cost", "mean"),
        std_hourly_cost=("effective_cost", "std"),
        min_hourly_cost=("effective_cost", "min"),
        max_hourly_cost=("effective_cost", "max"),
        positive_hours=("effective_cost", lambda x: (x > 0).sum()),
        zero_hours=("effective_cost", lambda x: (x == 0).sum()),
        negative_hours=("effective_cost", lambda x: (x < 0).sum()),
    )
    .reset_index()
)

# Keep services with strong hourly coverage
service_stats = service_stats[
    service_stats["observed_hours"] >= 576
]

# Rank by total cost
service_stats = service_stats.sort_values(
    "total_cost",
    ascending=False
)

print(
    service_stats.head(20).to_string(index=False)
)

print("\n----------------------------")
print("DATADOG COVERAGE")
print("----------------------------")

print(
    service_coverage[
        service_coverage["ServiceName"] == "Datadog"
    ].to_string(index=False)
)