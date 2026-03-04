from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from yieldscout import DeFiYieldScout, save_to_railway
import os
import asyncio
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VaultLogic Yield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
W3_RPC = os.getenv("ETH_RPC_URL")
w3 = Web3(Web3.HTTPProvider(W3_RPC))
VAULT_ENV = os.getenv("BANKER_VAULT_ADDRESS", "0x0000000000000000000000000000000000000000")
BANKER_VAULT = Web3.to_checksum_address(VAULT_ENV)

try:
    scout = DeFiYieldScout()
except Exception as e:
    print(f"Error starting Scout: {e}")
    scout = None

# --- IMPROVED BANKER LOOP ---
async def active_banking_loop():
    print(f"🚀 [Banker Startup] Monitoring Vault: {BANKER_VAULT}")
    while True:
        try:
            # 1. Check Balance
            balance_wei = w3.eth.get_balance(BANKER_VAULT)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            
            # 2. Trigger a Scout and Save to DB automatically every minute
            if scout:
                current_data = scout.get_best_yield()
                save_to_railway(current_data)
                best = current_data[0]
                print(f"🏦 BANKER REPORT: Balance {balance_eth:.4f} ETH | Best Yield: {best['protocol']} ({best['apy']}%)")
            
        except Exception as e:
            print(f"❌ Banker Loop Error: {e}")
        
        await asyncio.sleep(60) # Run every minute

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(active_banking_loop())

@app.get("/")
def read_root():
    return {"status": "online", "engine": "VaultLogic Banker v1"}

@app.get("/api/yield")
async def get_yield():
    if not scout:
        raise HTTPException(status_code=500, detail="Yield Scout not initialized")
    try:
        data = scout.get_best_yield()
        # Also trigger a save when the web API is called
        save_to_railway(data)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))