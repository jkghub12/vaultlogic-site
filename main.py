import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import random
import json

# --- VAULTLOGIC ENGINE KERNEL (Updated with Rebalancing Logic) ---
class VaultLogicKernel:
    def __init__(self):
        self.active_deployments = {}
        # Target Allocations based on engine.py architecture
        self.protocols = {
            "Aave V3": {"weight": 0.40, "base_apy": 0.042},
            "Morpho Blue": {"weight": 0.50, "base_apy": 0.051},
            "Aerodrome": {"weight": 0.10, "base_apy": 0.124}
        }

    def get_market_state(self):
        """Simulates live market drift for rebalancing triggers"""
        state = {}
        total_apy = 0
        for name, data in self.protocols.items():
            # Add stochastic drift to simulate real market conditions
            drift = random.uniform(-0.005, 0.005)
            current_apy = data["base_apy"] + drift
            # Simulate slight weight drift for the UI to "rebalance"
            weight_drift = random.uniform(-0.02, 0.02)
            state[name] = {
                "apy": current_apy * 100,
                "allocation": (data["weight"] + weight_drift) * 100,
                "target": data["weight"] * 100
            }
            total_apy += current_apy * data["weight"]
        return state, total_apy * 100

    def get_stats(self, addr): 
        if addr in self.active_deployments:
            data = self.active_deployments[addr]
            elapsed = (datetime.now() - data['start_time']).total_seconds()
            market_state, net_apy = self.get_market_state()
            
            # Continuous compounding calculation
            profit = data['principal'] * (net_apy / 100 / (365 * 24 * 3600)) * elapsed
            
            return {
                "principal": data['principal'], 
                "net_profit": profit,
                "apy": net_apy,
                "market_state": market_state,
                "status": "REBALANCING_OPTIMIZED"
            }
        return None

    def deploy(self, addr, amt, mode):
        self.active_deployments[addr] = {
            "principal": amt,
            "start_time": datetime.now(),
            "strategy": "INSTITUTIONAL_ALM",
            "mode": mode
        }
        tag = "[SANDBOX]" if mode == "sandbox" else "[LIVE]"
        return f"{tag} ENGINE INITIALIZED: Rebalancing logic active for {addr[:8]}. Target: 40% Aave / 50% Morpho / 10% Aero."

kernel = VaultLogicKernel()
app = FastAPI()

audit_logs = ["VAULTLOGIC V4.3.2: REBALANCING ENGINE ONLINE."]

class EngineInit(BaseModel):
    address: str
    amount: float
    is_sandbox: bool = False

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] KERNEL: {msg.upper()}")
    if len(audit_logs) > 30: audit_logs.pop(0)

@app.get("/stats/{address}")
async def get_stats(address: str):
    stats = kernel.get_stats(address)
    return {"stats": stats, "logs": audit_logs}

@app.post("/activate")
async def activate(data: EngineInit):
    if not data.is_sandbox and data.amount < 10000:
        add_log(f"REJECTED: ${data.amount:,.2f} is below floor.")
        return {"status": "error", "message": "Rejected: <$10k Floor"}
    
    mode = "sandbox" if data.is_sandbox else "live"
    msg = kernel.deploy(data.address, data.amount, mode)
    add_log(msg)
    return {"status": "success", "mode": mode}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Institutional ALM</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body { background: #010204; color: #f8fafc; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .glass { background: rgba(10, 15, 25, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
        .accent-gradient { background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); }
        .sandbox-gradient { background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); }
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        input[type=range] { -webkit-appearance: none; background: #0f172a; height: 4px; border-radius: 2px; }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 18px; width: 18px;
            background: #0ea5e9;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 15px rgba(14, 165, 233, 0.4);
            border: 2px solid #010204;
        }
        .hidden-bank { display: none !important; }
        .plaid-card:hover { transform: translateY(-2px); border-color: rgba(14, 165, 233, 0.4); }
        .rebalance-bar { transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1); }
    </style>
</head>
<body class="p-6 md:p-12 min-h-screen flex flex-col items-center">

    <!-- Wallet Modal -->
    <div id="walletModal" class="fixed inset-0 z-[600] hidden items-center justify-center bg-black/90 backdrop-blur-sm p-4">
        <div class="glass max-w-md w-full rounded-[2.5rem] overflow-hidden border border-white/10 shadow-2xl">
            <div class="p-8 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                <h3 class="font-black text-lg uppercase italic tracking-tighter text-sky-400">Connect Identity</h3>
                <button onclick="closeWallets()" class="text-slate-500 hover:text-white transition-colors">✕</button>
            </div>
            <div class="p-8 space-y-3">
                <div onclick="connectWith('Base')" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-sky-500/30 bg-sky-500/5 hover:bg-sky-500/10 transition-all">
                    <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-white text-[10px]">BASE</div>
                    <p class="text-[11px] font-black uppercase tracking-widest">Base Smart Wallet</p>
                </div>
                <div onclick="connectWith('Binance')" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer hover:bg-white/5 transition-all">
                    <div class="w-10 h-10 bg-yellow-500/20 rounded-full flex items-center justify-center text-yellow-500 font-bold text-[10px]">BNB</div>
                    <p class="text-[11px] font-black uppercase tracking-widest text-slate-300">Binance Web3</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Plaid Modal -->
    <div id="plaidModal" class="fixed inset-0 z-[700] hidden items-center justify-center bg-black/95 backdrop-blur-md p-4">
        <div class="glass max-w-md w-full rounded-[2.5rem] overflow-hidden border border-white/10 shadow-2xl">
            <div class="p-8 border-b border-white/5 bg-white/[0.02]">
                <div class="flex justify-between items-center mb-6">
                    <div class="flex items-center gap-2">
                        <span class="w-2 h-2 bg-sky-500 rounded-full"></span>
                        <span class="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">Plaid Auth</span>
                    </div>
                    <button onclick="closePlaid()" class="text-slate-500 hover:text-white">✕</button>
                </div>
                <h3 class="text-xl font-black italic uppercase tracking-tighter mb-4">Select Institution</h3>
                <input type="text" id="bankSearch" onkeyup="filterBanks()" placeholder="Search..." 
                       class="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-6 text-[11px] font-bold tracking-widest focus:outline-none focus:border-sky-500/50">
            </div>
            <div class="p-8 space-y-3 max-h-[300px] overflow-y-auto custom-scroll" id="bankList">
                <div onclick="selectBank('Chase')" class="plaid-card flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-white/5 bg-white/[0.01]">
                    <div class="w-10 h-10 bg-blue-700 rounded-xl flex items-center justify-center text-white font-black text-xs">C</div>
                    <p class="text-[11px] font-black uppercase tracking-widest">Chase Bank</p>
                </div>
                <div onclick="selectBank('BOA')" class="plaid-card flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-white/5 bg-white/[0.01]">
                    <div class="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center text-white font-black text-xs">B</div>
                    <p class="text-[11px] font-black uppercase tracking-widest">Bank of America</p>
                </div>
            </div>
        </div>
    </div>

    <header class="max-w-7xl w-full flex justify-between items-center mb-12">
        <div class="flex items-center gap-5">
            <div class="w-14 h-14 accent-gradient rounded-2xl flex items-center justify-center text-white font-black text-3xl italic shadow-2xl">V</div>
            <div>
                <h1 class="text-3xl font-black italic uppercase tracking-tighter leading-none">VaultLogic</h1>
                <p class="text-[10px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-1.5">ALM Engine V4.3.2</p>
            </div>
        </div>
        <div id="authGroup" class="flex gap-4">
            <button onclick="openWallets()" class="bg-white text-black px-10 py-4 rounded-2xl font-black text-[12px] uppercase tracking-[0.2em]">Connect</button>
            <button onclick="toggleSandbox()" class="text-slate-500 font-black text-[11px] uppercase tracking-widest">Sandbox</button>
        </div>
        <div id="walletDisplay" class="hidden glass px-6 py-3 rounded-2xl flex items-center gap-5">
            <span id="addrText" class="text-[11px] font-mono font-bold text-slate-300">0x...</span>
            <button onclick="location.reload()" class="text-[10px] font-black text-red-500 uppercase">Disconnect</button>
        </div>
    </header>

    <main class="max-w-7xl w-full relative grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div id="blockOverlay" class="absolute inset-0 z-10 flex flex-col items-center pt-32 text-center pointer-events-none">
            <h2 class="text-3xl font-black italic uppercase text-slate-800/40 tracking-tighter">Auth Required</h2>
        </div>

        <!-- Controls -->
        <div class="lg:col-span-4 space-y-6">
            <div id="strategyCard" class="glass p-10 rounded-[2.5rem] opacity-10 blur-sm pointer-events-none transition-all">
                <h3 id="strategyLabel" class="text-[10px] font-black uppercase tracking-[0.5em] text-sky-500 mb-8">Parameters</h3>
                <div class="space-y-10">
                    <div>
                        <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-4">
                            <span>Principal</span>
                            <span id="amtVal" class="text-sky-400 font-mono text-base font-black">$0</span>
                        </div>
                        <input type="range" id="amtRange" min="0" max="500000" step="1000" value="0" class="w-full"
                               oninput="document.getElementById('amtVal').innerText = '$'+parseInt(this.value).toLocaleString()">
                    </div>
                    <button id="deployBtn" onclick="initKernel()" class="w-full py-6 accent-gradient text-white font-black rounded-3xl text-[11px] uppercase tracking-[0.3em]">Initialize Engine</button>
                </div>
            </div>

            <div id="plaidContainer" class="transition-all">
                <div onclick="openPlaid()" class="glass p-8 rounded-[2rem] cursor-pointer hover:border-sky-500/30 transition-all flex items-center justify-between bg-white/[0.01]">
                    <p id="bankStatusText" class="text-[11px] font-black text-white uppercase tracking-widest">Link Bank Account</p>
                    <span class="text-slate-500">🏦</span>
                </div>
            </div>
        </div>

        <!-- Dashboard -->
        <div id="mainTerminal" class="lg:col-span-8 glass p-10 rounded-[2.5rem] opacity-10 blur-sm pointer-events-none transition-all flex flex-col gap-8">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="p-8 rounded-[2rem] bg-white/[0.02] border border-white/5">
                    <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Portfolio Value</p>
                    <h2 id="principalDisplay" class="text-4xl font-black italic tracking-tighter">$0</h2>
                </div>
                <div class="p-8 rounded-[2rem] bg-white/[0.02] border border-white/5">
                    <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Net Accrued</p>
                    <h2 id="liveProfit" class="text-4xl font-black text-emerald-400 italic tracking-tighter tabular-nums">$0.0000</h2>
                </div>
            </div>

            <!-- Rebalancing Monitor -->
            <div class="p-8 rounded-[2rem] bg-white/[0.01] border border-white/5">
                <div class="flex justify-between items-center mb-6">
                    <h4 class="text-[11px] font-black uppercase tracking-[0.3em] text-slate-400">Rebalancing Monitor</h4>
                    <div class="flex items-center gap-2">
                        <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                        <span id="netApyText" class="text-[10px] font-black text-emerald-500">APY: 0.00%</span>
                    </div>
                </div>
                <div id="rebalanceContainer" class="space-y-6">
                    <!-- Dynamic Bars -->
                </div>
            </div>

            <div id="logOutput" class="font-mono text-[10px] space-y-2 h-40 overflow-y-auto custom-scroll pr-4 opacity-60"></div>
        </div>
    </main>

    <script>
        let walletAddress = null;
        let syncTimer = null;
        let isSandbox = false;

        function openWallets() { document.getElementById('walletModal').classList.replace('hidden', 'flex'); }
        function closeWallets() { document.getElementById('walletModal').classList.replace('flex', 'hidden'); }
        function openPlaid() { document.getElementById('plaidModal').classList.replace('hidden', 'flex'); }
        function closePlaid() { document.getElementById('plaidModal').classList.replace('flex', 'hidden'); }

        function filterBanks() {
            let input = document.getElementById('bankSearch').value.toLowerCase();
            document.querySelectorAll('.plaid-card').forEach(item => {
                item.style.display = item.innerText.toLowerCase().includes(input) ? "flex" : "none";
            });
        }

        function selectBank(name) {
            document.getElementById('bankStatusText').innerText = "LINKED: " + name.toUpperCase();
            document.getElementById('bankStatusText').className = "text-[11px] font-black text-sky-400 uppercase tracking-widest";
            closePlaid();
        }

        function toggleSandbox() { walletAddress = "SANDBOX_MOCK_" + Math.random().toString(16).slice(2,6).toUpperCase(); isSandbox = true; onAuthSuccess(); }
        function connectWith(provider) { walletAddress = "0x" + Math.random().toString(16).slice(2,42).toUpperCase(); isSandbox = false; onAuthSuccess(); }

        function onAuthSuccess() {
            closeWallets();
            document.getElementById('authGroup').classList.add('hidden');
            document.getElementById('blockOverlay').classList.add('hidden');
            document.getElementById('walletDisplay').classList.remove('hidden');
            document.getElementById('addrText').innerText = isSandbox ? "SANDBOX_MOCK" : walletAddress.slice(0,10) + "...";
            
            if(isSandbox) document.getElementById('plaidContainer').classList.add('hidden-bank');
            
            document.getElementById('strategyCard').classList.remove('opacity-10', 'pointer-events-none', 'blur-sm');
            document.getElementById('mainTerminal').classList.remove('opacity-10', 'pointer-events-none', 'blur-sm');
            startSync();
        }

        async function initKernel() {
            const amount = parseFloat(document.getElementById('amtRange').value);
            const btn = document.getElementById('deployBtn');
            if (!isSandbox && amount < 10000) return;

            await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: walletAddress, amount: amount, is_sandbox: isSandbox })
            });
            btn.innerText = "ALGORITHM ENGAGED";
            btn.disabled = true;
        }

        function startSync() {
            syncTimer = setInterval(async () => {
                if (!walletAddress) return;
                try {
                    const res = await fetch('/stats/' + walletAddress);
                    const data = await res.json();
                    if (data.stats) {
                        document.getElementById('principalDisplay').innerText = '$' + data.stats.principal.toLocaleString();
                        document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 5});
                        document.getElementById('netApyText').innerText = `APY: ${data.stats.apy.toFixed(2)}%`;
                        updateRebalanceUI(data.stats.market_state);
                    }
                    if (data.logs) {
                        document.getElementById('logOutput').innerHTML = data.logs.map(l => `<div class="mb-1 border-l border-white/10 pl-3 py-1"> ${l.split('KERNEL: ')[1] || l}</div>`).reverse().join('');
                    }
                } catch (e) {}
            }, 2000);
        }

        function updateRebalanceUI(market) {
            const container = document.getElementById('rebalanceContainer');
            if (!container.innerHTML.trim()) {
                container.innerHTML = Object.keys(market).map(name => `
                    <div class="space-y-2">
                        <div class="flex justify-between text-[9px] font-black uppercase tracking-widest">
                            <span class="text-slate-300">${name}</span>
                            <span id="apy-${name.replace(' ', '')}" class="text-sky-500">0.00% APY</span>
                        </div>
                        <div class="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                            <div id="bar-${name.replace(' ', '')}" class="rebalance-bar h-full accent-gradient" style="width: 0%"></div>
                        </div>
                    </div>
                `).join('');
            }

            Object.entries(market).forEach(([name, data]) => {
                const id = name.replace(' ', '');
                document.getElementById(`bar-${id}`).style.width = data.allocation + '%';
                document.getElementById(`apy-${id}`).innerText = data.apy.toFixed(2) + '% APY';
            });
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)