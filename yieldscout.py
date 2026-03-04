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

# OFFICIAL AAVE V3 DATA PROVIDER (BASE MAINNET)
AAVE_PROVIDER_ADDRESS = "0x2d8a3C5677189723C4cB8873CfC9C8974F701758"
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
    # 1. Verify Connection
    if not w3.is_connected():
        print("❌ Not connected to Base node")
        return 0.0

    try:
        # Checksum the addresses
        provider_addr = w3.to_checksum_address(AAVE_PROVIDER_ADDRESS)
        asset_addr = w3.to_checksum_address(USDC_ADDRESS)

        # 2. Verify Contract exists at address
        code = w3.eth.get_code(provider_addr)
        if code == b'' or code == b'\x00':
            print(f"❌ No contract code found at {provider_addr}")
            return 0.0

        # 3. Connect to contract
        contract = w3.eth.contract(address=provider_addr, abi=AAVE_ABI)
        
        # 4. Fetch Data (liquidityRate is the 6th element, index 5)
        reserve_data = contract.functions.getReserveData(asset_addr).call()
        
        # Convert RAY (10^27) to percentage
        apy = (reserve_data[5] / 10**27) * 100
        return round(apy, 2)

    except Exception as e:
        print(f"Aave Error: {e}")
        return 0.0

def get_all_yields():
    aave_val = get_aave_yield()
    uni_val = 3.50  # Placeholder
    
    # Save to Postgres
    save_to_db("Aave", aave_val)
    save_to_db("Uniswap", uni_val)
    
    return [
        {"platform": "Aave", "yield": f"{aave_val}%"},
        {"platform": "Uniswap", "yield": f"{uni_val}%"}
    ]