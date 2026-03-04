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

app = FastAPI(title="VaultLogic Ecosystem")

# Connect the Logo/Static files
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

# --- 2. THE BACKGROUND ENGINE (Heartbeat + Logic) ---
@app.on_event("startup")
async def start_engine():
    async def heartbeat():
        while True:
            try:
                # 1. Pull data and save to Postgres
                get_all_yields()
                print("💓 Engine Sync: Data logged to Database.")
                
                # 2. Rebalancer Logic could go here next...
                
            except Exception as e:
                print(f"💓 Engine Error: {e}")
            await asyncio.sleep(60) 
    
    asyncio.create_task(heartbeat())

# --- 3. UI COMPONENTS (HTML) ---

# GENERIC LANDING PAGE (Public)
LANDING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>VaultLogic | Autonomous Systems</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { background: #020617; font-family: sans-serif; }</style>
</head>
<body class="text-slate-200">
    <nav class="p-8 flex justify-between items-center max-w-6xl mx-auto">
        <div class="flex items-center">
            <img src="/static/VLlogo.png" class="h-10 mr-3">
            <span class="text-2xl font-bold tracking-tighter">VaultLogic</span>
        </div>
        <a href="/vault" class="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-full text-sm font-semibold transition">Enter Vault</a>
    </nav>
    <header class="py-20 text-center px-4">
        <h1 class="text-6xl font-extrabold mb-6">Engineering Logic into <span class="text-blue-500">Value.</span></h1>
        <p class="max-w-2xl mx-auto text-slate-400 text-xl leading-relaxed">
            VaultLogic develops autonomous ecosystems for digital and physical assets. 
            Smart capital, smarter logistics, absolute logic.
        </p>
    </header>
</body>
</html>
"""

# CRYPTO DASHBOARD (Private)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>VaultLogic AI | Command Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #050a14; }
        .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-md w-full glass rounded-3xl p-8 shadow-2xl">
        <div class="flex items-center mb-8">
            <img src="/static/VLlogo.png" alt="VL" class="h-10 w-auto mr-4 rounded-lg">
            <div>
                <h1 class="text-2xl font-bold text-white uppercase tracking-tighter">VaultLogic <span class="text-blue-500">Banker</span></h1>
                <p class="text-[9px] text-slate-500 uppercase tracking-widest italic">Capital Rebalancer v1.0</p>
            </div>
        </div>
        <div class="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 mb-6 text-center">
            <p class="text-xs text-slate-500 mb-1 uppercase">Aave V3 Base Yield</p>
            <h2 id="aave-yield" class="text-5xl font-bold text-green-400">--%</h2>
        </div>
        <div class="grid grid-cols-2 gap-4 mb-8 text-center">
            <div class="bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
                <p class="text-[10px] text-slate-500 uppercase">ETH Balance</p>
                <p id="eth-bal" class="text-xl font-semibold">--</p>
            </div>
            <div class="bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
                <p class="text-[10px] text-slate-500 uppercase">USDC Balance</p>
                <p id="usdc-bal" class="text-xl font-semibold">--</p>
            </div>
        </div>
        <div class="text-[10px] text-center text-slate-700">System Status: Active | Last Scan: <span id="timestamp">--</span></div>
    </div>
    <script>
        async function update() {
            try {
                const res = await fetch('/api/yield');
                const d = await res.json();
                document.getElementById('aave-yield').innerText = d.yields[0].yield;
                document.getElementById('eth-bal').innerText = d.wallet.balance_eth || d.wallet.eth;
                document.getElementById('usdc-bal').innerText = d.wallet.usdc || "0.00";
                document.getElementById('timestamp').innerText = d.last_updated;
            } catch (e) { console.log(e); }
        }
        update(); setInterval(update, 30000);
    </script>
</body>
</html>
"""

# --- 4. THE ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home():
    return LANDING_HTML

@app.get("/vault", response_class=HTMLResponse)
async def vault_dashboard():
    return DASHBOARD_HTML

@app.get("/api/yield")
async def yield_api():
    return get_all_yields()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)