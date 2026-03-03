# yieldscout.py
import requests

class DeFiYieldScout:
    def __init__(self):
        # Official Aerodrome API - the most reliable source for Base yields
        self.aero_api = "https://api.aerodrome.finance/v1/pools"
        # Aavescan remains the best public indexer for Aave V3 Base
        self.aave_api = "https://api.aavescan.com/v2/latest?market=aave-v3-base"

    def get_aave_yield(self):
        """Directly fetches Aave V3 USDC Supply APY"""
        try:
            response = requests.get(self.aave_api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for asset in data:
                    if asset.get("symbol") == "USDC":
                        # Raw rate is in Ray units (10^27). 
                        # To get %, we divide by 10^25.
                        raw_rate = float(asset.get("currentLiquidityRate", 0))
                        apy = round((raw_rate / 10**25), 2)
                        print(f"DEBUG: Aave USDC APY found: {apy}%")
                        return apy
            return 0.0
        except Exception as e:
            print(f"DEBUG: Aave API Error: {e}")
            return 0.0

    def get_aerodrome_yield(self):
        """Directly fetches Aerodrome USDC pool APR"""
        try:
            response = requests.get(self.aero_api, timeout=10)
            if response.status_code == 200:
                pools = response.json().get("data", [])
                for pool in pools:
                    # We look for the highly liquid USDC/WETH volatile pool
                    symbol = pool.get("symbol", "")
                    if "USDC" in symbol and "WETH" in symbol:
                        # Aerodrome uses 'apr' for emissions-based yield
                        apr = round(float(pool.get("apr", 0.0)), 2)
                        print(f"DEBUG: Aerodrome {symbol} APR found: {apr}%")
                        return apr
            return 0.0
        except Exception as e:
            print(f"DEBUG: Aerodrome API Error: {e}")
            return 0.0

    def get_best_yield(self):
        """Simple comparison logic"""
        aave = self.get_aave_yield()
        aero = self.get_aerodrome_yield()
        
        # In March 2026, Aerodrome is usually higher due to emissions
        if aero >= aave and aero > 0:
            return {"protocol": "Aerodrome", "apy": aero}
        elif aave > 0:
            return {"protocol": "Aave V3", "apy": aave}
        else:
            return {"protocol": "Check Logs", "apy": 0.0}