import asyncio
import random
import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

# --- V3.3 CORE KERNEL (STABLE BASELINE) ---
class VaultKernel:
    def __init__(self):
        self.vaults = {
            "AAVE_V3_BASE": {"apy": 6.2, "tvl": "42.1M", "risk": "Low"},
            "COMPOUND_V3": {"apy": 5.8, "tvl": "18.5M", "risk": "Low"},
            "MORPHO_BLUE": {"apy": 9.4, "tvl": "8.2M", "risk": "Med"},
            "AERODROME_LP": {"apy": 14.2, "tvl": "2.1M", "risk": "High"}
        }
        self.active_position = None
        self.logs = ["[SYSTEM] Kernel v3.3 initialized. Ready for deployment."]

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {msg}")
        if len(self.logs) > 40: self.logs.pop(0)

    def deploy(self, address, amount):
        self.active_position = {
            "address": address,
            "principal": amount,
            "profit": 0.0,
            "venue": "AAVE_V3_BASE",
            "start_time": datetime.now()
        }
        self.log(f"DEPLOYED: ${amount:,.2f} to {address[:10]}...")
        return True

    def tick(self):
        if self.active_position:
            # v3.3 math: steady growth with random volatility spikes
            growth = (self.active_position["principal"] * (0.085 / 525600)) * (random.uniform(0.8, 1.2))
            self.active_position["profit"] += growth
            if random.random() > 0.98:
                old = self.active_position["venue"]
                self.active_position["venue"] = random.choice(list(self.vaults.keys()))
                self.log(f"ALM EVENT: Migrating from {old} to {self.active_position['venue']} (Yield Optimization)")

kernel = VaultKernel()

# --- API ROUTES ---
@app.post("/api/deploy")
async def deploy_endpoint(data: dict):
    kernel.deploy(data['address'], float(data['amount']))
    return {"status": "success"}

@app.get("/api/state")
async def get_state(address: str):
    return {
        "position": kernel.active_position,
        "vaults": kernel.vaults,
        "logs": kernel.logs
    }

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | V3.3 Industrial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        body { background: #05070a; color: #f8fafc; font-family: 'JetBrains Mono', monospace; }
        .panel { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        .custom-range { -webkit-appearance: none; height: 4px; background: #1e293b; border-radius: 2px; }
        .custom-range::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; background: #38bdf8; border-radius: 50%; cursor: pointer; }
    </style>
</head>
<body class="p-6">
    <div class="max-w-7xl mx-auto">
        <!-- HEADER -->
        <header class="flex justify-between items-center mb-10 border-b border-white/5 pb-6">
            <div>
                <h1 class="text-2xl font-bold tracking-tighter uppercase">VaultLogic <span class="text-sky-500">v3.3</span></h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-widest">Autonomous Asset-Liability Kernel</p>
            </div>
            <button id="connectBtn" onclick="connect()" class="bg-white text-black px-6 py-2 rounded text-[10px] font-bold uppercase hover:bg-sky-500 hover:text-white transition-all">Connect Wallet</button>
        </header>

        <div id="mainUI" class="opacity-30 pointer-events-none transition-opacity duration-500">
            <!-- STATS GRID -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div class="panel p-6">
                    <p class="text-[9px] text-slate-500 uppercase mb-2">Portfolio Principal</p>
                    <p id="statPrincipal" class="text-2xl font-bold">$0.00</p>
                </div>
                <div class="panel p-6">
                    <p class="text-[9px] text-emerald-500 uppercase mb-2">Net Realized Profit</p>
                    <p id="statProfit" class="text-2xl font-bold text-emerald-400">$0.0000</p>
                </div>
                <div class="panel p-6">
                    <p class="text-[9px] text-sky-500 uppercase mb-2">Current Venue</p>
                    <p id="statVenue" class="text-xl font-bold uppercase text-sky-400">IDLE</p>
                </div>
                <div class="panel p-6">
                    <p class="text-[9px] text-slate-500 uppercase mb-2">Kernel Status</p>
                    <p class="text-xl font-bold uppercase"><span class="status-dot bg-emerald-500 mr-2"></span>Active</p>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <!-- CONTROLS & VAULTS -->
                <div class="lg:col-span-4 space-y-6">
                    <div class="panel p-8">
                        <h3 class="text-[10px] font-bold uppercase text-slate-400 mb-6">Execution Engine</h3>
                        <div class="mb-8">
                            <div class="flex justify-between text-[10px] mb-4">
                                <span>Deployment Size</span>
                                <span id="amtVal" class="text-sky-400">$50,000</span>
                            </div>
                            <input type="range" min="1000" max="250000" value="50000" step="1000" class="w-full custom-range" id="amtInput" oninput="updateRange(this.value)">
                        </div>
                        <button onclick="deploy()" class="w-full bg-sky-600 py-4 rounded font-bold text-[10px] uppercase tracking-widest hover:bg-white hover:text-black transition-all">Execute ALM Strategy</button>
                    </div>

                    <div class="panel p-6">
                        <h3 class="text-[10px] font-bold uppercase text-slate-400 mb-4">Available Venues</h3>
                        <div id="vaultList" class="space-y-3"></div>
                    </div>
                </div>

                <!-- TERMINAL -->
                <div class="lg:col-span-8">
                    <div class="panel h-full flex flex-col min-h-[500px]">
                        <div class="p-4 border-b border-white/5 flex justify-between items-center">
                            <span class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Live Execution Log</span>
                            <span class="text-[10px] text-slate-600">v3.3.08-STABLE</span>
                        </div>
                        <div id="terminal" class="p-6 text-[11px] space-y-2 overflow-y-auto max-h-[500px] flex-grow"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let wallet = null;

        async function connect() {
            if (window.ethereum) {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                wallet = accounts[0];
                document.getElementById('connectBtn').innerText = wallet.substring(0,6) + '...' + wallet.substring(38);
                document.getElementById('mainUI').classList.remove('opacity-30', 'pointer-events-none');
                startSync();
            }
        }

        function updateRange(v) {
            document.getElementById('amtVal').innerText = '$' + parseInt(v).toLocaleString();
        }

        async function deploy() {
            const amount = document.getElementById('amtInput').value;
            await fetch('/api/deploy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({address: wallet, amount: amount})
            });
        }

        function startSync() {
            setInterval(async () => {
                const res = await fetch(`/api/state?address=${wallet}`);
                const data = await res.json();
                
                if (data.position) {
                    document.getElementById('statPrincipal').innerText = '$' + data.position.principal.toLocaleString();
                    document.getElementById('statProfit').innerText = '$' + data.position.profit.toLocaleString(undefined, {minimumFractionDigits: 4});
                    document.getElementById('statVenue').innerText = data.position.venue.replace(/_/g, ' ');
                }

                // Update Terminal
                const term = document.getElementById('terminal');
                term.innerHTML = data.logs.map(log => `<div class="text-slate-400"><span class="text-sky-800">>></span> ${log}</div>`).reverse().join('');

                // Update Vaults
                const vList = document.getElementById('vaultList');
                vList.innerHTML = Object.entries(data.vaults).map(([name, info]) => `
                    <div class="flex justify-between items-center p-3 bg-white/5 rounded border border-white/5">
                        <span class="text-[10px] font-bold uppercase">${name.replace(/_/g, ' ')}</span>
                        <span class="text-[10px] text-emerald-400">${info.apy}% APY</span>
                    </div>
                `).join('');

            }, 2000);
        }
    </script>
</body>
</html>
"""

async def background_loop():
    while True:
        kernel.tick()
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup():
    asyncio.create_task(background_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)