# yieldscout.py
import requests

class DeFiYieldScout:
    def __init__(self):
        # Base network USDC addresses
        self.usdc_address = "0x833589fcd6edb6e08f4c7c32e4f51b640003058f"
        
    def get_aave_yield(self):
        """Fetches Aave V3 Supply APY for USDC on Base"""
        try:
            # Using Aavescan public API for Base V3
            url = "https://api.aavescan.com/v2/latest?market=aave-v3-base"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # Find USDC in the list of assets
            for asset in data:
                if asset.get("symbol") == "USDC":
                    # currentLiquidityRate is the supply APR in Aave terms
                    # Divide by 1e25 to get the decimal percentage
                    raw_rate = float(asset.get("currentLiquidityRate", 0))
                    apy = (raw_rate / 10**25) * 100
                    return round(apy, 2)
            return 0.0
        except Exception as e:
            print(f"Aave Error: {e}")
            return 0.0

    def get_aerodrome_yield(self):
        """Fetches Aerodrome USDC/WETH pool APY"""
        try:
            # Aerodrome's frontend/API provides a public summary
            # We target the primary USDC/WETH pool
            url = "https://api.aerodrome.finance/v1/pools"
            response = requests.get(url, timeout=10)
            pools = response.json().get("data", [])
            
            for pool in pools:
                # Looking for the major USDC pool
                if "USDC" in pool.get("symbol", "") and pool.get("isStable") is False:
                    # Aerodrome lists apr/apy directly in their pool data
                    apy = float(pool.get("apr", 0.0))
                    return round(apy, 2)
            return 0.0
        except Exception as e:
            print(f"Aerodrome Error: {e}")
            return 0.0

    def get_best_yield(self):
        """Compares Aave and Aerodrome specifically"""
        aave_apy = self.get_aave_yield()
        aero_apy = self.get_aerodrome_yield()
        
        if aave_apy >= aero_apy:
            return {"protocol": "Aave V3", "apy": aave_apy}
        else:
            return {"protocol": "Aerodrome", "apy": aero_apy}