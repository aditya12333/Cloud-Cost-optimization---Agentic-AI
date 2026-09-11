import pandas as pd
import sys
from pathlib import Path

# Make sure the project's `src` directory is on sys.path so imports work
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from real_driver_evidence import (
    load_driver_data,
    check_cost_driver,
)


driver_data = load_driver_data()


cases = [
    {
        "name": "CASE 1",
        "service": "Amazon Elastic File System",
        "hour": "2024-09-19 20:00:00",
    },
    {
        "name": "CASE 2",
        "service": "Amazon Elastic File System",
        "hour": "2024-09-28 17:00:00",
    },
]


for case in cases:

    evidence, _ = check_cost_driver(
        driver_data,
        service_name=case["service"],
        current_hour=case["hour"],
    )

    print("\n================================")
    print(case["name"])
    print("================================")

    print(
        "Hour:",
        case["hour"],
    )

    print(
        "Driver:",
        evidence[
            "charge_description"
        ],
    )

    print(
        "Sub-account:",
        evidence[
            "sub_account"
        ],
    )

    print("\nEFFECTIVE COST")

    print(
        "Current:",
        evidence[
            "current_effective_cost_24h"
        ],
    )

    print(
        "Baseline:",
        evidence[
            "baseline_effective_cost_24h"
        ],
    )

    print(
        "Change %:",
        evidence[
            "cost_change_pct"
        ],
    )

    print("\nBILLED COST")

    print(
        "Current:",
        evidence[
            "current_billed_cost_24h"
        ],
    )

    print(
        "Baseline:",
        evidence[
            "baseline_billed_cost_24h"
        ],
    )

    print(
        "Change %:",
        evidence[
            "billed_cost_change_pct"
        ],
    )

    print("\nUSAGE")

    print(
        "Current:",
        evidence[
            "current_quantity_24h"
        ],
    )

    print(
        "Baseline:",
        evidence[
            "baseline_quantity_24h"
        ],
    )

    print(
        "Change %:",
        evidence[
            "usage_change_pct"
        ],
    )

    print("\nPRICING")

    print(
        "Billed unit-cost change %:",
        evidence[
            "unit_cost_change_pct"
        ],
    )

    print(
        "List-price change %:",
        evidence[
            "list_unit_price_change_pct"
        ],
    )

    print(
        "Current list price:",
        evidence[
            "current_list_unit_price"
        ],
    )

    print(
        "Baseline list price:",
        evidence[
            "baseline_list_unit_price"
        ],
    )

    print(
        "\nNew driver:",
        evidence[
            "is_new_driver"
        ],
    )