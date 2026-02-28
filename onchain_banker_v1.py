import os
import uvicorn
import httpx
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3
from dotenv import load_dotenv

# 1. Load the "hidden" environment variables
load_dotenv()

app = FastAPI()

# Enable CORS so your website can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configuration
W3_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(W3_RPC))

VAULT_ENV = os.getenv("BANKER_VAULT_ADDRESS", "0x456Eb50604f0C240A1F0C9d661338561Cc601889")
BANKER_VAULT = Web3.to_checksum_address(VAULT_ENV)
REQUIRED_AMOUNT_ETH = "0.0001"

# --- NEW: THE ACTIVE BANKER LOGIC ---

async def active_banking_loop():
    """Proactively monitors your vault balance in the background."""
    print(f"🚀 [Banker Startup] Monitoring Vault: {BANKER_VAULT}")
    while True:
        try:
            balance_wei = w3.eth.get_balance(BANKER_VAULT)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            print(f"🏦 BANKER REPORT: Vault balance is {balance_eth:.6f} ETH")
        except Exception as e:
            print(f"❌ Banker Loop Error: {e}")
        
        await asyncio.sleep(60) # Wait 60 seconds

@app.on_event("startup")
async def startup_event():
    # This starts the background loop when Railway turns the app on
    asyncio.create_task(active_banking_loop())

# --- END ACTIVE BANKER LOGIC ---

async def fetch_live_base_yields():
    """Mock-up alpha data; in production, this would scrape DEXs or use DeFiLlama API."""
    return [
        {"platform": "Aerodrome", "pool": "WETH/USDC", "apy": "12.5%", "risk": "Low"},
        {"platform": "Beefy", "pool": "cbETH/ETH", "apy": "4.2%", "risk": "Minimal"},
        {"platform": "Moonwell", "pool": "USDC", "apy": "5.8%", "risk": "Low"}
    ]

@app.get("/")
async def read_root():
    return {
        "status": "online",
        "legal_entity": "VaultLogic Dev LLC",  # Official Name
        "engine": "On-Chain Banker v1",
        "message": "Proprietary financial intelligence engine active."
    }
@app.get("/scout")
async def scout_yields(request: Request):
    """
    The 'Bouncer' endpoint. 
    Requires a 'proof' header (Transaction Hash) to release data.
    """
    proof = request.headers.get("X-Payment-Proof")

    if not proof:
        # Trigger the 402 Payment Required response
        return JSONResponse(
            status_code=402,
            content={
                "message": "Payment Required to access VaultLogic Alpha",
                "amount_eth": REQUIRED_AMOUNT_ETH,
                "pay_to": BANKER_VAULT,
                "network": "Base Mainnet"
            }
        )

    try:
        tx = w3.eth.get_transaction(proof)
        
        if tx['to'].lower() != BANKER_VAULT.lower():
            raise HTTPException(status_code=402, detail="Payment sent to wrong address.")
            
        if tx['value'] < w3.to_wei(REQUIRED_AMOUNT_ETH, 'ether'):
            raise HTTPException(status_code=402, detail="Insufficient payment amount.")
            
    except Exception:
        raise HTTPException(status_code=402, detail="Transaction not confirmed or invalid.")

    print(f"💰 SUCCESS: Payment verified for TX {proof[:10]}...")
    live_data = await fetch_live_base_yields()
    
    return {
        "status": "PAID",
        "service": "Vaultlogic Yield Scout",
        "top_opportunities": live_data,
        "vault_received_at": BANKER_VAULT
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)