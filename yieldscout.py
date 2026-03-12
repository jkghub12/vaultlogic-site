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
# Primary RPC for Base (Yields)
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
# Public RPC for Ethereum Mainnet (to find your 2.64 ETH)
ETH_MAINNET_RPC = "https://eth.llamarpc.com"
DB_URL = os.getenv("DATABASE_URL")
BANKER_VAULT_ADDRESS = os.getenv("BANKER_VAULT_ADDRESS", "0x31d8210350bc719fDfde1149f6aEDF9420E1b889")

# Protocol Addresses (Base)
DATA_PROVIDER = "0xC4Fcf9893072d61Cc2899C0054877Cb752587981"
USDC_ADDR = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
UNI_POOL_ADDRESS = "0x4C36388bE6F416A29C8d8Eee81c771cE6bE14B18"

# ABIs
AAVE_ABI = [{"inputs": [{"name": "asset", "type": "address"}],"name": "getReserveData","outputs": [{"name": "unbacked", "type": "uint256"},{"name": "accruedToTreasuryScaled", "type": "uint256"},{"name": "totalAToken", "type": "uint256"},{"name": "totalStableDebt", "type": "uint256"},{"name": "totalVariableDebt", "type": "uint256"},{"name": "liquidityRate", "type": "uint256"},{"name": "variableBorrowRate", "type": "uint256"},{"name": "stableBorrowRate", "type": "uint256"},{"name": "averageStableBorrowRate", "type": "uint256"},{"name": "liquidityIndex", "type": "uint256"},{"name": "variableBorrowIndex", "type": "uint256"},{"name": "lastUpdateTimestamp", "type": "uint40"}],"stateMutability": "view","type": "function"}]
UNI_POOL_ABI = [{"inputs":[],"name":"feeGrowthGlobal0X128","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
ERC20_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

# Global State for Fee Calculation
last_fee_growth = None
last_check_time = None

def get_aave_yield():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        contract = w3.eth.contract(address=w3.to_checksum_address(DATA_PROVIDER), abi=AAVE_ABI)
        data = contract.functions.getReserveData(w3.to_checksum_address(USDC_ADDR)).call()
        return round((float(data[5]) / 1e27) * 100, 2)
    except Exception:
        return 2.42

def get_uniswap_yield():
    global last_fee_growth, last_check_time
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        pool = w3.eth.contract(address=w3.to_checksum_address(UNI_POOL_ADDRESS), abi=UNI_POOL_ABI)
        current_fees = pool.functions.feeGrowthGlobal0X128().call()
        current_time = time.time()
        
        if last_fee_growth is None or current_fees < last_fee_growth:
            last_fee_growth, last_check_time = current_fees, current_time
            return 3.50
        
        fee_delta = current_fees - last_fee_growth
        time_delta = current_time - last_check_time
        
        if fee_delta > 0 and time_delta > 0:
            annual_scaling = (365 * 24 * 3600) / time_delta
            # Calculation based on estimated pool share
            raw_yield = (fee_delta / (2**128)) * annual_scaling * 0.05
            return round(max(0.5, min(raw_yield, 20.0)), 2)
        return 3.50
    except Exception:
        return 3.50

def get_wallet_balances():
    try:
        # 1. Connect to both networks
        base_w3 = Web3(Web3.HTTPProvider(RPC_URL))
        eth_w3 = Web3(Web3.HTTPProvider(ETH_MAINNET_RPC))
        
        # Clean address
        vault_addr = base_w3.to_checksum_address(BANKER_VAULT_ADDRESS.strip()[:42])
        
        # 2. Get ETH from Base Network (The 0.0011 part)
        base_eth_wei = base_w3.eth.get_balance(vault_addr)
        base_eth = float(base_w3.from_wei(base_eth_wei, 'ether'))
        
        # 3. Get ETH from Ethereum Mainnet (The 2.64 part)
        mainnet_eth_wei = eth_w3.eth.get_balance(vault_addr)
        mainnet_eth = float(eth_w3.from_wei(mainnet_eth_wei, 'ether'))
        
        # 4. Get USDC from Base
        usdc_contract = base_w3.eth.contract(address=base_w3.to_checksum_address(USDC_ADDR), abi=ERC20_ABI)
        usdc_raw = usdc_contract.functions.balanceOf(vault_addr).call()
        usdc_bal = float(usdc_raw) / 1_000_000 
        
        # Totaling the ETH from both networks
        total_eth = base_eth + mainnet_eth
        
        return {
            "eth": f"{total_eth:.4f}",
            "usdc": f"{usdc_bal:.2f}"
        }
    except Exception as e:
        return {"eth": "0.0000", "usdc": "0.00"}

def save_to_db(aave_rate, uni_rate):
    if not DB_URL: return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS yields (id SERIAL PRIMARY KEY, aave_rate REAL, uniswap_rate REAL, timestamp TIMESTAMP);")
        cur.execute("INSERT INTO yields (aave_rate, uniswap_rate, timestamp) VALUES (%s, %s, %s)", (float(aave_rate), float(uni_rate), datetime.now()))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass

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
    while True:
        try:
            aave_val = get_aave_yield()
            uni_val = get_uniswap_yield()
            save_to_db(aave_val, uni_val)
        except Exception:
            pass
        await asyncio.sleep(300)