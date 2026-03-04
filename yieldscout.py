import os
import requests
from web3 import Web3
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL") # Provided by Railway
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Correct Aave V3 Data Provider on Base
AAVE_DATA_PROVIDER = "0x2d8a3C5677189723C4cB8873CfC9C8974F701758"
# Simple ABI for Aave
AAVE_ABI = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint128","name":"liquidityRate","type":"uint128"}],"internalType":"struct IProtocolDataProvider.TokenData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'

USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

def save_to_db(platform, yield_val):
    if not DB_URL:
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO yields (platform, yield_rate, timestamp) VALUES (%s, %s, %s)",
            (platform, yield_val, datetime.utcnow())
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def get_aave_yield():
    try:
        contract = w3.eth.contract(address=AAVE_DATA_PROVIDER, abi=AAVE_ABI)
        data = contract.functions.getReserveData(USDC_ADDRESS).call()
        # Ray conversion (1e27) to percentage
        rate = (data[5] / 10**27) * 100
        return round(rate, 2)
    except Exception as e:
        print(f"Aave Error: {e}")
        return 0.0

def get_uniswap_yield():
    # Placeholder for Uniswap logic or API call
    return 3.50 

def get_all_yields():
    aave = get_aave_yield()
    uni = get_uniswap_yield()
    
    # Save to DB for history
    save_to_db("Aave", aave)
    save_to_db("Uniswap", uni)
    
    return [
        {"platform": "Aave", "yield": f"{aave}%"},
        {"platform": "Uniswap", "yield": f"{uni}%"}
    ]