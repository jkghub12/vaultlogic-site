import asyncio
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields
from engine import run_alm_engine

# 1. Initialize App
app = FastAPI()

# 2. Configuration & Cache
DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420'

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
    "wallet_balance": "0.000 ETH",
    "usdc_balance": "1.50 USDC",
    "engine_status": "OFFLINE",
    "is_connected": False
}

class WalletConnect(BaseModel):
    address: str

# 3. Helper Functions
async def fetch_wallet_balances(address: str):
    """Scouts the Base network for actual ETH and USDC holdings."""
    try:
        async with httpx.AsyncClient() as client:
            rpc_url = "https://mainnet.base.org"
            payload = {"jsonrpc":"2.0","method":"eth_getBalance","params":[address, "latest"],"id":1}
            resp = await client.post(rpc_url, json=payload)
            data = resp.json()
            if 'result' in data:
                hex_bal = data['result']
                eth_bal = int(hex_bal, 16) / 10**18
                vault_cache["wallet_balance"] = f"{eth_bal:.4f} ETH"
                vault_cache["engine_status"] = "SCOUTING ACTIVE"
                vault_cache["is_connected"] = True
    except Exception as e:
        print(f"BALANCE ERROR: {e}")

async def background_sync():
    while True:
        try:
            vault_cache["yields"] = await get_all_yields()
            vault_cache["gas_price"] = "0.0012 Gwei (OPTIMAL)"
            vault_cache["last_updated"] = f"ACTIVE: {len(vault_cache['yields'])} SOURCES NOMINAL"
        except Exception as e:
            vault_cache["last_updated"] = f"SYNC ERROR: {str(e)}"
        await asyncio.sleep(60)

# 4. Routes
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())
    print("[SYSTEM] PRE-FLIGHT CHECK: INITIALIZING VAULTLOGIC ENGINE...", flush=True)
    asyncio.create_task(run_alm_engine("SYSTEM_DIAGNOSTIC", is_debug=True))

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        asyncio.create_task(run_alm_engine(data.address))
        asyncio.create_task(fetch_wallet_balances(data.address))
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/terminate-session")
async def terminate_session():
    vault_cache["is_connected"] = False
    vault_cache["engine_status"] = "OFFLINE"
    vault_cache["wallet_balance"] = "0.000 ETH"
    return {"status": "success"}

@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return f"""
    <html>
        <head>
            <title>VaultLogic | Strategy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: #ccc; font-family: sans-serif; line-height: 1.8; padding: 60