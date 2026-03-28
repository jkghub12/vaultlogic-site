import asyncio

async def get_all_yields():
    """
    Returns the specific institutional yields verified for Phase Alpha.
    """
    return [
        {"protocol": "UNISWAP V3", "apy": 179.0, "asset": "WETH/USDC"},
        {"protocol": "MORPHO BLUE", "apy": 3.60, "asset": "STEAK / GT USDCP"},
        {"protocol": "UNISWAP V3", "apy": 3.50, "asset": "USDC/ETH"},
        {"protocol": "AAVE V3", "apy": 2.87, "asset": "USDC"},
        {"protocol": "AERODROME", "apy": 12.40, "asset": "cbBTC/WETH"}
    ]

def evaluate_opportunity(current_apy, target_apy, capital=500, gas_price_gwei=0.0012):
    """
    CONSERVATIVE FILTER (Industrial Grade):
    - Requires 3x coverage of gas costs.
    - Minimum spread (Delta) of 5.0% to justify contract risk.
    """
    # Base Network gas estimate (~250k gas units for a swap/rebalance)
    eth_price = 2500
    gas_cost_usd = (250000 * gas_price_gwei * 1e-9) * eth_price
    
    apy_delta = float(target_apy) - float(current_apy)
    
    # Projected gain over 7 days (the settlement window)
    projected_gain = (capital * (apy_delta / 100)) * (7/365)
    
    # Deterministic Gate
    is_viable = (projected_gain > (gas_cost_usd * 3)) and (apy_delta >= 5.0)
    
    return {
        "is_viable": is_viable,
        "delta": round(apy_delta, 2),
        "cost": round(gas_cost_usd, 4),
        "gain": round(projected_gain, 4)
    }