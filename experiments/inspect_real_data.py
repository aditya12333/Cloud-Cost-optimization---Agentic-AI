import pandas as pd

DATA_PATH = "data/real/focus_data_table.csv.gz"

df = pd.read_csv(
    DATA_PATH,
    low_memory=False
)

print("\nSHAPE")
print(df.shape)

# print("\nCOLUMNS")
# for column in df.columns:
#     print(column)

# print("\nFIRST 3 ROWS")
# print(df.head(3).to_string())

# print("\nDATA TYPES")
# print(df.dtypes)

# print("\nMISSING VALUES")
# print(df.isna().sum().sort_values(ascending=False).head(20))

# # ==================================================
# # PROVIDER ANALYSIS
# # ==================================================

# print("\n----------------------------")
# print("PROVIDERS")
# print("----------------------------")

# print(df["ProviderName"].value_counts(dropna=False))


# ==================================================
# AWS DATA
# ==================================================

aws_df = df[df["ProviderName"] == "AWS"].copy()

print("\n----------------------------")
print("AWS SHAPE")
print("----------------------------")

print(aws_df.shape)


# Convert timestamps
aws_df["ChargePeriodStart"] = pd.to_datetime(
    aws_df["ChargePeriodStart"]
)

print("\n----------------------------")
print("AWS TIME COVERAGE")
print("----------------------------")

print(
    "Start:",
    aws_df["ChargePeriodStart"].min()
)

print(
    "End:",
    aws_df["ChargePeriodStart"].max()
)

print(
    "Unique days:",
    aws_df["ChargePeriodStart"].dt.date.nunique()
)