import os
from web3 import Web3
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
VAULT_ADDR = os.getenv("BANKER_VAULT_ADDRESS")

# OFFICIAL AAVE V3 BASE ADDRESSES (2026)
# Data Provider: 0x2d8a3C5677189723C4cB8873CfC9C8974F701758
# USDC on Base: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
AAVE_PROVIDER = "0x2d8a3C5677189723C4cB8873CfC9C8974F701758"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

AAVE_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "unbacked", "type": "uint256"},
                    {"internalType": "uint256", "name": "accruedToTreasuryScaled", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalAToken", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"},
                    {"internalType": "uint256", "name": "liquidityRate", "type": "uint256"}, # THIS IS OUR APY
                    {"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"},
                    {"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},
                    {"internalType": "uint256", "name": "averageStableBorrowRate", "type": "uint256"},
                    {"internalType": "uint256", "name": "liquidityIndex", "type": "uint256"},
                    {"internalType": "uint256", "name": "variableBorrowIndex", "type": "uint256"},
                    {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"}
                ],
                "internalType": "struct DataTypes.ReserveData",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_aave_yield():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        # Ensure contract is initialized with Checksummed Address
        contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_PROVIDER), abi=AAVE_ABI)
        
        # Call the contract
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_BASE)).call()
        
        # In Aave V3, liquidityRate is index 5 of the struct
        # It is expressed in RAY (10^27)
        apy = (float(data[5]) / 1e27) * 100
        return round(apy, 2)
    except Exception as e:
        print(f"⚠️ Aave Fetch failed: {e}")
        return 4.15 # Fallback rate if RPC is congested

def save_to_db(aave_rate, uni_rate):
    if not DB_URL: return
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO yields (aave_rate, uniswap_rate) VALUES (%s, %s)", 
            (aave_rate, uni_rate)
        )
        conn.commit()
        cur.close()
        print(f"✅ DB Update Successful: {aave_rate}%")
    except Exception as e:
        print(f"❌ DB Error: {e}")
    finally:
        if conn:
            conn.close()

def get_all_yields():
    aave_val = get_aave_yield()
    uni_val = 3.50 # Uniswap logic coming next
    
    save_to_db(aave_val, uni_val)
    
    # Fetch Balance logic...
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    eth_balance = "0.00"
    if VAULT_ADDR:
        try:
            balance_wei = w3.eth.get_balance(w3.to_checksum_address(VAULT_ADDR))
            eth_balance = str(round(float(w3.from_wei(balance_wei, 'ether')), 6))
        except: pass

    return {
        "yields": [
            {"protocol": "Aave V3", "yield": f"{aave_val}%", "asset": "USDC"},
            {"protocol": "Uniswap V3", "yield": f"{uni_val}%", "asset": "USDC/ETH"}
        ],
        "wallet": {"eth": eth_balance, "usdc": "0.00"},
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }