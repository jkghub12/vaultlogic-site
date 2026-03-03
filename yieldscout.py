# yieldscout.py
import requests

class DeFiYieldScout:
    def __init__(self):
        self.aero_api = "https://api.aerodrome.finance/v1/pools"
        self.aave_api = "https://api.aavescan.com/v2/latest?market=aave-v3-base"

    def get_aave_yield(self):
        """Fetches Aave V3 Supply APY for USDC"""
        try:
            response = requests.get(self.aave_api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Aavescan returns a list of assets
                for asset in data:
                    if asset.get("symbol") == "USDC":
                        # Liquidity Rate is often in Ray units (10^27)
                        # To get percentage: (Rate / 10^27) * 100
                        raw_rate = float(asset.get("currentLiquidityRate", 0))
                        apy = round((raw_rate / 10**25), 2)
                        print(f"DEBUG: Aave USDC APY: {apy}%")
                        return apy
            return 0.0
        except Exception as e:
            print(f"DEBUG: Aave Error: {e}")
            return 0.0

    def get_aerodrome_yield(self):
        """Fetches Aerodrome USDC pool APR/APY"""
        try:
            response = requests.get(self.aero_api, timeout=10)
            if response.status_code == 200:
                pools = response.json().get("data", [])
                best_aero_apy = 0.0
                for pool in pools:
                    symbol = pool.get("symbol", "")
                    # Check both directions for the pair
                    if "USDC" in symbol and ("WETH" in symbol or "AERO" in symbol):
                        # API may use 'apr' or 'pool_apr'
                        apy = float(pool.get("apr") or pool.get("pool_apr") or 0.0)
                        if apy > best_aero_apy:
                            best_aero_apy = apy
                            print(f"DEBUG: Found Aero Pool {symbol}: {apy}%")
                return round(best_aero_apy, 2)
            return 0.0
        except Exception as e:
            print(f"DEBUG: Aerodrome Error: {e}")
            return 0.0

    def get_best_yield(self):
        """Compares Aave and Aerodrome and returns the highest"""
        aave_apy = self.get_aave_yield()
        aero_apy = self.get_aerodrome_yield()
        
        if aero_apy >= aave_apy and aero_apy > 0:
            return {"protocol": "Aerodrome", "apy": aero_apy}
        elif aave_apy > 0:
            return {"protocol": "Aave V3", "apy": aave_apy}
        else:
            # If both are 0, we need to check if the APIs are even responding
            return {"protocol": "Check Railway Logs", "apy": 0.0}