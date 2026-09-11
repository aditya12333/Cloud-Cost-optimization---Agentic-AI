import pandas as pd


DATA_PATH = "data/real/focus_data_table.csv.gz"


SELECTED_SERVICES = [
    "Amazon Relational Database Service",
    "Amazon Elastic File System",
    "Amazon Simple Storage Service",
    "Amazon Elastic Container Service for Kubernetes",
]


columns = [
    "ProviderName",
    "ServiceName",
    "ChargeCategory",
    "ConsumedQuantity",
    "ConsumedUnit",
    "EffectiveCost",
]


df = pd.read_csv(
    DATA_PATH,
    usecols=columns,
    low_memory=False,
)


df = df[
    (df["ProviderName"] == "AWS")
    & (df["ChargeCategory"] == "Usage")
    & (df["ServiceName"].isin(SELECTED_SERVICES))
].copy()


for service, service_df in df.groupby("ServiceName"):

    print("\n================================")
    print(service)
    print("================================")

    summary = (
        service_df.groupby(
            "ConsumedUnit",
            dropna=False
        )
        .agg(
            total_quantity=("ConsumedQuantity", "sum"),
            total_cost=("EffectiveCost", "sum"),
            billing_rows=("EffectiveCost", "size"),
        )
        .sort_values(
            "total_cost",
            ascending=False
        )
    )

    print(
        summary.head(15).to_string()
    )