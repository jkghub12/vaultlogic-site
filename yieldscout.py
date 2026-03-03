# yieldscout.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        # Base network ID for GeckoTerminal
        self.network = "base"
        
        # Specific Pool IDs for major USDC pools on Base
        # You can find these IDs on GeckoTerminal.com
        self.pool_addresses = [
            "0x6854580b06716d1f99c0d48e8e7a68e0d9b4b0e8", # Aerodrome USDC/ETH
            "0x8e83344697f26284f180738a53e36e1c940b5435", # Uniswap V3 USDC/ETH
            "0x6854580b06716d1f99c0d48e8e7a68e0d9b4b0e8"  # Curve USDC/USDT
        ]

    def get_best_yield(self):
        """Fetches aggregated data from multiple pools and returns the best"""
        
        if not self.api_key:
            return {"protocol": "Error", "apy": 0.0, "message": "Missing API Key"}

        # Format addresses for the multi-pool endpoint
        addresses_str = ",".join(self.pool_addresses)
        url = f"https://api.coingecko.com/api/v3/onchain/networks/{self.network}/pools/multi/{addresses_str}"
        
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": self.api_key
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            pools = data.get("data", [])
            best_pool = {"protocol": "None", "apy": 0.0}

            for pool in pools:
                attributes = pool.get("attributes", {})
                
                # Get the APY (GeckoTerminal calls it h24_apy or similar)
                apy = float(attributes.get("h24_apy", 0.0))
                
                # Get Protocol Name
                protocol = attributes.get("dex", {}).get("name", "Unknown")

                if apy > best_pool["apy"]:
                    best_pool = {
                        "protocol": protocol,
                        "apy": apy
                    }
            
            return best_pool

        except Exception as e:
            return {"protocol": "Error", "apy": 0.0, "message": str(e)}