import os
import requests
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        # 1. Connect to Base Network via RPC
        rpc_url = os.getenv("ETH_RPC_URL")
        if not rpc_url:
            raise ValueError("❌ ETH_RPC_URL not found in .env file")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # 2. BASE NETWORK ADDRESSES
        # Aave V3 Protocol Data Provider (Base)
        self.AAVE_PROVIDER = Web3.to_checksum_address("0x69FA688f1Dc47d4B5d3C2A6708bFCaD38303fAD1")
        # Native USDC (Base)
        self.USDC_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

    def fetch_aave_rates(self):
        """Direct RPC call to Aave V3 on Base"""
        # Aave V3 Data Provider ABI
        abi = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'
        
        try:
            contract = self.w3.eth.contract(address=self.AAVE_PROVIDER, abi=abi)
            data = contract.functions.getReserveData(self.USDC_ADDRESS).call()
            # Index 5 is liquidityRate (Deposit APY) in RAY (10^27)
            apy = (data[5] / 10**27) * 100
            return {"protocol": "Aave", "asset": "USDC", "apy": round(apy, 2)}
        except Exception as e:
            print(f"Aave RPC Error: {e}")
            return {"protocol": "Aave", "asset": "USDC", "apy": 0.0}

    def fetch_market_yields(self):
        """Fetches Aerodrome, Uniswap, and Curve via DefiLlama API"""
        url = "https://yields.llama.fi/pools"
        # We target specific projects on Base
        targets = {'aerodrome': 'Aerodrome', 'uniswap-v3': 'Uniswap V3', 'curve-dex': 'Curve'}
        results = []
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).json()
            for pool in response.get('data', []):
                # Filter for Base network and USDC asset
                if pool.get('chain') == 'Base' and 'USDC' in pool.get('symbol', ''):
                    proj = pool.get('project')
                    if proj in targets:
                        results.append({
                            "protocol": targets[proj],
                            "asset": "USDC",
                            "apy": round(float(pool.get('apy', 0)), 2)
                        })
            return results
        except Exception as e:
            print(f"Market API Error: {e}")
            return []

    def get_best_yield(self):
        """Returns the FULL list to the API so opi.vaultlogic.dev shows everything"""
        aave = self.fetch_aave_rates()
        market = self.fetch_market_yields()
        
        all_rates = [aave] + market
        
        # Sort by APY (Highest first)
        sorted_rates = sorted(all_rates, key=lambda x: x['apy'], reverse=True)
        
        # Logging to console so you can see it in the deploy logs
        print("\n--- 🏦 VAULTLOGIC YIELD LEADERBOARD ---")
        for r in sorted_rates:
            print(f"{r['protocol']:<12} | {r['apy']}%")
        print("---------------------------------------\n")
        
        # We return the WHOLE list so the website can display more than one item
        return sorted_rates

if __name__ == "__main__":
    scout = DeFiYieldScout()
    print(scout.get_best_yield())