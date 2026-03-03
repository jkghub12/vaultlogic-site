# yieldscout.py
import requests

class DeFiYieldScout:
    def __init__(self):
        # Aave V3 Base Market - Your working endpoint
        self.aave_api = "https://api.aavescan.com/v2/latest?market=aave-v3-base"
        # Aerodrome Public API
        self.aero_api = "https://api.aerodrome.finance/v1/pools"

    def get_aave_yield(self):
        """Fetches Aave V3 Supply APY for USDC"""
        try:
            response = requests.get(self.aave_api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for asset in data:
                    if asset.get("symbol") == "USDC":
                        # currentLiquidityRate is the supply APR
                        # Raw value is in Rays (10^27), convert to %
                        raw_rate = float(asset.get("currentLiquidityRate", 0))
                        return round((raw_rate / 10**25), 2)
            return 0.0
        except Exception:
            return 0.0

    def get_aerodrome_yield(self):
        """Fetches Aerodrome USDC/WETH pool APY"""
        try:
            response = requests.get(self.aero_api, timeout=10)
            if response.status_code == 200:
                pools = response.json().get("data", [])
                for pool in pools:
                    # Target the volatile USDC/WETH pool (highest typical yield)
                    if "USDC" in pool.get("symbol", "") and "WETH" in pool.get("symbol", ""):
                        # Aerodrome uses 'apr' for their emissions yield
                        return round(float(pool.get("apr", 0.0)), 2)
            return 0.0
        except Exception:
            return 0.0

    def get_best_yield(self):
        """Compares all active protocols and returns the winner"""
        yields = {
            "Aave V3": self.get_aave_yield(),
            "Aerodrome": self.get_aerodrome_yield()
        }
        
        # Find the protocol with the highest APY
        best_protocol = max(yields, key=yields.get)
        best_apy = yields[best_protocol]

        # If everything is 0, return a fallback
        if best_apy == 0:
            return {"protocol": "Searching...", "apy": 0.0}
            
        return {"protocol": best_protocol, "apy": best_apy}