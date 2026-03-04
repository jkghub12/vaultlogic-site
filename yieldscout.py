import os
from web3 import Web3
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
# The address of your vault/wallet
VAULT_ADDR = os.getenv("BANKER_VAULT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Aave V3 Base Data Provider & USDC Asset
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
        # Ensure table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS yields (
                id SERIAL PRIMARY KEY, 
                platform TEXT, 
                yield_rate NUMERIC, 
                timestamp TIMESTAMP
            )
        """)
        # Insert data
        cur.execute(
            "INSERT INTO yields (platform, yield_rate, timestamp) VALUES (%s, %s, %s)", 
            (platform, yield_val, datetime.utcnow())
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ DB Saved: {platform} ({yield_val}%)")
    except Exception as e:
        print(f"❌ DB Error: {e}")

def get_aave_yield():
    try:
        if not w3.is_connected(): return 4.15
        contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_BASE)).call()
        # Convert RAY to Percentage
        apy = (float(data[5]) / 1e27) * 100
        return round(apy, 2) if apy > 0 else 4.15
    except Exception as e:
        print(f"⚠️ Aave Fetch failed, using fallback: {e}")
        return 4.15 

def get_all_yields():
    # 1. Fetch Yields
    aave_val = get_aave_yield()
    uni_val = 3.50 # Placeholder for Uniswap
    
    # 2. Fetch Wallet Balance (The .0005 ETH update)
    eth_balance = "0.00"
    if VAULT_ADDR:
        try:
            balance_wei = w3.eth.get_balance(w3.to_checksum_address(VAULT_ADDR))
            eth_balance = round(float(w3.from_wei(balance_wei, 'ether')), 6)
        except Exception as e:
            print(f"⚠️ Balance Fetch failed: {e}")
            eth_balance = "Error"

    # 3. Save to Database
    save_to_db("Aave", aave_val)
    save_to_db("Uniswap", uni_val)
    
    # 4. Construct Final JSON Output
    return {
        "yields": [
            {"platform": "Aave", "yield": f"{aave_val}%"},
            {"platform": "Uniswap", "yield": f"{uni_val}%"}
        ],
        "wallet": {
            "address": VAULT_ADDR,
            "balance_eth": eth_balance
        },
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }