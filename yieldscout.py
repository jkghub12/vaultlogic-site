import os
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables (ETH_RPC_URL) from .env file
load_dotenv()

class DeFiYieldScout:
    def __init__(self):
        # Connect to Ethereum Mainnet using your Alchemy URL
        rpc_url = os.getenv("ETH_RPC_URL")
        if not rpc_url:
            raise ValueError("❌ ETH_RPC_URL not found in .env file")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.protocols = ['aave', 'curve', 'uniswap']

    def fetch_aave_rates(self, asset_symbol='USDC'):
        """Fetches REAL APY from Aave V3 Protocol Data Provider"""
        
        # 1. Correct Mainnet Aave Protocol Data Provider Address (Verified)
        AAVE_PROVIDER_ADDRESS = Web3.to_checksum_address("0x497a1994c46d4f6C864904A9f1fac6328Cb7C8a6")
        
        # 2. Verify deployment
        if not self.w3.is_connected():
            print("❌ Not connected to Ethereum node")
            return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}

        try:
            code = self.w3.eth.get_code(AAVE_PROVIDER_ADDRESS)
            if code == b'' or code == b'x00':
                print(f"❌ No contract code found at {AAVE_PROVIDER_ADDRESS}")
                return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}
            else:
                print(f"✅ Contract code found at {AAVE_PROVIDER_ADDRESS}")
        except Exception as e:
            print(f"Error checking contract: {e}")
            return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}

        # 3. Correct ABI for ProtocolDataProviderV3 (Missing quotes fixed here)
        abi = '''[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'''
        
        contract = self.w3.eth.contract(address=AAVE_PROVIDER_ADDRESS, abi=abi)
        
        # Asset addresses (Ethereum Mainnet)
        assets = {
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F'
        }
        asset_address = assets.get(asset_symbol)
        
        if not asset_address:
            print(f"Asset {asset_symbol} not supported.")
            return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}

        # 4. The actual call with the 'from' parameter
        print(f"Fetching REAL Aave rates for {asset_symbol}...")
        try:
            # The 'from' address is needed for some call simulations
            reserve_data = contract.functions.getReserveData(asset_address).call(
                {'from': '0x0000000000000000000000000000000000000000'}
            )
            liquidity_rate = reserve_data[5] # Index 5 is liquidityRate (deposit rate)
            
            # Aave rates are in RAY (10^27)
            apy = (liquidity_rate / 10**27) * 100 
            return {"protocol": "Aave", "asset": asset_symbol, "apy": round(apy, 2)}
        except Exception as e:
            print(f"Error fetching Aave rates: {e}")
            return {"protocol": "Aave", "asset": asset_symbol, "apy": 0}

    def get_best_yield(self):
        # Logic to compare rates and pick the winner
        aave = self.fetch_aave_rates()
        # For now, just compare Aave against placeholders
        rates = [aave] # Adding other protocols later
        best = max(rates, key=lambda x: x['apy'])
        return best

# --- Main Execution ---
if __name__ == "__main__":
    try:
        scout = DeFiYieldScout()
        best_option = scout.get_best_yield()
        print(f"Best Yield Option: {best_option}")
    except Exception as e:
        print(f"Application error: {e}")