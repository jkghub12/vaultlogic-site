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
AAVE_DATA_PROVIDER = "0x0a1677c790757d906141a0172e817a020188bECD"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Simplified ABI focused only on the Yield data
AAVE_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {"internalType": "uint256", "name": "unbacked", "type": "uint256"},
            {"internalType": "uint256", "name": "accruedToTreasuryScaled", "type": "uint256"},
            {"internalType": "uint256", "name": "totalAToken", "type": "uint256"},
            {"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"},
            {"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidityRate", "type": "uint256"},
            {"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "averageStableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidityIndex", "type": "uint256"},
            {"internalType": "uint256", "name": "variableBorrowIndex", "type": "uint256"},
            {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_aave_yield():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_DATA_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_BASE)).call()
        
        # The liquidityRate is index 5 in this tuple.
        # It is expressed in RAY (10^27).
        apy = (float(data[5]) / 1e27) * 100
        print(f"📡 LIVE AAVE FETCH: {round(apy, 2)}%")
        return round(apy, 2)
    except Exception as e:
        print(f"⚠️ Aave Data Extraction Error: {e}")
        return 4.15

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
        print(f"✅ DB UPDATE SUCCESS: Aave {aave_rate}%")
    except Exception as e:
        print(f"❌ DB Write Error: {e}")

def get_all_yields():
    aave_val = get_aave_yield()
    uni_val = 3.50 # Real Uniswap coming in the next session!
    
    save_to_db(aave_val, uni_val)

    return {
        "yields": [
            {"protocol": "Aave V3", "yield": f"{aave_val}%", "asset": "USDC"},
            {"protocol": "Uniswap V3", "yield": f"{uni_val}%", "asset": "USDC/ETH"}
        ],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }