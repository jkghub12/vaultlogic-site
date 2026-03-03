import os
import requests
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables (ETH_RPC_URL) from .env file
load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        # 1. Connect to Base Network via RPC
        rpc_url = os.getenv("ETH_RPC_URL")
        if not rpc_url:
            raise ValueError("❌ ETH_RPC_URL not found in .env file")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # 2. Base Network Addresses (Checksummed)
        # Aave V3 Protocol Data Provider on Base
        self.AAVE_PROVIDER_ADDRESS = Web3.to_checksum_address("0x2d8A3C567be027b9C1f3f019623C82806788B77b")
        # Native USDC on Base
        self.USDC_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

    def fetch_aave_rates(self, asset_symbol='USDC'):
        """Direct RPC call to Aave V3 on Base"""
        if not self.w3.is_connected():
            return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}

        # Aave V3 getReserveData ABI
        abi = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'
        
        try:
            contract = self.w3.eth.contract(address=self.AAVE_PROVIDER_ADDRESS, abi=abi)
            data = contract.functions.getReserveData(self.USDC_ADDRESS).call()
            # Index 5 is liquidityRate (Deposit APY) in RAY (10^27)
            apy = (data[5] / 10**27) * 100
            return {"protocol": "Aave", "asset": asset_symbol, "apy": round(apy, 2)}
        except Exception as e:
            print(f"Aave RPC Error: {e}")
            return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}

    def fetch_market_yields(self, asset_symbol='USDC'):
        """Fetches Aerodrome, Uniswap, and Curve yields via DefiLlama API"""
        url = "https://yields.llama.fi/pools"
        results = []
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            data = response.json().get('data', [])
            
            # Target protocols on Base
            targets = {
                'aerodrome': 'Aerodrome', 
                'uniswap-v3': 'Uniswap V3', 
                'curve-dex': 'Curve'
            }
            
            for pool in data:
                if pool.get('chain') == 'Base' and asset_symbol in pool.get('symbol', ''):
                    proj = pool.get('project')
                    if proj in targets:
                        results.append({
                            "protocol": targets[proj],
                            "asset": asset_symbol,
                            "apy": round(float(pool.get('apy', 0.0)), 2)
                        })
            return results
        except Exception as e:
            print(f"Market API Error: {e}")
            return []

    def get_best_yield(self):
        """Compares all sources and prints a leaderboard"""
        aave = self.fetch_aave_rates('USDC')
        market = self.fetch_market_yields('USDC')
        
        all_rates = [aave] + market
        
        # Sort by APY for the leaderboard
        sorted_rates = sorted(all_rates, key=lambda x: x['apy'], reverse=True)
        
        print("\n--- 🏦 VAULTLOGIC YIELD LEADERBOARD ---")
        for r in sorted_rates:
            print(f"{r['protocol']:<12} | {r['asset']}: {r['apy']}%")
        print("---------------------------------------\n")
        
        # Return the winner (highest APY)
        return sorted_rates[0] if sorted_rates else None

if __name__ == "__main__":
    scout = DeFiYieldScout()
    winner = scout.get_best_yield()
    if winner:
        print(f"🏆 WINNER: {winner['protocol']} at {winner['apy']}% APY")