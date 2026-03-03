# app.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from yieldscout import DeFiYieldScout
import os
import asyncio
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VaultLogic Yield API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
W3_RPC = os.getenv("ETH_RPC_URL") # Use your env var
w3 = Web3(Web3.HTTPProvider(W3_RPC))
VAULT_ENV = os.getenv("BANKER_VAULT_ADDRESS")
BANKER_VAULT = Web3.to_checksum_address(VAULT_ENV)

# Initialize the scout
try:
    scout = DeFiYieldScout()
except Exception as e:
    print(f"Error starting Scout: {e}")
    scout = None

# --- BACKGROUND LOOP ---
async def active_banking_loop():
    print(f"🚀 [Banker Startup] Monitoring Vault: {BANKER_VAULT}")
    while True:
        try:
            balance_wei = w3.eth.get_balance(BANKER_VAULT)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            print(f"🏦 BANKER REPORT: Vault balance is {balance_eth:.6f} ETH")
        except Exception as e:
            print(f"❌ Banker Loop Error: {e}")
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(active_banking_loop())

# --- ROUTES ---
@app.get("/")
def read_root():
    return {
        "status": "online",
        "legal_entity": "VaultLogic Dev LLC",
        "engine": "On-Chain Banker v1",
        "message": "Proprietary financial intelligence engine active."
    }

@app.get("/api/yield")
async def get_yield():
    """Endpoint that returns the best yield option as JSON"""
    if not scout:
        raise HTTPException(status_code=500, detail="Yield Scout not initialized")
    try:
        data = scout.get_best_yield()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))