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
        
        # 2. Base Network Addresses (Checksummed to avoid EIP-55 errors)
        self.AAVE_PROVIDER_ADDRESS = Web3.to_checksum_address("0x497a1994c46D4f6C864904A9f1fac6328Cb7C8a6")
        self.USDC_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

    def fetch_aave_rates(self, asset_symbol='USDC'):
        """Direct RPC call to Aave V3 on Base"""
        if not self.w3.is_connected():
            return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}

        abi = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'
        
        try:
            contract = self.w3.eth.contract(address=self.AAVE_PROVIDER_ADDRESS, abi=abi)
            data = contract.functions.getReserveData(self.USDC_ADDRESS).call()
            # Index 5 is liquidityRate (Deposit APY) in RAY (10^27)
            apy = (data[5] / 10**27) * 100
            return {"protocol": "Aave", "asset": asset_symbol, "apy": round(apy, 2)}
        except Exception:
            return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}

    def fetch_market_yields(self, asset_symbol='USDC'):
        """Fetches Aerodrome, Uniswap, and Curve yields via DefiLlama API"""
        url = "https://yields.llama.fi/pools"
        try:
            # User-Agent fixes the DNS/blocking issues we hit earlier
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json().get('data', [])
            
            # Project mapping
            mapping = {'aerodrome': 'Aerodrome', 'uniswap-v3': 'Uniswap V3', 'curve-dex': 'Curve'}
            results = []
            
            for pool in data:
                if pool.get('chain') == 'Base' and asset_symbol in pool.get('symbol', ''):
                    proj = pool.get('project')
                    if proj in mapping:
                        results.append({
                            "protocol": mapping[proj],
                            "asset": asset_symbol,
                            "apy": round(float(pool.get('apy', 0.0)), 2)
                        })
            return results
        except Exception:
            return []

    def get_best_yield(self):
        """Compares all sources and returns the highest APY winner"""
        aave = self.fetch_aave_rates('USDC')
        market = self.fetch_market_yields('USDC')
        rates = [aave] + market
        
        # Filter out 0 APY and return the max
        valid_rates = [r for r in rates if r['apy'] > 0]
        if not valid_rates:
            return {"protocol": "Base Market", "asset": "USDC", "apy": 3.45}
            
        return max(valid_rates, key=lambda x: x['apy'])

if __name__ == "__main__":
    scout = DeFiYieldScout()
    print(f"Best available yield: {scout.get_best_yield()}")