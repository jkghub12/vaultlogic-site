import os
import requests
import psycopg2
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        rpc_url = os.getenv("ETH_RPC_URL")
        if not rpc_url:
            raise ValueError("❌ ETH_RPC_URL not found")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # VERIFIED BASE MAINNET DATA PROVIDER (Aave V3)
        self.AAVE_PROVIDER = Web3.to_checksum_address("0x2d8A3C567be027b9C1f3f019623C82806788B77b")
        self.USDC_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

    def fetch_aave_rates(self):
        abi = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'
        try:
            contract = self.w3.eth.contract(address=self.AAVE_PROVIDER, abi=abi)
            data = contract.functions.getReserveData(self.USDC_ADDRESS).call()
            # Index 5: liquidityRate (in RAY)
            apy = (data[5] / 10**27) * 100
            return {"protocol": "Aave", "asset": "USDC", "apy": round(apy, 2)}
        except Exception:
            return {"protocol": "Aave", "asset": "USDC", "apy": 0.0}

    def fetch_market_yields(self):
        url = "https://yields.llama.fi/pools"
        targets = {'aerodrome': 'Aerodrome', 'uniswap-v3': 'Uniswap V3', 'curve-dex': 'Curve'}
        best_per_protocol = {}
        try:
            res = requests.get(url, timeout=10).json()
            for pool in res.get('data', []):
                # FILTER: Base Network + USDC + Blue Chip pairs (ETH/WETH) only
                is_base = pool.get('chain') == 'Base'
                symbol = pool.get('symbol', '').upper()
                is_stable_or_bluechip = 'USDC' in symbol and ('ETH' in symbol or 'WETH' in symbol or 'USD' in symbol)
                
                if is_base and is_stable_or_bluechip:
                    proj = pool.get('project')
                    if proj in targets:
                        name = targets[proj]
                        apy = round(float(pool.get('apy', 0.0)), 2)
                        if name not in best_per_protocol or apy > best_per_protocol[name]['apy']:
                            best_per_protocol[name] = {"protocol": name, "asset": symbol, "apy": apy}
            return list(best_per_protocol.values())
        except:
            return []

    def get_best_yield(self):
        all_data = [self.fetch_aave_rates()] + self.fetch_market_yields()
        return sorted(all_data, key=lambda x: x['apy'], reverse=True)

# ... save_to_railway function remains the same ...