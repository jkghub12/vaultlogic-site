# yieldscout.py
import requests

class DeFiYieldScout:
    def __init__(self):
        # Direct API for Aerodrome Pools
        self.aero_api = "https://api.aerodrome.finance/v1/pools"
        # Aave V3 Base Market - using the widely used subgraphs or public indexers
        self.aave_api = "https://api.aavescan.com/v2/latest?market=aave-v3-base"

    def get_aerodrome_yield(self):
        """Fetches Aerodrome USDC/WETH pool APY"""
        try:
            response = requests.get(self.aero_api, timeout=10)
            if response.status_code == 200:
                pools = response.json().get("data", [])
                for pool in pools:
                    # Look for the primary USDC/WETH volatile pool
                    if "USDC" in pool.get("symbol", "") and "WETH" in pool.get("symbol", ""):
                        # Aerodrome often returns 'apr' which is our yield
                        apr = float(pool.get("apr", 0.0))
                        return round(apr, 2)
            return 0.0
        except Exception as e:
            print(f"Aerodrome Scout Error: {e}")
            return 0.0

    def get_aave_yield(self):
        """Fetches Aave V3 Supply APY for USDC"""
        try:
            response = requests.get(self.aave_api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for asset in data:
                    if asset.get("symbol") == "USDC":
                        # Aave rates are often stored as Rays (10^27)
                        # currentLiquidityRate is the supply APY
                        raw_rate = float(asset.get("currentLiquidityRate", 0))
                        apy = (raw_rate / 10**25) * 100 # Adjusting for percentage
                        return round(apy, 2)
            return 0.0
        except Exception as e:
            print(f"Aave Scout Error: {e}")
            return 0.0

    def get_best_yield(self):
        """Compares and returns the winner"""
        aero = self.get_aerodrome_yield()
        aave = self.get_aave_yield()
        
        # We prefer Aerodrome if the yield is significantly higher (which it usually is)
        if aero >= aave and aero > 0:
            return {"protocol": "Aerodrome", "apy": aero}
        elif aave > 0:
            return {"protocol": "Aave V3", "apy": aave}
        else:
            # Fallback if both APIs fail or return 0
            return {"protocol": "Check Dashboard", "apy": 0.0}