import os
from web3 import Web3
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Aave V3 Base
AAVE_PROVIDER = "0x2d8a3C5677189723C4cB8873CfC9C8974F701758"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
AAVE_ABI = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint128","name":"liquidityRate","type":"uint128"}],"internalType":"struct IProtocolDataProvider.TokenData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'

def save_to_db(platform, yield_val):
    if not DB_URL:
        print("❌ DATABASE_URL missing")
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS yields (id SERIAL PRIMARY KEY, platform TEXT, yield_rate NUMERIC, timestamp TIMESTAMP)")
        cur.execute("INSERT INTO yields (platform, yield_rate, timestamp) VALUES (%s, %s, %s)", (platform, yield_val, datetime.utcnow()))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ DB Saved: {platform}")
    except Exception as e:
        print(f"❌ DB Error: {e}")

def get_aave_yield():
    try:
        if not w3.is_connected(): return 4.15
        contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_BASE)).call()
        apy = (float(data[5]) / 1e27) * 100
        return round(apy, 2) if apy > 0 else 4.15
    except:
        return 4.15 # Hard fallback if anything fails

def get_all_yields():
    # 1. Get Values
    aave_val = get_aave_yield()
    uni_val = 3.50
    
    # 2. Save to DB
    save_to_db("Aave", aave_val)
    save_to_db("Uniswap", uni_val)
    
    # 3. Return for API
    return [
        {"platform": "Aave", "yield": f"{aave_val}%"},
        {"platform": "Uniswap", "yield": f"{uni_val}%"}
    ]