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
            raise ValueError("❌ ETH_RPC_URL not found in .env file")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # BASE MAINNET ADDRESSES
        self.AAVE_PROVIDER = Web3.to_checksum_address("0xC4Fcf9893072d61Cc2899C0054877Cb752587981")
        self.USDC_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

    def fetch_aave_rates(self):
        abi = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct IPoolDataProvider.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'
        try:
            contract = self.w3.eth.contract(address=self.AAVE_PROVIDER, abi=abi)
            data = contract.functions.getReserveData(self.USDC_ADDRESS).call()
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
                if pool.get('chain') == 'Base' and 'USDC' in pool.get('symbol'):
                    proj = pool.get('project')
                    if proj in targets:
                        name = targets[proj]
                        apy = round(float(pool.get('apy', 0.0)), 2)
                        if name not in best_per_protocol or apy > best_per_protocol[name]['apy']:
                            best_per_protocol[name] = {"protocol": name, "asset": pool.get('symbol'), "apy": apy}
            return list(best_per_protocol.values())
        except:
            return []

    def get_best_yield(self):
        all_data = [self.fetch_aave_rates()] + self.fetch_market_yields()
        return sorted(all_data, key=lambda x: x['apy'], reverse=True)

def save_to_railway(data):
    """Saves the scouted data into Railway Postgres"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️ DATABASE_URL not found. Skipping save.")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        now = datetime.now()
        
        for entry in data:
            # Update Current Snapshot
            cur.execute("""
                INSERT INTO current_yields (protocol, asset, apy, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (protocol, asset) 
                DO UPDATE SET apy = EXCLUDED.apy, updated_at = EXCLUDED.updated_at;
            """, (entry['protocol'], entry['asset'], entry['apy'], now))

            # Record in History
            cur.execute("""
                INSERT INTO yield_history (protocol, asset, apy, captured_at)
                VALUES (%s, %s, %s, %s);
            """, (entry['protocol'], entry['asset'], entry['apy'], now))

        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Database updated at {now}")
    except Exception as e:
        print(f"❌ DB Error: {e}")

if __name__ == "__main__":
    scout = DeFiYieldScout()
    yields = scout.get_best_yield()
    print(yields)
    # save_to_railway(yields) # Uncomment to test locally if you have DB_URL