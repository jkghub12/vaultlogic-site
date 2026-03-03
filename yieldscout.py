# yieldscout.py
import requests

class DeFiYieldScout:
    def __init__(self):
        # Aerodrome API endpoint for Base
        self.aero_api = "https://api.aerodrome.finance/v1/pools"
        # Aave V3 Base Market
        self.aave_api = "https://api.aavescan.com/v2/latest?market=aave-v3-base"

    def get_aerodrome_yield(self):
        """Fetches Aerodrome USDC pool APY"""
        try:
            response = requests.get(self.aero_api, timeout=10)
            pools = response.json().get("data", [])
            for pool in pools:
                # Target major USDC pools, preferably volatile for higher yield
                if "USDC" in pool.get("symbol", "") and pool.get("isStable") is False:
                    # 'apr' is typically used for rewards
                    return float(pool.get("apr", 0.0))
            return 0.0
        except Exception:
            return 0.0

    def get_aave_yield(self):
        """Fetches Aave V3 Supply APY"""
        try:
            response = requests.get(self.aave_api, timeout=10)
            data = response.json()
            for asset in data:
                if asset.get("symbol") == "USDC":
                    raw_rate = float(asset.get("currentLiquidityRate", 0))
                    return (raw_rate / 10**25) * 100
            return 0.0
        except Exception:
            return 0.0

    def get_best_yield(self):
        """Compares Aerodrome and Aave"""
        aero_apy = self.get_aerodrome_yield()
        aave_apy = self.get_aave_yield()
        
        # Prioritize Aero, but take Aave if Aero is 0
        if aero_apy > 0:
            return {"protocol": "Aerodrome", "apy": round(aero_apy, 2)}
        elif aave_apy > 0:
            return {"protocol": "Aave V3", "apy": round(aave_apy, 2)}
        else:
            return {"protocol": "No Yield", "apy": 0.0}