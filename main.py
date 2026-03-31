import asyncio
import random
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

# --- THE STABLE INDUSTRIAL KERNEL ---
class VaultKernel:
    def __init__(self):
        self.vaults = {
            "AAVE_V3_BASE": {"apy": 6.4, "tvl": "42.1M", "risk": "Low"},
            "COMPOUND_V3": {"apy": 5.9, "tvl": "18.5M", "risk": "Low"},
            "MORPHO_BLUE": {"apy": 9.2, "tvl": "8.2M", "risk": "Med"},
            "AERODROME_LP": {"apy": 14.8, "tvl": "2.1M", "risk": "High"}
        }
        self.active_positions = {}
        self.logs = ["[SYSTEM] Kernel v3.3 Industrial Restoration Active.", "[SYSTEM] Institutional Floor enforced at $10,000.00 USD."]

    def log(self, msg, category="KERNEL"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {category}: {msg}")
        if len(self.logs) > 60: self.logs.pop(0)

    def deploy(self, address, amount):
        # INSTITUTIONAL FLOOR CHECK
        if amount < 10000:
            self.log(f"REJECTED: ${amount:,.2f} is below the 10k floor requirement.", "SECURITY")
            return False
            
        self.active_positions[address] = {
            "principal": amount,
            "profit": 0.0,
            "venue": "AAVE_V3_BASE",
            "start_time": datetime.now(),
            "status": "OPTIMIZING"
        }
        self.log(f"SUCCESS: ${amount:,.2f} liquidity bridge established for {address[:10]}...", "EXECUTION")
        return True

    def rebalance(self):
        # AUTOMATED ALM LOGIC
        if not self.active_positions: return
        
        for addr in self.active_positions:
            if random.random() > 0.95: # 5% chance per tick to find a better yield
                old_venue = self.active_positions[addr]["venue"]
                new_venue = random.choice([v for v in self.vaults.keys() if v != old_venue])
                self.active_positions[addr]["venue"] = new_venue
                self.log(f"REBALANCING: Migrating {addr[:8]} assets from {old_venue} to {new_venue} (+{random.uniform(0.1, 0.5):.2f}% Yield Spread)", "ALM")

    def tick(self):
        for addr, pos in self.active_positions.items():
            # Standard Industrial Yield Math
            apy = self.vaults[pos["venue"]]["apy"] / 100
            growth = (pos["principal"] * (apy / 31536000) * 10) # 10x simulation speed
            pos["profit"] += growth

kernel = VaultKernel()

# --- API ENDPOINTS ---
@app.post("/api/deploy")
async def deploy(data: dict):
    success = kernel.deploy(data['address'], float(data['amount']))
    return {"status": "success" if success else "failed"}

@app.get("/api/state")
async def get_state(address: str):
    return {
        "position": kernel.active_positions.get(address),
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
    <title>VaultLogic | Industrial ALM</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;700&display=swap');
        body { background: #030508; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(10, 15, 25, 0.8); border: 1px solid rgba(255,255,255,0.04); backdrop-filter: blur(12px); }
        .btn-primary { background: #fff; color: #000; font-weight: 900; transition: all 0.2s; }
        .btn-primary:hover { background: #0ea5e9; color: #fff; transform: translateY(-1px); }
        .custom-range { -webkit-appearance: none; height: 4px; background: #1e293b; border-radius: 2px; width: 100%; }
        .custom-range::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; background: #fff; border-radius: 50%; cursor: pointer; border: 2px solid #0ea5e9; }
        .terminal-row { border-left: 2px solid #1e293b; padding-left: 12px; margin-bottom: 8px; transition: all 0.3s; }
        .terminal-row:hover { border-left-color: #0ea5e9; background: rgba(14, 165, 233, 0.03); }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto">
        <!-- HEADER -->
        <header class="flex justify-between items-center mb-12 border-b border-white/5 pb-8">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center font-black text-black text-xl italic">V</div>
                <div>
                    <h1 class="text-xl font-bold tracking-tighter uppercase italic">VaultLogic</h1>
                    <p class="text-[9px] text-slate-500 uppercase tracking-[0.3em] font-black">Industrial Asset-Liability Management</p>
                </div>
            </div>
            <div class="flex gap-3">
                <button onclick="bypass()" class="text-[9px] font-black text-slate-500 border border-slate-800 px-4 py-2 rounded uppercase hover:text-sky-400 hover:border-sky-400 transition-all">Bypass Handshake</button>
                <button id="connectBtn" onclick="connect()" class="btn-primary px-6 py-2 rounded text-[10px] uppercase tracking-widest">Connect Wallet</button>
            </div>
        </header>

        <div id="dashboard" class="opacity-20 pointer-events-none transition-all duration-700">
            <!-- TOP STATS -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div class="glass p-6 rounded-2xl">
                    <p class="text-[9px] text-slate-500 uppercase font-black mb-2 tracking-widest">Principal Under Management</p>
                    <p id="statPrincipal" class="text-3xl font-bold mono tracking-tighter">$0.00</p>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <p class="text-[9px] text-emerald-500 uppercase font-black mb-2 tracking-widest">Net Realized Profit</p>
                    <p id="statProfit" class="text-3xl font-bold text-emerald-400 mono tracking-tighter">$0.0000</p>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <p class="text-[9px] text-sky-500 uppercase font-black mb-2 tracking-widest">Current Yield Venue</p>
                    <p id="statVenue" class="text-xl font-bold uppercase mono tracking-tighter mt-1 text-sky-100">IDLE</p>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <p class="text-[9px] text-slate-500 uppercase font-black mb-2 tracking-widest">Rebalance Pulse</p>
                    <div class="flex items-center gap-3 mt-1">
                        <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                        <span class="text-xs font-black uppercase tracking-widest">Optimal</span>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <!-- CONTROLS -->
                <div class="lg:col-span-4 space-y-6">
                    <div class="glass p-8 rounded-3xl">
                        <h3 class="text-[10px] font-black uppercase text-sky-500 mb-8 tracking-widest">Strategy Deployment</h3>
                        <div class="mb-10">
                            <div class="flex justify-between text-[10px] font-black uppercase mb-4">
                                <span class="text-slate-500">Allocation Size</span>
                                <span id="amtVal" class="text-white">$10,000</span>
                            </div>
                            <input type="range" min="1000" max="250000" value="10000" step="1000" class="custom-range" id="amtInput" oninput="updateUI(this.value)">
                            <div class="flex justify-between mt-4 text-[8px] font-black text-slate-600 uppercase">
                                <span>$1,000</span>
                                <span>Institutional Floor: $10,000</span>
                            </div>
                        </div>
                        <button id="deployBtn" onclick="execute()" class="w-full py-5 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] transition-all bg-slate-800 text-slate-500 pointer-events-none">Initialize Kernel</button>
                    </div>

                    <div class="glass p-6 rounded-2xl">
                        <h3 class="text-[10px] font-black uppercase text-slate-500 mb-4 tracking-widest">Live Venues</h3>
                        <div id="vaultGrid" class="space-y-2"></div>
                    </div>
                </div>

                <!-- TERMINAL -->
                <div class="lg:col-span-8">
                    <div class="glass rounded-3xl h-full flex flex-col min-h-[550px] overflow-hidden">
                        <div class="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                            <span class="text-[9px] font-black uppercase tracking-widest text-slate-400">Autonomous Kernel Audit Log</span>
                            <span class="text-[8px] font-black text-slate-600 mono">v3.3.RESTORED</span>
                        </div>
                        <div id="terminal" class="p-8 mono text-[10px] overflow-y-auto max-h-[500px] flex-grow custom-scrollbar space-y-1"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let wallet = null;
        let syncID = null;

        function bypass() {
            wallet = "VAULTLOGIC_ADMIN_BYPASS";
            unlock();
        }

        async function connect() {
            if (window.ethereum) {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                wallet = accounts[0];
                unlock();
            }
        }

        function unlock() {
            document.getElementById('connectBtn').innerText = wallet.substring(0,8).toUpperCase() + "...";
            document.getElementById('dashboard').classList.remove('opacity-20', 'pointer-events-none');
            if(!syncID) startSync();
        }

        function updateUI(v) {
            document.getElementById('amtVal').innerText = '$' + parseInt(v).toLocaleString();
            const btn = document.getElementById('deployBtn');
            if(v < 10000) {
                btn.className = "w-full py-5 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] bg-slate-800 text-slate-500 pointer-events-none";
                btn.innerText = "BELOW INSTITUTIONAL FLOOR";
            } else {
                btn.className = "w-full py-5 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] bg-sky-600 text-white hover:bg-white hover:text-black cursor-pointer";
                btn.innerText = "INITIALIZE KERNEL";
            }
        }

        async function execute() {
            const val = document.getElementById('amtInput').value;
            await fetch('/api/deploy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({address: wallet, amount: val})
            });
        }

        function startSync() {
            syncID = setInterval(async () => {
                const res = await fetch(`/api/state?address=${wallet}`);
                const data = await res.json();
                
                if (data.position) {
                    document.getElementById('statPrincipal').innerText = '$' + data.position.principal.toLocaleString();
                    document.getElementById('statProfit').innerText = '$' + data.position.profit.toLocaleString(undefined, {minimumFractionDigits: 4});
                    document.getElementById('statVenue').innerText = data.position.venue.replace(/_/g, ' ');
                }

                const term = document.getElementById('terminal');
                term.innerHTML = data.logs.map(log => {
                    let color = "text-slate-400";
                    if(log.includes("REJECTED") || log.includes("SECURITY")) color = "text-red-400";
                    if(log.includes("SUCCESS") || log.includes("ALM")) color = "text-sky-400";
                    return `<div class="terminal-row ${color}"><span class="opacity-20 mr-2">></span>${log}</div>`;
                }).reverse().join('');

                const grid = document.getElementById('vaultGrid');
                grid.innerHTML = Object.entries(data.vaults).map(([name, info]) => `
                    <div class="flex justify-between items-center p-3 border border-white/5 rounded-lg bg-white/5">
                        <span class="text-[10px] font-black uppercase text-slate-300">${name.replace(/_/g, ' ')}</span>
                        <span class="text-[10px] font-black text-emerald-400">${info.apy}% APY</span>
                    </div>
                `).join('');
            }, 1500);
        }
        
        // Initial button check
        updateUI(10000);
    </script>
</body>
</html>
"""

async def kernel_loop():
    while True:
        kernel.tick()
        kernel.rebalance()
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup():
    asyncio.create_task(kernel_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)