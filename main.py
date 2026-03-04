import os
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from eth_account import Account
from dotenv import load_dotenv

from coinbase_agentkit import (
    AgentKit, AgentKitConfig, EthAccountWalletProvider, 
    EthAccountWalletProviderConfig, cdp_api_action_provider,
    erc20_action_provider, basename_action_provider, wallet_action_provider
)
# This is the important import
from yieldscout import get_all_yields

load_dotenv()

app = FastAPI(title="VaultLogic AI")

app.mount("/static", StaticFiles(directory="."), name="static")

# --- 1. AGENTKIT IDENTITY SETUP ---
def get_llc_account():
    with open("vaultlogic_wallet.json", "r") as f:
        data = json.load(f)
        return Account.from_key(data["private_key"])

wallet_provider = EthAccountWalletProvider(
    EthAccountWalletProviderConfig(
        account=get_llc_account(),
        chain_id="8453"
    )
)

# --- 2. THE BACKGROUND HEARTBEAT (The Database Updater) ---
@app.on_event("startup")
async def start_heartbeat():
    async def heartbeat():
        while True:
            try:
                # This triggers the save_to_db inside yieldscout
                print("💓 Heartbeat: Syncing VaultLogic AI to Database...")
                get_all_yields() 
            except Exception as e:
                print(f"💓 Heartbeat Error: {e}")
            await asyncio.sleep(60) # Run every minute
    
    asyncio.create_task(heartbeat())

# --- 3. THE DASHBOARD UI ---
# (Keep your HTML_CONTENT variable here exactly as you have it)
HTML_CONTENT = """...""" # Use your existing HTML here

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return HTML_CONTENT

@app.get("/api/yield")
async def yield_api():
    return get_all_yields()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))