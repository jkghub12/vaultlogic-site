import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- 2026 VERIFIED BASE ADDRESSES ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
# Official Aave V3 Protocol Data Provider (Base)
DATA_PROVIDER = "0xC4Fcf9893072d61Cc2899C0054877Cb752587981"
USDC_ADDR = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Full 12-item tuple for getReserveData
ABI = [{
    "inputs": [{"name": "asset", "type": "address"}],
    "name": "getReserveData",
    "outputs": [
        {"name": "unbacked", "type": "uint256"},
        {"name": "accruedToTreasuryScaled", "type": "uint256"},
        {"name": "totalAToken", "type": "uint256"},
        {"name": "totalStableDebt", "type": "uint256"},
        {"name": "totalVariableDebt", "type": "uint256"},
        {"name": "liquidityRate", "type": "uint256"}, # THIS IS INDEX 5
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
        # Injecting at layer 0 is critical for Base/L2s in Web3.py v7
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        contract = w3.eth.contract(address=w3.to_checksum_address(DATA_PROVIDER), abi=ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_ADDR)).call()
        
        # liquidityRate (index 5) is in RAY (10^27)
        apy = (float(data[5]) / 1e27) * 100
        print(f"📡 Aave Data Fetched: {round(apy, 2)}%")
        return round(apy, 2)
    except Exception as e:
        print(f"⚠️ Aave Error: {e}")
        return 4.15 # Fallback

def save_to_db(aave_rate, uni_rate):
    if not DB_URL: return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO yields (aave_rate, uniswap_rate) VALUES (%s, %s)",
            (float(aave_rate), float(uni_rate))
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Database Sync: Aave {aave_rate}% | Uni {uni_rate}%")
    except Exception as e:
        print(f"❌ DB Error: {e}")

def get_all_yields():
    aave_val = get_aave_yield()
    uni_val = 3.50 # Placeholder until we wire up Uni V3
    save_to_db(aave_val, uni_val)
    
    return {
        "yields": [
            {"protocol": "Aave V3", "yield": f"{aave_val}%", "asset": "USDC"},
            {"protocol": "Uniswap V3", "yield": f"{uni_val}%", "asset": "USDC/ETH"}
        ],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }