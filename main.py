import asyncio
import random
import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

# --- V3.3 INDUSTRIAL KERNEL (RESTORED) ---
class VaultKernel:
    def __init__(self):
        self.vaults = {
            "AAVE_V3_BASE": {"apy": 6.2, "tvl": "42.1M", "risk": "Low"},
            "COMPOUND_V3": {"apy": 5.8, "tvl": "18.5M", "risk": "Low"},
            "MORPHO_BLUE": {"apy": 9.4, "tvl": "8.2M", "risk": "Med"},
            "AERODROME_LP": {"apy": 14.2, "tvl": "2.1M", "risk": "High"}
        }
        self.active_position = None
        self.logs = ["[SYSTEM] Kernel v3.3 Restoration Complete.", "[SYSTEM] Institutional Floor: $10,000 USD."]

    def log(self, msg, type="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {type}: {msg}")
        if len(self.logs) > 50: self.logs.pop(0)

    def deploy(self, address, amount):
        # RULE: REJECT LESS THAN 10K
        if amount < 10000:
            self.log(f"REJECTED: ${amount:,.2f} is below Industrial Floor.", "RISK")
            return False
            
        self.active_position = {
            "address": address,
            "principal": amount,
            "profit": 0.0,
            "venue": "AAVE_V3_BASE",
            "start_time": datetime.now()
        }
        self.log(f"DEPLOYED: ${amount:,.2f} to {address[:10]}...", "SUCCESS")
        return True

    def tick(self):
        if self.active_position:
            # v3.3 yield math
            growth = (self.active_position["principal"] * (0.072 / 525600)) * (random.uniform(0.9, 1.1))
            self.active_position["profit"] += growth
            if random.random() > 0.98:
                old = self.active_position["venue"]
                self.active_position["venue"] = random.choice(list(self.vaults.keys()))
                self.log(f"ALM REBALANCE: Migrated from {old} to {self.active_position['venue']}", "ALM")

kernel = VaultKernel()

# --- API ROUTES ---
@app.post("/api/deploy")
async def deploy_endpoint(data: dict):
    success = kernel.deploy(data['address'], float(data['amount']))
    return {"status": "success" if success else "failed"}

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
    <title>VaultLogic | Industrial v3.3</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        body { background: #020408; color: #f8fafc; font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.05); }
        .status-pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
        .custom-range { -webkit-appearance: none; height: 4px; background: #1e293b; border-radius: 2px; }
        .custom-range::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; background: #38bdf8; border-radius: 50%; cursor: pointer; }
    </style>
</head>
<body class="p-4 md:p-10">
    <div class="max-w-6xl mx-auto">
        <nav class="flex justify-between items-end mb-12 border-b border-white/5 pb-8">
            <div>
                <h1 class="text-xl font-bold tracking-tighter uppercase italic">VaultLogic <span class="text-sky-500">v3.3_Restored</span></h1>
                <p class="text-[9px] text-slate-500 uppercase tracking-widest mt-1">Autonomous Institutional Kernel</p>
            </div>
            <div class="flex gap-4">
                <button onclick="bypassCheck()" class="text-[9px] text-slate-600 border border-slate-800 px-3 py-1 rounded hover:text-white transition-all uppercase">Bypass Handshake</button>
                <button id="connectBtn" onclick="connect()" class="bg-white text-black px-6 py-2 rounded text-[10px] font-bold uppercase hover:bg-sky-500 hover:text-white transition-all">Authenticate</button>
            </div>
        </nav>

        <div id="mainUI" class="opacity-20 pointer-events-none transition-all duration-1000">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div class="glass p-6 rounded-xl">
                    <p class="text-[9px] text-slate-500 uppercase mb-2">Target Yield</p>
                    <p class="text-2xl font-bold text-sky-400">7.2%<span class="text-xs ml-1 font-normal text-slate-600 uppercase">APY</span></p>
                </div>
                <div class="glass p-6 rounded-xl">
                    <p class="text-[9px] text-emerald-500 uppercase mb-2">Net Profit</p>
                    <p id="statProfit" class="text-2xl font-bold text-emerald-400">$0.0000</p>
                </div>
                <div class="glass p-6 rounded-xl">
                    <p class="text-[9px] text-slate-500 uppercase mb-2">Active Principal</p>
                    <p id="statPrincipal" class="text-2xl font-bold">$0.00</p>
                </div>
                <div class="glass p-6 rounded-xl">
                    <p class="text-[9px] text-slate-500 uppercase mb-2">Kernel Status</p>
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 bg-emerald-500 rounded-full status-pulse"></div>
                        <p class="text-sm font-bold uppercase">Optimizing</p>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div class="lg:col-span-4 space-y-6">
                    <div class="glass p-8 rounded-2xl">
                        <h3 class="text-[10px] font-bold uppercase text-slate-400 mb-6">Strategy Deployment</h3>
                        <div class="mb-8">
                            <div class="flex justify-between text-[10px] mb-4">
                                <span class="text-slate-500 uppercase">Deployment Size</span>
                                <span id="amtVal" class="text-sky-400 font-bold">$10,000</span>
                            </div>
                            <input type="range" min="1000" max="250000" value="10000" step="1000" class="w-full custom-range" id="amtInput" oninput="updateRange(this.value)">
                            <p class="text-[8px] text-slate-600 uppercase mt-4 text-center tracking-tighter">Min Floor: $10,000 USDC</p>
                        </div>
                        <button id="deployBtn" onclick="deploy()" class="w-full bg-sky-600 py-4 rounded-lg font-bold text-[10px] uppercase tracking-widest hover:bg-white hover:text-black transition-all">Initialize Kernel</button>
                    </div>

                    <div class="glass p-6 rounded-xl">
                        <h3 class="text-[10px] font-bold uppercase text-slate-400 mb-4 tracking-widest">Yield Venues</h3>
                        <div id="vaultList" class="space-y-2 opacity-60"></div>
                    </div>
                </div>

                <div class="lg:col-span-8">
                    <div class="glass rounded-2xl h-full flex flex-col min-h-[500px]">
                        <div class="p-4 border-b border-white/5 flex justify-between items-center bg-white/5">
                            <span class="text-[9px] font-bold uppercase tracking-widest text-slate-400">Kernel Audit Log</span>
                            <span class="text-[8px] text-slate-600">BUILD_RESTORE_3.3</span>
                        </div>
                        <div id="terminal" class="p-6 text-[10px] space-y-2 overflow-y-auto max-h-[550px] flex-grow leading-relaxed"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let wallet = "0xUSER_BYPASS";
        
        function bypassCheck() {
            document.getElementById('mainUI').classList.remove('opacity-20', 'pointer-events-none');
            document.getElementById('connectBtn').innerText = "BYPASS_ACTIVE";
            startSync();
        }

        async function connect() {
            if (window.ethereum) {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                wallet = accounts[0];
                document.getElementById('connectBtn').innerText = wallet.substring(0,6) + '...' + wallet.substring(38);
                document.getElementById('mainUI').classList.remove('opacity-20', 'pointer-events-none');
                startSync();
            }
        }

        function updateRange(v) {
            document.getElementById('amtVal').innerText = '$' + parseInt(v).toLocaleString();
            const btn = document.getElementById('deployBtn');
            if(v < 10000) {
                btn.classList.add('bg-slate-800', 'text-slate-500');
                btn.classList.remove('bg-sky-600');
                btn.innerText = "BELOW_FLOOR";
            } else {
                btn.classList.remove('bg-slate-800', 'text-slate-500');
                btn.classList.add('bg-sky-600');
                btn.innerText = "INITIALIZE KERNEL";
            }
        }

        async function deploy() {
            const amount = document.getElementById('amtInput').value;
            const res = await fetch('/api/deploy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({address: wallet, amount: amount})
            });
            const data = await res.json();
            if(data.status === "failed") {
                // Flash terminal on failure
            }
        }

        function startSync() {
            setInterval(async () => {
                const res = await fetch(`/api/state?address=${wallet}`);
                const data = await res.json();
                
                if (data.position) {
                    document.getElementById('statPrincipal').innerText = '$' + data.position.principal.toLocaleString();
                    document.getElementById('statProfit').innerText = '$' + data.position.profit.toLocaleString(undefined, {minimumFractionDigits: 4});
                }

                const term = document.getElementById('terminal');
                term.innerHTML = data.logs.map(log => {
                    const color = log.includes('RISK') ? 'text-red-400' : (log.includes('SUCCESS') ? 'text-emerald-400' : 'text-slate-400');
                    return `<div class="${color}"><span class="text-sky-900">#</span> ${log}</div>`;
                }).reverse().join('');

                const vList = document.getElementById('vaultList');
                vList.innerHTML = Object.entries(data.vaults).map(([name, info]) => `
                    <div class="flex justify-between items-center text-[10px] p-2 hover:bg-white/5 transition-all">
                        <span class="font-bold text-slate-300 tracking-tighter">${name.replace(/_/g, ' ')}</span>
                        <span class="text-sky-500">${info.apy}%</span>
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