case = {
    "current_cost": 1450,
    "baseline_cost": 1000,
    "current_usage": 105000,
    "baseline_usage": 100000,
    "recent_deployment": True,
    "expected_pattern": False
}

def cost_change(case):
    """
    Calculate the cost change percentage between current and baseline costs.

    Parameters:
    case (dict): A dictionary containing current and baseline costs.

    Returns:
    float: The percentage change in cost.
    """
    current_cost = case["current_cost"]
    baseline_cost = case["baseline_cost"]
    
    if baseline_cost == 0:
        raise ValueError("Baseline cost cannot be zero.")
    
    cost_change_percentage = ((current_cost - baseline_cost) / baseline_cost) * 100
    return cost_change_percentage

def usage_change(case):
    """
    Calculate the usage change percentage between current and baseline usage.

    Parameters:
    case (dict): A dictionary containing current and baseline usage.

    Returns:
    float: The percentage change in usage.
    """
    current_usage = case["current_usage"]
    baseline_usage = case["baseline_usage"]
    
    if baseline_usage == 0:
        raise ValueError("Baseline usage cannot be zero.")
    
    usage_change_percentage = ((current_usage - baseline_usage) / baseline_usage) * 100
    return usage_change_percentage

def unit_cost(case):
    """
    Calculate the unit cost based on current cost and current usage.

    Parameters:
    case (dict): A dictionary containing current cost and current usage.

    Returns:
    float: The unit cost.
    """
    current_cost = case["current_cost"]
    current_usage = case["current_usage"]
    
    if current_usage == 0:
        raise ValueError("Current usage cannot be zero.")
    
    unit_cost_value = current_cost / current_usage
    baseline_unit_cost = case["baseline_cost"] / case["baseline_usage"]
    return unit_cost_value, baseline_unit_cost

def unit_cost_change(case):
    """
    Calculate the unit cost change percentage between current and baseline unit costs.

    Parameters:
    case (dict): A dictionary containing current and baseline costs and usage.

    Returns:
    float: The percentage change in unit cost.
    """
    unit_cost_value, baseline_unit_cost = unit_cost(case)
    
    if baseline_unit_cost == 0:
        raise ValueError("Baseline unit cost cannot be zero.")
    
    unit_cost_change_percentage = ((unit_cost_value - baseline_unit_cost) / baseline_unit_cost) * 100
    return unit_cost_change_percentage

# result = cost_change(case)
# usage_result = usage_change(case)
# unit_cost_result, baseline_unit_cost = unit_cost(case)
# unit_cost_change_result = unit_cost_change(case)
# print(f"Cost change percentage: {result:.2f}%")
# print(f"Usage change percentage: {usage_result:.2f}%")
# print(f"Unit cost: {unit_cost_result:.5f}, Baseline unit cost: {baseline_unit_cost:.5f}")
# print(f"Unit cost change percentage: {unit_cost_change_result:.2f}%")