import os
import time
import asyncio
import psycopg2
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
DB_URL = os.getenv("DATABASE_URL")
BANKER_VAULT_ADDRESS = "0x456Eb50604f0C240A1F0C9d661338561Cc60188"

# Protocol Addresses
DATA_PROVIDER = "0xC4Fcf9893072d61Cc2899C0054877Cb752587981"
USDC_ADDR = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
UNI_POOL_ADDRESS = "0x4C36388bE6F416A29C8d8Eee81c771cE6bE14B18"

# ABIs
AAVE_ABI = [{"inputs": [{"name": "asset", "type": "address"}],"name": "getReserveData","outputs": [{"name": "unbacked", "type": "uint256"},{"name": "accruedToTreasuryScaled", "type": "uint256"},{"name": "totalAToken", "type": "uint256"},{"name": "totalStableDebt", "type": "uint256"},{"name": "totalVariableDebt", "type": "uint256"},{"name": "liquidityRate", "type": "uint256"},{"name": "variableBorrowRate", "type": "uint256"},{"name": "stableBorrowRate", "type": "uint256"},{"name": "averageStableBorrowRate", "type": "uint256"},{"name": "liquidityIndex", "type": "uint256"},{"name": "variableBorrowIndex", "type": "uint256"},{"name": "lastUpdateTimestamp", "type": "uint40"}],"stateMutability": "view","type": "function"}]
UNI_POOL_ABI = [{"inputs":[],"name":"feeGrowthGlobal0X128","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
ERC20_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

# Global State for Uniswap
last_fee_growth = None
last_check_time = None

def get_aave_yield():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        contract = w3.eth.contract(address=w3.to_checksum_address(DATA_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_ADDR)).call()
        return round((float(data[5]) / 1e27) * 100, 2)
    except Exception as e:
        print(f"⚠️ Aave Error: {e}")
        return 4.15

def get_uniswap_yield():
    global last_fee_growth, last_check_time
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        pool = w3.eth.contract(address=w3.to_checksum_address(UNI_POOL_ADDRESS), abi=UNI_POOL_ABI)
        current_fees = pool.functions.feeGrowthGlobal0X128().call()
        current_time = time.time()
        
        if last_fee_growth is None:
            last_fee_growth, last_check_time = current_fees, current_time
            return 3.50
        
        fee_delta = current_fees - last_fee_growth
        time_delta = current_time - last_check_time
        
        if fee_delta > 0 and time_delta > 0:
            annual_scaling = (365 * 24 * 3600) / time_delta
            raw_yield = (fee_delta / (2**128)) * annual_scaling * 100 
            return round(max(0.1, min(raw_yield, 50.0)), 2)
        return 3.50
    except Exception as e:
        print(f"⚠️ Uni Error: {e}")
        return 3.50

def get_wallet_balances():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        vault_addr = w3.to_checksum_address(BANKER_VAULT_ADDRESS)
        
        # ETH Balance
        eth_wei = w3.eth.get_balance(vault_addr)
        eth_bal = w3.from_wei(eth_wei, 'ether')
        
        # USDC Balance (USDC has 6 decimals)
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_ADDR), abi=ERC20_ABI)
        usdc_raw = usdc_contract.functions.balanceOf(vault_addr).call()
        usdc_bal = usdc_raw / 10**6
        
        return {
            "eth": f"{round(float(eth_bal), 4)}",
            "usdc": f"{round(float(usdc_bal), 2)}"
        }
    except Exception as e:
        print(f"⚠️ Balance Error: {e}")
        return {"eth": "0.00", "usdc": "0.00"}

def save_to_db(aave_rate, uni_rate):
    if not DB_URL: return
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS yields (id SERIAL PRIMARY KEY, aave_rate REAL, uniswap_rate REAL, timestamp TIMESTAMP);")
        cur.execute("INSERT INTO yields (aave_rate, uniswap_rate, timestamp) VALUES (%s, %s, %s)", (float(aave_rate), float(uni_rate), datetime.now()))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ DB SYNC: Aave {aave_rate}% | Uni {uni_rate}%")
    except Exception as e:
        print(f"❌ DB FAILED: {e}")

def get_all_yields():
    aave = get_aave_yield()
    uni = get_uniswap_yield()
    balances = get_wallet_balances()
    return {
        "yields": [
            {"protocol": "Aave V3", "yield": f"{aave}%", "asset": "USDC"},
            {"protocol": "Uniswap V3", "yield": f"{uni}%", "asset": "USDC/ETH"}
        ],
        "wallet": balances,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

async def heartbeat_monitor():
    """ The new bulletproof background task """
    print("💓 VaultLogic Engine: Async Heartbeat Active")
    while True:
        try:
            aave_val = get_aave_yield()
            uni_val = get_uniswap_yield()
            save_to_db(aave_val, uni_val)
        except Exception as e:
            print(f"💓 Engine Error: {e}")
        await asyncio.sleep(300) # Sync every 5 minutes