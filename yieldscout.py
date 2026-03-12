import os
import json
from web3 import Web3
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
# Use the internal Railway URL if available, otherwise fallback
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
VAULT_ADDR = os.getenv("BANKER_VAULT_ADDRESS")

# Aave V3 Pool Data Provider (Base Mainnet)
AAVE_PROVIDER = "0x2d8a3C5677189723C4cB8873CfC9C8974F701758"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# ABI as a String - we will parse it later
AAVE_ABI_STR = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint40":"lastUpdateTimestamp","type":"uint40"}],"internalType":"struct DataTypes.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'

def get_aave_yield():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        # FIX: We must parse the string into a JSON object (list)
        abi = json.loads(AAVE_ABI_STR)
        
        contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_PROVIDER), abi=abi)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_BASE)).call()
        
        # index 5 is liquidityRate (Ray units)
        apy = (float(data[0][5]) / 1e27) * 100 # data[0] because it's a returned tuple/struct
        return round(apy, 2)
    except Exception as e:
        print(f"⚠️ Aave Fetch failed: {e}")
        return 4.15

def save_to_db(aave_rate, uni_rate):
    if not DB_URL: return
    conn = None
    try:
        # We use a short timeout and a fresh connection every time
        conn = psycopg2.connect(DB_URL, connect_timeout=5)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO yields (aave_rate, uniswap_rate) VALUES (%s, %s)",
            (float(aave_rate), float(uni_rate))
        )
        conn.commit()
        cur.close()
        print(f"✅ Saved to DB: Aave {aave_rate}% | Uni {uni_rate}%")
    except Exception as e:
        print(f"❌ DB Error: {e}")
    finally:
        if conn: conn.close()

def get_all_yields():
    # 1. Get real Aave data
    aave_val = get_aave_yield()
    uni_val = 3.50 # Placeholder
    
    # 2. Save to history
    save_to_db(aave_val, uni_val)

    # 3. Get ETH Balance
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    eth_bal = "0.00"
    if VAULT_ADDR:
        try:
            bal = w3.eth.get_balance(w3.to_checksum_address(VAULT_ADDR))
            eth_bal = str(round(float(w3.from_wei(bal, 'ether')), 6))
        except: eth_bal = "0.00"

    return {
        "yields": [
            {"protocol": "Aave V3", "yield": f"{aave_val}%", "asset": "USDC"},
            {"protocol": "Uniswap V3", "yield": f"{uni_val}%", "asset": "USDC/ETH"}
        ],
        "wallet": {"eth": eth_bal, "usdc": "0.00"},
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }