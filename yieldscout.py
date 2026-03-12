import os
import time
import json
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

# The provided address (included the extra '9' for the auto-fix logic to handle)
BANKER_VAULT_ADDRESS = "0x456Eb50604f0C240A1F0C9d661338561Cc601889"

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
            raw_yield = (fee_delta / (2**128)) * annual_scaling * 0.1
            return round(max(0.1, min(raw_yield, 15.0)), 2)
        return 3.50
    except Exception as e:
        print(f"⚠️ Uni Error: {e}")
        return 3.50

def get_wallet_balances():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        
        # --- AUTO-FIX FOR ADDRESS LENGTH ---
        clean_addr = BANKER_VAULT_ADDRESS.strip()
        if len(clean_addr) > 42:
            clean_addr = clean_addr[:42] # Trims the extra '9'
        
        vault_addr = w3.to_checksum_address(clean_addr)
        
        # ETH Balance
        eth_wei = w3.eth.get_balance(vault_addr)
        eth_bal = float(w3.from_wei(eth_wei, 'ether'))
        
        # USDC Balance (6 decimals)
        usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_ADDR), abi=ERC20_ABI)
        usdc_raw = usdc_contract.functions.balanceOf(vault_addr).call()
        usdc_bal = float(usdc_raw / 10**6)
        
        print(f"📊 WALLET CHECK: {vault_addr} | ETH: {eth_bal:.4f} | USDC: {usdc_bal:.2f}")
        
        return {
            "eth": f"{eth_bal:.4f}",
            "usdc": f"{usdc_bal:.2f}"
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
        cur.execute("INSERT INTO yields (aave_rate, uniswap_rate, timestamp) VALUES (%s,