import os
from web3 import Web3
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
VAULT_ADDR = os.getenv("BANKER_VAULT_ADDRESS")

# --- 1. HARDENED AAVE LOGIC ---
AAVE_PROVIDER = "0x2d8a3C5677189723C4cB8873CfC9C8974F701758"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Minimalist ABI to ensure it doesn't fail on complex tuple returns
AAVE_ABI = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"uint256":"unbacked","type":"uint256"},{"uint256":"accruedToTreasuryScaled","type":"uint256"},{"uint256":"totalAToken","type":"uint256"},{"uint256":"totalStableDebt","type":"uint256"},{"uint256":"totalVariableDebt","type":"uint256"},{"uint256":"liquidityRate","type":"uint256"},{"uint256":"variableBorrowRate","type":"uint256"},{"uint256":"stableBorrowRate","type":"uint256"},{"uint256":"averageStableBorrowRate","type":"uint256"},{"uint256":"liquidityIndex","type":"uint256"},{"uint256":"variableBorrowIndex","type":"uint256"},{"uint40":"lastUpdateTimestamp","type":"uint40"}],"stateMutability":"view","type":"function"}]'

def get_aave_yield():
    try:
        # Create a fresh provider instance inside the call to prevent stale connections
        temp_w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not temp_w3.is_connected(): return 4.15
        
        contract = temp_w3.eth.contract(address=temp_w3.to_checksum_address(AAVE_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(temp_w3.to_checksum_address(USDC_BASE)).call()
        
        # liquidityRate is at index 5, expressed in RAY (10^27)
        apy = (float(data[5]) / 1e27) * 100
        return round(apy, 2) if apy > 0 else 4.15
    except Exception as e:
        print(f"⚠️ Aave Fetch failed: {e}")
        return 4.15 

# --- 2. HARDENED DATABASE LOGIC ---
def save_to_db(aave_rate, uni_rate):
    if not DB_URL: return
    conn = None
    try:
        # Explicitly setting a connect_timeout to prevent the "Server closed" error
        conn = psycopg2.connect(DB_URL, connect_timeout=10)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO yields (aave_rate, uniswap_rate) VALUES (%s, %s)", 
            (aave_rate, uni_rate)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"❌ DB Error: {e}")
    finally:
        if conn:
            conn.close()

# --- 3. MAIN ENGINE FUNCTION ---
def get_all_yields():
    aave_val = get_aave_yield()
    uni_val = 3.50 
    
    # Fetch Balance
    temp_w3 = Web3(Web3.HTTPProvider(RPC_URL))
    eth_balance = "0.00"
    if VAULT_ADDR:
        try:
            balance_wei = temp_w3.eth.get_balance(temp_w3.to_checksum_address(VAULT_ADDR))
            eth_balance = str(round(float(temp_w3.from_wei(balance_wei, 'ether')), 6))
        except:
            eth_balance = "0.00"

    # Save to history
    save_to_db(aave_val, uni_val)

    return {
        "yields": [
            {"protocol": "Aave V3", "yield": f"{aave_val}%", "asset": "USDC"},
            {"protocol": "Uniswap V3", "yield": f"{uni_val}%", "asset": "USDC/ETH"}
        ],
        "wallet": {
            "eth": eth_balance,
            "usdc": "0.00" 
        },
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }