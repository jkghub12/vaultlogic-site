import os
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from eth_account import Account
from dotenv import load_dotenv

# AgentKit & YieldScout Imports
from coinbase_agentkit import (
    AgentKit, AgentKitConfig, EthAccountWalletProvider, 
    EthAccountWalletProviderConfig, cdp_api_action_provider,
    erc20_action_provider, basename_action_provider, wallet_action_provider
)
from yieldscout import get_all_yields

load_dotenv()

app = FastAPI(title="VaultLogic AI")

# Serve the Logo
app.mount("/static", StaticFiles(directory="."), name="static")

# --- 1. IDENTITY SETUP ---
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

# --- 2. THE BACKGROUND HEARTBEAT ---
# This keeps the database updating every 60 seconds
@app.on_event("startup")
async def start_heartbeat():
    async def heartbeat():
        while True:
            try:
                # This calls get_all_yields which triggers save_to_db internally
                get_all_yields()
                print("💓 Heartbeat: Vault Data Saved to DB")
            except Exception as e:
                print(f"💓 Heartbeat Error: {e}")
            await asyncio.sleep(60) 
    
    asyncio.create_task(heartbeat())

# --- 3. THE DASHBOARD UI ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic AI | Command Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #050a14; }
        .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col items-center justify-center p-6 text-center">
    <div class="max-w-md w-full glass rounded-3xl p-8 shadow-2xl">
        <div class="flex items-center justify-center mb-8">
            <img src="/static/VLlogo.png" alt="VL" class="h-12 w-auto mr-4 rounded-lg">
            <div class="text-left">
                <h1 class="text-2xl font-bold tracking-tight text-white">VaultLogic <span class="text-blue-500">AI</span></h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-widest">Autonomous Wealth Engine</p>
            </div>
        </div>
        <div class="mb-6">
            <p class="text-[9px] text-slate-500 uppercase mb-1">Agent Identity</p>
            <p class="text-[10px] font-mono text-blue-400 bg-blue-500/10 p-2 rounded-lg break-all">""" + wallet_provider.get_address() + """</p>
        </div>
        <div class="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 mb-6">
            <p class="text-xs text-slate-500 mb-1 uppercase">Aave V3 Yield</p>
            <h2 id="aave-yield" class="text-5xl font-bold text-green-400">--%</h2>
        </div>
        <div class="grid grid-cols-2 gap-4 mb-8">
            <div class="bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
                <p class="text-[10px] text-slate-500 uppercase">ETH</p>
                <p id="eth-bal" class="text-xl font-semibold">--</p>
            </div>
            <div class="bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
                <p class="text-[10px] text-slate-500 uppercase">USDC</p>
                <p id="usdc-bal" class="text-xl font-semibold">--</p>
            </div>
        </div>
        <div class="text-[10px] text-slate-700">Last Scan: <span id="timestamp">--</span></div>
    </div>
    <script>
        async function fetchVaultData() {
            try {
                const response = await fetch('/api/yield');
                const data = await response.json();
                document.getElementById('aave-yield').innerText = data.yields[0].yield;
                document.getElementById('eth-bal').innerText = data.wallet.balance_eth || data.wallet.eth;
                document.getElementById('usdc-bal').innerText = data.wallet.usdc || "0.00";
                document.getElementById('timestamp').innerText = data.last_updated;
            } catch (error) { console.error("AI Sync Error:", error); }
        }
        fetchVaultData();
        setInterval(fetchVaultData, 30000); 
    </script>
</body>
</html>
"""
import asyncio

# This is the "Engine" that runs in the background
@app.on_event("startup")
async def start_heartbeat():
    async def heartbeat():
        while True:
            try:
                # This is the magic line that saves to your Postgres
                print("💓 Banker is scanning and saving to Database...")
                get_all_yields() 
            except Exception as e:
                print(f"💓 Heartbeat Error: {e}")
            
            # Wait 60 seconds before scanning again
            await asyncio.sleep(60) 
    
    # This creates the task so it doesn't block the website from loading
    asyncio.create_task(heartbeat())

# --- 4. THE ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return HTML_CONTENT

@app.get("/api/yield")
async def yield_api():
    return get_all_yields()

if __name__ == "__main__":
    import uvicorn
    # Railway provides the PORT environment variable
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)