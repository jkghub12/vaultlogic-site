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
# Refined Provider Address for Base Mainnet
AAVE_PROVIDER = "0x2d8a3C5677189723C4cB8873CfC9C8974F701758"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Minimal ABI for Aave Data Provider
AAVE_ABI = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint40"}],"name":"","type":"tuple"}],"stateMutability":"view","type":"function"}]'

# Minimal ERC20 ABI for USDC balance
ERC20_ABI = '[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]'

def get_aave_yield():
    try:
        if not w3.is_connected():
            print("❌ Web3 not connected to RPC")
            return 4.15
            
        contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_PROVIDER), abi=AAVE_ABI)
        
        # getReserveData returns a tuple; the liquidityRate is index 5
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_BASE)).call()
        
        # Aave rates are in RAY (10^27)
        ray = 10**27
        # Convert to percentage
        apy = (float(data[5]) / ray) * 100
        
        if apy > 0:
            print(f"✅ Aave USDC Yield: {round(apy, 2)}%")
            return round(apy, 2)
        else:
            print("⚠️ Aave returned 0 APY, using fallback.")
            return 4.15
            
    except Exception as e:
        print(f"⚠️ Aave Fetch failed: {e}")
        return 4.15 

def get_wallet_balances():
    balances = {"eth": "0.00", "usdc": "0.00"}
    if not VAULT_ADDR:
        return balances

    try:
        checksum_addr = w3.to_checksum_address(VAULT_ADDR)
        
        # 1. Get ETH Balance
        eth_wei = w3.eth.get_balance(checksum_addr)
        balances["eth"] = str(round(float(w3.from_wei(eth_wei, 'ether')), 6))
        
        # 2. Get USDC Balance
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_BASE), abi=ERC20_ABI)
        usdc_raw = usdc_contract.functions.balanceOf(checksum_addr).call()
        # USDC has 6 decimals
        balances["usdc"] = str(round(usdc_raw / 10**6, 2))
        
    except Exception as e:
        print(f"⚠️ Balance Fetch failed: {e}")
    
    return balances

def save_to_db(aave_rate, uni_rate):
    if not DB_URL: 
        print("⚠️ No DATABASE_URL found.")
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # We removed the CREATE TABLE line from here. 
        # Now the script will only try to INSERT data.
        cur.execute(
            "INSERT INTO yields (aave_rate, uniswap_rate) VALUES (%s, %s)", 
            (aave_rate, uni_rate)
        )
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ DB Error: {e}")

def get_all_yields():
    aave_val = get_aave_yield()
    uni_val = 3.50 # Uniswap logic can be added later
    
    save_to_db(aave_val, uni_val)
    wallet = get_wallet_balances()
    
    return {
        "yields": [
            {"protocol": "Aave", "yield": f"{aave_val}%"},
            {"protocol": "Uniswap", "yield": f"{uni_val}%"}
        ],
        "wallet": wallet,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }