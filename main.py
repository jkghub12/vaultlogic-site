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
    EthAccountWalletProviderConfig
)
from yieldscout import get_all_yields

load_dotenv()

app = FastAPI(title="VaultLogic Ecosystem")

# Connect the Logo (Make sure VLlogo.png is in your GitHub root)
app.mount("/static", StaticFiles(directory="."), name="static")

# --- 1. IDENTITY & ENGINE ---
def get_llc_account():
    with open("vaultlogic_wallet.json", "r") as f:
        data = json.load(f)
        return Account.from_key(data["private_key"])

@app.on_event("startup")
async def start_engine():
    async def heartbeat():
        while True:
            try:
                # This pulls yields and logs them to your Postgres DB
                get_all_yields()
                print("💓 VaultLogic Engine: Yields Synced.")
            except Exception as e:
                print(f"💓 Engine Error: {e}")
            await asyncio.sleep(60) 
    asyncio.create_task(heartbeat())

# --- 2. PUBLIC LANDING PAGE (vaultlogic.dev) ---
LANDING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>VaultLogic | Autonomous Systems</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#020617] text-white font-sans">
    <nav class="p-8 flex justify-between items-center max-w-6xl mx-auto">
        <div class="flex items-center">
            <img src="/static/VLlogo.png" class="h-10 mr-3 rounded">
            <span class="text-2xl font-bold tracking-tighter uppercase">VaultLogic</span>
        </div>
        <a href="/vault" class="border border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white px-6 py-2 rounded-full text-sm transition">Client Access</a>
    </nav>
    <main class="mt-24 text-center px-4">
        <h1 class="text-7xl font-black mb-6 italic">Logic is <span class="text-blue-500">Value.</span></h1>
        <p class="max-w-2xl mx-auto text-slate-400 text-xl leading-relaxed mb-10">
            VaultLogic builds autonomous engines for the management of digital and physical assets. 
            From DeFi rebalancing to real-world logistics.
        </p>
        <div class="flex justify-center gap-4">
            <div class="p-6 bg-slate-900/50 rounded-2xl border border-slate-800 w-48">
                <p class="text-blue-500 font-bold">Capital</p>
                <p class="text-xs text-slate-500">Autonomous DeFi</p>
            </div>
            <div class="p-6 bg-slate-900/50 rounded-2xl border border-slate-800 w-48 opacity-50">
                <p class="text-slate-400 font-bold">Physical</p>
                <p class="text-xs text-slate-500">Coming Soon</p>
            </div>
        </div>
    </main>
</body>
</html>
"""

# --- 3. PRIVATE BANKER DASHBOARD (vaultlogic.dev/vault) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>VaultLogic Banker</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#050a14] text-slate-200 flex flex-col items-center justify-center min-h-screen p-6">
    <div class="max-w-md w-full bg-slate-900/80 backdrop-blur-md rounded-3xl p-8 border border-white/10 shadow-2xl">
        <div class="flex items-center mb-10">
            <img src="/static/VLlogo.png" class="h-12 w-auto mr-4 rounded-lg">
            <div>
                <h1 class="text-2xl font-black text-white uppercase tracking-tighter">VaultLogic <span class="text-blue-500 italic">Banker</span></h1>
                <p class="text-[9px] text-blue-400 uppercase tracking-[0.2em] font-bold">Autonomous Yield Agent</p>
            </div>
        </div>
        
        <div class="space-y-4">
            <div class="bg-black/40 p-6 rounded-2xl border border-slate-800 text-center">
                <p class="text-[10px] text-slate-500 uppercase mb-1">Target Yield (Aave V3)</p>
                <h2 id="aave-yield" class="text-5xl font-mono font-bold text-green-400">--%</h2>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-black/40 p-4 rounded-2xl border border-slate-800">
                    <p class="text-[10px] text-slate-500 uppercase">Wallet ETH</p>
                    <p id="eth-bal" class="text-xl font-bold text-white">--</p>
                </div>
                <div class="bg-black/40 p-4 rounded-2xl border border-slate-800">
                    <p class="text-[10px] text-slate-500 uppercase">Wallet USDC</p>
                    <p id="usdc-bal" class="text-xl font-bold text-white">--</p>
                </div>
            </div>
        </div>
        <div class="mt-8 text-[9px] text-center text-slate-600 uppercase tracking-widest">
            System Status: <span class="text-green-500">Operational</span> | <span id="timestamp">--</span>
        </div>
    </div>

    <script>
        async function update() {
            try {
                const res = await fetch('/api/yield');
                const d = await res.json();
                document.getElementById('aave-yield').innerText = d.yields[0].yield;
                document.getElementById('eth-bal').innerText = d.wallet.eth.substring(0,6);
                document.getElementById('usdc-bal').innerText = d.wallet.usdc || "0.00";
                document.getElementById('timestamp').innerText = d.last_updated;
            } catch (e) { console.error(e); }
        }
        update(); setInterval(update, 30000);
    </script>
</body>
</html>
"""

# --- 4. ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return LANDING_HTML

@app.get("/vault", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/api/yield")
async def yield_api():
    return get_all_yields()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)