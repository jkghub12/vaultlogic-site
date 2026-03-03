import os
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        rpc_url = os.getenv("ETH_RPC_URL")
        if not rpc_url:
            raise ValueError("❌ ETH_RPC_URL not found in .env file")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # VERIFIED BASE MAINNET ADDRESSES
        # Aave V3 Protocol Data Provider (Base)
        self.AAVE_PROVIDER = Web3.to_checksum_address("0x2d8A3C567be027b9C1f3f019623C82806788B77b")
        # Native USDC (Base)
        self.USDC_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

    def fetch_aave_rates(self):
        """Direct RPC call for Aave V3 on Base"""
        abi = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'
        try:
            contract = self.w3.eth.contract(address=self.AAVE_PROVIDER, abi=abi)
            data = contract.functions.getReserveData(self.USDC_ADDRESS).call()
            # Index 5 is the liquidity rate in RAY
            apy = (data[5] / 10**27) * 100
            return {"protocol": "Aave", "asset": "USDC", "apy": round(apy, 2)}
        except Exception as e:
            print(f"Aave Error: {e}")
            return {"protocol": "Aave", "asset": "USDC", "apy": 0.0}

    def fetch_market_yields(self):
        """Fetches Aerodrome, Uniswap, and Curve via DefiLlama API"""
        url = "https://yields.llama.fi/pools"
        # Mapping API names to display names
        targets = {
            'aerodrome': 'Aerodrome', 
            'uniswap-v3': 'Uniswap V3', 
            'curve-dex': 'Curve'
        }
        
        best_per_protocol = {}
        
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).json()
            for pool in response.get('data', []):
                # We filter for Base chain and pools containing USDC
                if pool.get('chain') == 'Base' and 'USDC' in pool.get('symbol', ''):
                    proj_id = pool.get('project')
                    if proj_id in targets:
                        display_name = targets[proj_id]
                        apy = round(float(pool.get('apy', 0.0)), 2)
                        
                        # Only keep the highest APY pool for each protocol
                        if display_name not in best_per_protocol or apy > best_per_protocol[display_name]['apy']:
                            best_per_protocol[display_name] = {
                                "protocol": display_name,
                                "asset": "USDC",
                                "apy": apy
                            }
            return list(best_per_protocol.values())
        except Exception as e:
            print(f"Market API Error: {e}")
            return []

    def get_best_yield(self):
        """Returns the refined leaderboard (one entry per protocol)"""
        aave = self.fetch_aave_rates()
        market = self.fetch_market_yields()
        
        # Combine and sort
        all_rates = [aave] + market
        sorted_rates = sorted(all_rates, key=lambda x: x['apy'], reverse=True)
        
        # Console logging for deploy logs
        print("\n--- 🏦 VAULTLOGIC CLEAN LEADERBOARD ---")
        for r in sorted_rates:
            print(f"{r['protocol']:<12} | APY: {r['apy']}%")
        print("---------------------------------------\n")
        
        return sorted_rates

if __name__ == "__main__":
    scout = DeFiYieldScout()
    print(scout.get_best_yield())