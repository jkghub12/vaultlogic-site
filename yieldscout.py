import os
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        # Connect to Base Network (Ensure your .env RPC URL is for Base)
        rpc_url = os.getenv("ETH_RPC_URL")
        if not rpc_url:
            raise ValueError("❌ ETH_RPC_URL not found in .env file")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Base Network Addresses
        self.AAVE_PROVIDER = Web3.to_checksum_address("0x2d8A3C567be027b9C1f3f019623C82806788B77b")
        self.USDC_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

    def fetch_aave_rates(self):
        """Direct RPC call for Aave V3 on Base"""
        abi = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'
        try:
            contract = self.w3.eth.contract(address=self.AAVE_PROVIDER, abi=abi)
            data = contract.functions.getReserveData(self.USDC_ADDRESS).call()
            apy = (data[5] / 10**27) * 100 # RAY conversion
            return {"protocol": "Aave", "asset": "USDC", "apy": round(apy, 2)}
        except:
            return {"protocol": "Aave", "asset": "USDC", "apy": 0}

    def fetch_market_rates(self):
        """Fetches Aerodrome, Curve, and Uniswap via DefiLlama"""
        url = "https://yields.llama.fi/pools"
        targets = {'aerodrome': 'Aerodrome', 'uniswap-v3': 'Uniswap V3', 'curve-dex': 'Curve'}
        results = []
        try:
            response = requests.get(url, timeout=10).json()
            for pool in response.get('data', []):
                if pool.get('chain') == 'Base' and 'USDC' in pool.get('symbol'):
                    proj = pool.get('project')
                    if proj in targets:
                        results.append({
                            "protocol": targets[proj],
                            "asset": "USDC",
                            "apy": round(float(pool.get('apy', 0)), 2)
                        })
            return results
        except:
            return []

    def get_best_yield(self):
        """Displays all found rates and identifies the winner"""
        all_rates = [self.fetch_aave_rates()] + self.fetch_market_rates()
        
        # Sort to show highest first
        all_rates = sorted(all_rates, key=lambda x: x['apy'], reverse=True)
        
        print("\n--- 🏦 VAULTLOGIC YIELD LEADERBOARD ---")
        for r in all_rates:
            print(f"{r['protocol']:<12} | {r['apy']}%")
        print("---------------------------------------\n")
        
        return all_rates[0] if all_rates else None

if __name__ == "__main__":
    scout = DeFiYieldScout()
    winner = scout.get_best_yield()
    print(f"🏆 TOP PICK: {winner}")