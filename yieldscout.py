import os
import time
import threading
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
DATA_PROVIDER = "0xC4Fcf9893072d61Cc2899C0054877Cb752587981"
USDC_ADDR = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

AAVE_ABI = [{
    "inputs": [{"name": "asset", "type": "address"}],
    "name": "getReserveData",
    "outputs": [
        {"name": "unbacked", "type": "uint256"},
        {"name": "accruedToTreasuryScaled", "type": "uint256"},
        {"name": "totalAToken", "type": "uint256"},
        {"name": "totalStableDebt", "type": "uint256"},
        {"name": "totalVariableDebt", "type": "uint256"},
        {"name": "liquidityRate", "type": "uint256"},
        {"name": "variableBorrowRate", "type": "uint256"},
        {"name": "stableBorrowRate", "type": "uint256"},
        {"name": "averageStableBorrowRate", "type": "uint256"},
        {"name": "liquidityIndex", "type": "uint256"},
        {"name": "variableBorrowIndex", "type": "uint256"},
        {"name": "lastUpdateTimestamp", "type": "uint40"}
    ],
    "stateMutability": "view",
    "type": "function"
}]

def get_aave_yield():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        contract = w3.eth.contract(address=w3.to_checksum_address(DATA_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_ADDR)).call()
        apy = (float(data[5]) / 1e27) * 100
        return round(apy, 2)
    except Exception as e:
        print(f"⚠️ Aave Error: {e}")
        return 4.15

def save_to_db(aave_rate, uni_rate):
    if not DB_URL: return
    conn = None
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=5)
        cur = conn.cursor()
        
        # We now explicitly define the 'timestamp' column as a TIMESTAMP type
        cur.execute("""
            CREATE TABLE IF NOT EXISTS yields (
                id SERIAL PRIMARY KEY,
                aave_rate REAL,
                uniswap_rate REAL,
                timestamp TIMESTAMP
            );
        """)
        
        # Sending datetime.now() ensures Python's time is recorded
        current_time = datetime.now()
        cur.execute(
            "INSERT INTO yields (aave_rate, uniswap_rate, timestamp) VALUES (%s, %s, %s)",
            (float(aave_rate), float(uni_rate), current_time)
        )
        conn.commit()
        cur.close()
        print(f"✅ DB SYNC SUCCESS [{current_time.strftime('%H:%M:%S')}]: {aave_rate}%")
    except Exception as e:
        print(f"❌ DB CONNECTION FAILED: {e}")
    finally:
        if conn: conn.close()

def heartbeat_worker():
    """ This runs in the background to keep the DB fresh! """
    print("💓 VaultLogic Heartbeat Started...")
    while True:
        aave_val = get_aave_yield()
        save_to_db(aave_val, 3.50)
        # Sleep for 5 minutes (300 seconds)
        time.sleep(300)

def start_heartbeat():
    # Start the worker thread so it doesn't block the API
    thread = threading.Thread(target=heartbeat_worker, daemon=True)
    thread.start()

def get_all_yields():
    # This is what the website sees
    aave_val = get_aave_yield()
    return {
        "yields": [
            {"protocol": "Aave V3", "yield": f"{aave_val}%", "asset": "USDC"},
            {"protocol": "Uniswap V3", "yield": "3.50%", "asset": "USDC/ETH"}
        ],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }