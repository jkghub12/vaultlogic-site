import asyncio

async def get_all_yields():
    """
    Returns the specific high-performance and institutional 
    yields verified for the Phase Alpha demo.
    """
    # We return the exact list you mentioned to ensure the demo is consistent
    return [
        {
            "protocol": "UNISWAP V3",
            "apy": "179.0",
            "asset": "WETH/USDC"
        },
        {
            "protocol": "MORPHO BLUE",
            "apy": "3.60",
            "asset": "STEAK / GT USDCP"
        },
        {
            "protocol": "UNISWAP V3",
            "apy": "3.50",
            "asset": "USDC/ETH"
        },
        {
            "protocol": "AAVE V3",
            "apy": "2.87",
            "asset": "USDC"
        },
        {
            "protocol": "AERODROME",
            "apy": "12.40",
            "asset": "cbBTC/WETH"
        }
    ]

def heartbeat_monitor():
    return True