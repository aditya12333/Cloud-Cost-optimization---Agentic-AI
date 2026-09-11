import pandas as pd
import numpy as np


DATA_PATH = "data/real/aws_hourly_driver_usage.csv"


def load_driver_data():

    return pd.read_csv(
        DATA_PATH,
        parse_dates=["hour"],
    )


def safe_pct_change(current, baseline):

    if (
        baseline is None
        or pd.isna(baseline)
        or baseline == 0
    ):
        return np.nan

    return (
        (current - baseline)
        / baseline
        * 100
    )


def check_cost_driver(
    df,
    service_name,
    current_hour,
):

    current_hour = pd.Timestamp(
        current_hour
    )

    # ==================================================
    # CURRENT 24 HOURS
    # ==================================================

    current_start = (
        current_hour
        - pd.Timedelta(hours=23)
    )

    current = df[
        (df["ServiceName"] == service_name)
        & (df["hour"] >= current_start)
        & (df["hour"] <= current_hour)
    ].copy()


    # ==================================================
    # PREVIOUS 7 DAYS
    # ==================================================

    baseline_end = current_start

    baseline_start = (
        baseline_end
        - pd.Timedelta(days=7)
    )

    baseline = df[
        (df["ServiceName"] == service_name)
        & (df["hour"] >= baseline_start)
        & (df["hour"] < baseline_end)
    ].copy()


    driver_columns = [
        "ChargeDescription",
        "ConsumedUnit",
        "SubAccountName",
    ]


    # ==================================================
    # CURRENT DRIVER DATA
    # ==================================================

    current_drivers = (
        current.groupby(
            driver_columns,
            dropna=False,
        )
        .agg(
            current_effective_cost_24h=(
                "effective_cost",
                "sum",
            ),

            current_billed_cost_24h=(
                "billed_cost",
                "sum",
            ),

            current_quantity_24h=(
                "consumed_quantity",
                "sum",
            ),

            current_list_unit_price=(
                "mean_list_unit_price",
                "mean",
            ),

            current_contracted_unit_price=(
                "mean_contracted_unit_price",
                "mean",
            ),
        )
    )


    # ==================================================
    # BASELINE DRIVER DATA
    # ==================================================

    baseline_drivers = (
        baseline.groupby(
            driver_columns,
            dropna=False,
        )
        .agg(
            baseline_effective_cost_7d=(
                "effective_cost",
                "sum",
            ),

            baseline_billed_cost_7d=(
                "billed_cost",
                "sum",
            ),

            baseline_quantity_7d=(
                "consumed_quantity",
                "sum",
            ),

            baseline_list_unit_price=(
                "mean_list_unit_price",
                "mean",
            ),

            baseline_contracted_unit_price=(
                "mean_contracted_unit_price",
                "mean",
            ),
        )
    )


    # Convert previous 7 days into expected
    # 24-hour values.

    baseline_drivers[
        "baseline_effective_cost_24h"
    ] = (
        baseline_drivers[
            "baseline_effective_cost_7d"
        ] / 7
    )

    baseline_drivers[
        "baseline_billed_cost_24h"
    ] = (
        baseline_drivers[
            "baseline_billed_cost_7d"
        ] / 7
    )

    baseline_drivers[
        "baseline_quantity_24h"
    ] = (
        baseline_drivers[
            "baseline_quantity_7d"
        ] / 7
    )


    # ==================================================
    # COMBINE CURRENT + BASELINE
    # ==================================================

    comparison = current_drivers.join(
        baseline_drivers[
            [
                "baseline_effective_cost_24h",
                "baseline_billed_cost_24h",
                "baseline_quantity_24h",
                "baseline_list_unit_price",
                "baseline_contracted_unit_price",
            ]
        ],
        how="outer",
    )


    zero_columns = [
        "current_effective_cost_24h",
        "current_billed_cost_24h",
        "current_quantity_24h",
        "baseline_effective_cost_24h",
        "baseline_billed_cost_24h",
        "baseline_quantity_24h",
    ]

    comparison[
        zero_columns
    ] = (
        comparison[
            zero_columns
        ]
        .fillna(0.0)
    )


    # ==================================================
    # EFFECTIVE COST CHANGE
    # ==================================================

    comparison[
        "absolute_effective_cost_change"
    ] = (
        comparison[
            "current_effective_cost_24h"
        ]
        -
        comparison[
            "baseline_effective_cost_24h"
        ]
    )


    comparison[
        "effective_cost_change_pct"
    ] = comparison.apply(
        lambda row: safe_pct_change(
            row[
                "current_effective_cost_24h"
            ],
            row[
                "baseline_effective_cost_24h"
            ],
        ),
        axis=1,
    )


    # ==================================================
    # BILLED COST CHANGE
    # ==================================================

    comparison[
        "billed_cost_change_pct"
    ] = comparison.apply(
        lambda row: safe_pct_change(
            row[
                "current_billed_cost_24h"
            ],
            row[
                "baseline_billed_cost_24h"
            ],
        ),
        axis=1,
    )


    # ==================================================
    # USAGE CHANGE
    # ==================================================

    comparison[
        "usage_change_pct"
    ] = comparison.apply(
        lambda row: safe_pct_change(
            row[
                "current_quantity_24h"
            ],
            row[
                "baseline_quantity_24h"
            ],
        ),
        axis=1,
    )


    # ==================================================
    # BILLED UNIT COST
    #
    # Important:
    # use BilledCost for pricing evidence.
    # Do not use EffectiveCost as unit price.
    # ==================================================

    comparison[
        "current_billed_unit_cost"
    ] = np.where(
        comparison[
            "current_quantity_24h"
        ] > 0,

        comparison[
            "current_billed_cost_24h"
        ]
        /
        comparison[
            "current_quantity_24h"
        ],

        np.nan,
    )


    comparison[
        "baseline_billed_unit_cost"
    ] = np.where(
        comparison[
            "baseline_quantity_24h"
        ] > 0,

        comparison[
            "baseline_billed_cost_24h"
        ]
        /
        comparison[
            "baseline_quantity_24h"
        ],

        np.nan,
    )


    comparison[
        "billed_unit_cost_change_pct"
    ] = comparison.apply(
        lambda row: safe_pct_change(
            row[
                "current_billed_unit_cost"
            ],
            row[
                "baseline_billed_unit_cost"
            ],
        ),
        axis=1,
    )


    # ==================================================
    # LIST PRICE CHANGE
    # ==================================================

    comparison[
        "list_unit_price_change_pct"
    ] = comparison.apply(
        lambda row: safe_pct_change(
            row[
                "current_list_unit_price"
            ],
            row[
                "baseline_list_unit_price"
            ],
        ),
        axis=1,
    )


    # ==================================================
    # CONTRACTED PRICE CHANGE
    # ==================================================

    comparison[
        "contracted_unit_price_change_pct"
    ] = comparison.apply(
        lambda row: safe_pct_change(
            row[
                "current_contracted_unit_price"
            ],
            row[
                "baseline_contracted_unit_price"
            ],
        ),
        axis=1,
    )


    # ==================================================
    # NEW DRIVER
    # ==================================================

    comparison[
        "is_new_driver"
    ] = (
        (
            comparison[
                "baseline_effective_cost_24h"
            ] == 0
        )
        &
        (
            comparison[
                "current_effective_cost_24h"
            ] > 0
        )
    )


    # ==================================================
    # FIND DOMINANT COST DRIVER
    # ==================================================

    comparison = comparison.sort_values(
        "absolute_effective_cost_change",
        ascending=False,
    )


    if comparison.empty:

        return None, comparison


    top_driver = (
        comparison.iloc[0]
    )

    driver_identity = (
        comparison.index[0]
    )


    # ==================================================
    # STRUCTURED EVIDENCE
    # ==================================================

    evidence = {

        "service_name":
            service_name,

        "current_hour":
            current_hour,

        "charge_description":
            driver_identity[0],

        "consumed_unit":
            driver_identity[1],

        "sub_account":
            driver_identity[2],


        # ------------------------------------------
        # EFFECTIVE COST
        # ------------------------------------------

        "current_effective_cost_24h":
            top_driver[
                "current_effective_cost_24h"
            ],

        "baseline_effective_cost_24h":
            top_driver[
                "baseline_effective_cost_24h"
            ],

        "cost_change_pct":
            top_driver[
                "effective_cost_change_pct"
            ],


        # ------------------------------------------
        # BILLED COST
        # ------------------------------------------

        "current_billed_cost_24h":
            top_driver[
                "current_billed_cost_24h"
            ],

        "baseline_billed_cost_24h":
            top_driver[
                "baseline_billed_cost_24h"
            ],

        "billed_cost_change_pct":
            top_driver[
                "billed_cost_change_pct"
            ],


        # ------------------------------------------
        # USAGE
        # ------------------------------------------

        "current_quantity_24h":
            top_driver[
                "current_quantity_24h"
            ],

        "baseline_quantity_24h":
            top_driver[
                "baseline_quantity_24h"
            ],

        "usage_change_pct":
            top_driver[
                "usage_change_pct"
            ],


        # ------------------------------------------
        # BILLED UNIT COST
        # ------------------------------------------

        "current_billed_unit_cost":
            top_driver[
                "current_billed_unit_cost"
            ],

        "baseline_billed_unit_cost":
            top_driver[
                "baseline_billed_unit_cost"
            ],

        # Keep this name so real_feedback.py
        # remains compatible.
        "unit_cost_change_pct":
            top_driver[
                "billed_unit_cost_change_pct"
            ],


        # ------------------------------------------
        # LIST PRICE
        # ------------------------------------------

        "current_list_unit_price":
            top_driver[
                "current_list_unit_price"
            ],

        "baseline_list_unit_price":
            top_driver[
                "baseline_list_unit_price"
            ],

        "list_unit_price_change_pct":
            top_driver[
                "list_unit_price_change_pct"
            ],


        # ------------------------------------------
        # CONTRACTED PRICE
        # ------------------------------------------

        "current_contracted_unit_price":
            top_driver[
                "current_contracted_unit_price"
            ],

        "baseline_contracted_unit_price":
            top_driver[
                "baseline_contracted_unit_price"
            ],

        "contracted_unit_price_change_pct":
            top_driver[
                "contracted_unit_price_change_pct"
            ],


        # ------------------------------------------
        # NEW DRIVER?
        # ------------------------------------------

        "is_new_driver":
            bool(
                top_driver[
                    "is_new_driver"
                ]
            ),
    }

    return evidence, comparison


# ==================================================
# TEST ON EFS FAILURE CASE
# ==================================================

if __name__ == "__main__":

    df = load_driver_data()

    evidence, comparison = (
        check_cost_driver(
            df,
            service_name=(
                "Amazon Elastic File System"
            ),
            current_hour=(
                "2024-09-22 01:00:00"
            ),
        )
    )

    print("\n----------------------------")
    print("EFS DRIVER EVIDENCE V2")
    print("----------------------------")

    if evidence is None:

        print(
            "No driver evidence found."
        )

    else:

        for key, value in (
            evidence.items()
        ):

            print(
                f"{key}: {value}"
            )


    print("\n----------------------------")
    print("TOP DRIVER SUMMARY")
    print("----------------------------")

    if evidence is not None:

        print(
            "Effective cost change %:",
            evidence[
                "cost_change_pct"
            ]
        )

        print(
            "Billed cost change %:",
            evidence[
                "billed_cost_change_pct"
            ]
        )

        print(
            "Usage change %:",
            evidence[
                "usage_change_pct"
            ]
        )

        print(
            "Billed unit-cost change %:",
            evidence[
                "unit_cost_change_pct"
            ]
        )

        print(
            "List price change %:",
            evidence[
                "list_unit_price_change_pct"
            ]
        )