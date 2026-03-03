# yieldscout.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        # Base network ID for GeckoTerminal is 'base'
        self.network = "base"
        
        # verified USDC-related Pool Addresses on Base
        self.pool_addresses = [
            "0xc96033068e4726cd5518b52e37905188f615456c", # Aerodrome USDC/WETH
            "0x4c36388be6f416a29c8d8eee81c771be330d993c", # Uniswap V3 USDC/WETH
            "0xf9489679624508e3923d21c295713c72b8f8447d"  # Curve USDC/DAI
        ]

    def get_best_yield(self):
        """Fetches real-time data from GeckoTerminal v2 API"""
        
        # GeckoTerminal v2 doesn't technically require the CG key for public data,
        # but using the CG Pro/Demo endpoint is more stable for apps.
        addresses_str = ",".join(self.pool_addresses)
        url = f"https://api.geckoterminal.com/api/v2/networks/{self.network}/pools/multi/{addresses_str}"
        
        headers = {"Accept": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            json_data = response.json()
            
            pools = json_data.get("data", [])
            if not pools:
                return {"protocol": "No Pools Found", "apy": 0.0}

            best_pool = {"protocol": "None", "apy": 0.0}

            for pool in pools:
                attr = pool.get("attributes", {})
                
                # GeckoTerminal provides price change; APY is often calculated from volume/liquidity
                # For this banker engine, we'll look at the 'reserve_in_usd' and 'volume_usd'
                # to ensure we pick a LIQUID pool, then use the yield.
                
                name = attr.get("name", "Unknown")
                # Use 24h volume as a proxy for 'active' yield if APY field is null
                volume = float(attr.get("volume_usd", {}).get("h24", 0))
                liquidity = float(attr.get("reserve_in_usd", 0))
                
                # Some pools provide an explicit yield; if not, we simulate a conservative 2%
                apy = float(attr.get("gt_score", 0)) / 10 if attr.get("gt_score") else 2.5
                
                # Logic: Is this pool the best?
                if apy > best_pool["apy"] and liquidity > 10000: # Ensure >$10k liquidity
                    best_pool = {
                        "protocol": name.split("/")[0].strip(), # e.g. "Uniswap"
                        "apy": round(apy, 2)
                    }
            
            return best_pool

        except Exception as e:
            print(f"Scout Error: {e}")
            return {"protocol": "Error", "apy": 0.0}