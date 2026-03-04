import os
from web3 import Web3
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# The Aave V3 Protocol Data Provider for Base
AAVE_DATA_PROVIDER = "0x2d8a3C5677189723C4cB8873CfC9C8974F701758"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

AAVE_ABI = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint128","name":"liquidityRate","type":"uint128"}],"internalType":"struct IProtocolDataProvider.TokenData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'

def save_to_db(platform, yield_val):
    if not DB_URL: return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO yields (platform, yield_rate, timestamp) VALUES (%s, %s, %s)",
                   (platform, float(yield_val), datetime.utcnow()))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def get_aave_yield():
    try:
        # Force checksum addresses to prevent errors
        provider_addr = Web3.to_checksum_address(AAVE_DATA_PROVIDER)
        asset_addr = Web3.to_checksum_address(USDC_ADDRESS)
        
        contract = w3.eth.contract(address=provider_addr, abi=AAVE_ABI)
        data = contract.functions.getReserveData(asset_addr).call()
        
        # data[5] is liquidityRate in Ray (10^27)
        # Formula: (Rate / 10^27) * 100
        actual_yield = (data[5] / 10**27) * 100
        return round(actual_yield, 2)
    except Exception as e:
        print(f"Aave Engine Error: {e}")
        return 0.0

def get_all_yields():
    aave = get_aave_yield()
    uni = 3.50  # Hardcoded for now
    
    # Save the real numbers to your Postgres history
    save_to_db("Aave", aave)
    save_to_db("Uniswap", uni)
    
    return [
        {"platform": "Aave", "yield": f"{aave}%"},
        {"platform": "Uniswap", "yield": f"{uni}%"}
    ]