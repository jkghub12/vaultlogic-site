# yieldscout.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.network = "base"
        self.base_url = "https://api.geckoterminal.com/api/v2"
        
        # We will search for pools containing these tokens
        self.usdc_address = "0x833589fcd6edb6e08f4c7c32e4f51b640003058f" # USDC on Base

    def get_best_yield(self):
        """Searches for the best pool for USDC on Base"""
        
        if not self.api_key:
            return {"protocol": "Error", "apy": 0.0, "message": "Missing API Key"}

        # Search for pools on Base that contain USDC
        url = f"{self.base_url}/networks/{self.network}/tokens/{self.usdc_address}/pools"
        
        headers = {
            "Accept": "application/json",
            "x-cg-demo-api-key": self.api_key
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            json_data = response.json()
            
            pools = json_data.get("data", [])
            
            if not pools:
                return {"protocol": "No Pools Found", "apy": 0.0}

            best_pool = {"protocol": "None", "apy": 0.0}

            for pool in pools:
                attr = pool.get("attributes", {})
                
                # Check protocol name (DEX)
                name = attr.get("name", "Unknown")
                
                # APY is often called 'h24_apy' or derived from volume/liquidity
                apy = float(attr.get("h24_apy", 0.0))
                
                # Liquidity check (must be at least $50,000 for safety)
                liquidity = float(attr.get("reserve_in_usd", 0))                
                
                # Logic: Is this pool the best?
                if apy > best_pool["apy"] and liquidity > 50000:
                    best_pool = {
                        "protocol": name.split("/")[0].strip(), # e.g. "Aerodrome"
                        "apy": round(apy, 2)
                    }
            
            return best_pool

        except Exception as e:
            print(f"Scout Error: {e}")
            return {"protocol": "Error", "apy": 0.0}