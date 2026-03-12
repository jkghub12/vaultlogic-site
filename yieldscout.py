import os
from web3 import Web3
# Standard for web3.py v7 and Layer 2s like Base
from web3.middleware import ExtraDataToPOAMiddleware
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
VAULT_ADDR = os.getenv("BANKER_VAULT_ADDRESS")

# OFFICIAL AAVE V3 BASE DATA PROVIDER (2026)
AAVE_DATA_PROVIDER = "0xC4Fcf9893072d61Cc2899C0054877Cb752587981"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Verified 12-item Struct for Aave V3 getReserveData
AAVE_ABI = [{
    "inputs": [{"name": "asset", "type": "address"}],
    "name": "getReserveData",
    "outputs": [
        {"name": "unbacked", "type": "uint256"},
        {"name": "accruedToTreasuryScaled", "type": "uint256"},
        {"name": "totalAToken", "type": "uint256"},
        {"name": "totalStableDebt", "type": "uint256"},
        {"name": "totalVariableDebt", "type": "uint256"},
        {"name": "liquidityRate", "type": "uint256"}, # APY at Index 5
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
        # Critical for Base Mainnet compatibility
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if not w3.is_connected():
            print("❌ RPC Connection Failed")
            return 4.15
            
        contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_DATA_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_BASE)).call()
        
        # Convert RAY (10^27) to standard percentage
        apy = (float(data[5]) / 1e27) * 100
        print(f"📡 Aave Data Fetched: {round(apy, 2)}%")
        return round(apy, 2)
    except Exception as e:
        print(f"⚠️ Aave Fetch Logic Error: {e}")
        return 4.15

def save_to_db(aave_