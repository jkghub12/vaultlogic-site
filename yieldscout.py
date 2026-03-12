import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
VAULT_ADDR = os.getenv("BANKER_VAULT_ADDRESS")

# AAVE V3 PROTOCOL DATA PROVIDER (BASE MAINNET)
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
        
        if not w3.is_connected():
            return 4.15
            
        contract = w3.eth.contract(address=w3.to_checksum_address(DATA_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_ADDR)).call()
        
        # RAY conversion
        apy = (float(data[5]) / 1e27) * 100
        print(f"📡 Aave Data Fetched: {round(apy, 2)}%")
        return round(apy, 2)
    except Exception as e:
        print(f"⚠️ Aave Error: {e}")
        return 4.15

def save_to_db(aave_rate, uni_rate):
    if not DB_URL:
        print("❌ DB Error: DATABASE_URL variable is empty!")
        return
    
    # Debugging: Show where we are trying to connect
    db_info = DB_URL.split('@')[-1] if '@' in DB_URL else "Internal Address"
    print(f"🔄 Attempting DB sync to: {db_info}")
    
    conn = None
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=5)
        cur = conn.cursor()
        
        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS yields (
                id SERIAL PRIMARY KEY,
                aave_rate REAL,
                uniswap_rate REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cur.execute(
            "INSERT INTO yields (aave_rate, uniswap_rate) VALUES (%s, %s)",
            (float(aave_rate), float(uni_rate))
        )
        conn.commit()
        cur.close()
        print(f"✅ DATABASE SYNC SUCCESS: Aave {aave_rate}%")
    except Exception as e:
        print(f"❌ DATABASE CONNECTION FAILED: {e}")
    finally:
        if conn:
            conn.close()

def get_all_yields():
    aave_val = get_aave_yield()
    uni_val = 3.50 
    
    save_to_db(aave_val, uni_val)

    # Balance check
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    eth_bal = "0.00"
    if VAULT_ADDR:
        try:
            bal = w3.eth.get_balance(w3.to_checksum_address(VAULT_ADDR))
            eth_bal = str(round(float(w3.from_wei(bal, 'ether')), 6))
        except:
            pass

    return {
        "yields": [
            {"protocol": "Aave V3", "yield": f"{aave_val}%", "asset": "USDC"},
            {"protocol": "Uniswap V3", "yield": f"{uni_val}%", "asset": "USDC/ETH"}
        ],
        "wallet": {"eth": eth_bal, "usdc": "0.00"},
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }