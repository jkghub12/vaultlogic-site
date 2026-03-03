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
        
        # Dictionary of protocols and their verified USDC pool addresses on Base
        self.protocols = {
            "Aerodrome": "0xc96033068e4726cd5518b52e37905188f615456c",
            "Uniswap V3": "0x4c36388be6f416a29c8d8eee81c771be330d993c",
            "Curve": "0xf9489679624508e3923d21c295713c72b8f8447d"
        }

    def get_pool_data(self, pool_address):
        """Fetches data for a single pool"""
        url = f"{self.base_url}/networks/{self.network}/pools/{pool_address}"
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract APY and Liquidity
            attr = data.get("data", {}).get("attributes", {})
            apy = float(attr.get("h24_apy", 0.0))
            liquidity = float(attr.get("reserve_in_usd", 0))
            
            return apy, liquidity
        except Exception as e:
            print(f"Error fetching {pool_address}: {e}")
            return 0.0, 0.0

    def get_best_yield(self):
        """Scouts all pools and returns the best one"""
        best_pool = {"protocol": "None", "apy": 0.0}
        
        for name, address in self.protocols.items():
            apy, liquidity = self.get_pool_data(address)
            
            # Logic: Higher APY, and must have at least $10,000 liquidity
            if apy > best_pool["apy"] and liquidity > 10000:
                best_pool = {
                    "protocol": name,
                    "apy": round(apy, 2)
                }
                
        return best_pool