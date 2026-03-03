# yieldscout.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.network = "base"
        
        # New verified USDC-related Pool Addresses on Base
        # These are common pools, but they do change!
        self.pool_addresses = [
            "0xc96033068e4726cd5518b52e37905188f615456c", # Aerodrome USDC/WETH
            "0x4c36388be6f416a29c8d8eee81c771be330d993c", # Uniswap V3 USDC/WETH
            "0x8e83344697f26284f180738a53e36e1c940b5435"  # Curve USDC/DAI
        ]

    def get_best_yield(self):
        """Fetches real-time data from GeckoTerminal v2 API"""
        
        if not self.api_key:
            return {"protocol": "Error", "apy": 0.0, "message": "Missing API Key"}

        addresses_str = ",".join(self.pool_addresses)
        # Using the base API endpoint as recommended by docs
        url = f"https://api.geckoterminal.com/api/v2/networks/{self.network}/pools/multi/{addresses_str}"
        
        headers = {
            "Accept": "application/json",
            "x-cg-demo-api-key": self.api_key # Pass key here
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            # Log the raw response for debugging if it fails
            if response.status_code != 200:
                print(f"API Error: {response.status_code} - {response.text}")
                return {"protocol": "Error", "apy": 0.0}

            json_data = response.json()
            pools = json_data.get("data", [])
            
            if not pools:
                return {"protocol": "No Pools Found", "apy": 0.0}

            best_pool = {"protocol": "None", "apy": 0.0}

            for pool in pools:
                attr = pool.get("attributes", {})
                name = attr.get("name", "Unknown")
                
                # Fetching APY from the specific 'h24_apy' field if available
                # Fallback to a default small value if not provided
                apy = float(attr.get("h24_apy", 0.0))
                liquidity = float(attr.get("reserve_in_usd", 0))
                
                # Only consider pools with decent liquidity
                if apy > best_pool["apy"] and liquidity > 5000:
                    best_pool = {
                        "protocol": name.split("/")[0].strip(), # e.g. "Uniswap"
                        "apy": round(apy, 2)
                    }
            
            return best_pool

        except Exception as e:
            print(f"Scout Error: {e}")
            return {"protocol": "Error", "apy": 0.0}