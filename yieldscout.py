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
        
        # VERIFIED BASE MAINNET DATA PROVIDER
        self.AAVE_PROVIDER = Web3.to_checksum_address("0xC4Fcf9893072d61Cc2899C0054877Cb752587981")
        self.USDC_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

    def fetch_aave_rates(self):
        abi = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'
        try:
            contract = self.w3.eth.contract(address=self.AAVE_PROVIDER, abi=abi)
            data = contract.functions.getReserveData(self.USDC_ADDRESS).call()
            # Index 5: liquidityRate (in RAY)
            apy = (data[5] / 10**27) * 100
            return {"protocol": "Aave", "asset": "USDC", "apy": round(apy, 2)}
        except Exception as e:
            return {"protocol": "Aave", "asset": "USDC", "apy": 0.0}

    def fetch_market_yields(self):
        url = "https://yields.llama.fi/pools"
        targets = {'aerodrome': 'Aerodrome', 'uniswap-v3': 'Uniswap V3', 'curve-dex': 'Curve'}
        best_per_protocol = {}
        
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).json()
            for pool in response.get('data', []):
                # FILTER: Base Network + USDC + Stable Pairs only (WETH/ETH)
                is_base = pool.get('chain') == 'Base'
                symbol = pool.get('symbol', '').upper()
                is_stable_pair = 'USDC' in symbol and ('ETH' in symbol or 'WETH' in symbol)
                
                if is_base and is_stable_pair:
                    proj_id = pool.get('project')
                    if proj_id in targets:
                        name = targets[proj_id]
                        apy = round(float(pool.get('apy', 0.0)), 2)
                        
                        if name not in best_per_protocol or apy > best_per_protocol[name]['apy']:
                            best_per_protocol[name] = {"protocol": name, "asset": symbol, "apy": apy}
            
            return list(best_per_protocol.values())
        except:
            return []

    def get_best_yield(self):
        aave = self.fetch_aave_rates()
        market = self.fetch_market_yields()
        return sorted([aave] + market, key=lambda x: x['apy'], reverse=True)

if __name__ == "__main__":
    print(DeFiYieldScout().get_best_yield())