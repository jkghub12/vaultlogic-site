import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import random
import json

# --- VAULTLOGIC ENGINE KERNEL (Updated with Balance Enforcement) ---
class VaultLogicKernel:
    def __init__(self):
        self.active_deployments = {}
        self.institutional_floor = 10000.0
        # Target Allocations from engine.py
        self.protocols = {
            "Aave V3": {"weight": 0.40, "base_apy": 0.042},
            "Morpho Blue": {"weight": 0.50, "base_apy": 0.051},
            "Aerodrome": {"weight": 0.10, "base_apy": 0.124}
        }

    def get_wallet_balance(self, addr):
        """
        Simulates an on-chain balance check.
        For this simulation: 
        - Addresses starting with '0x1' are whales ($500k+)
        - Others are randomized to demonstrate the 'Rejected' state.
        """
        if addr.startswith("SANDBOX"): return 1000000.0
        # Deterministic 'balance' for testing purposes
        seed = sum(ord(c) for c in addr)
        random.seed(seed)
        return random.uniform(500, 50000)

    def get_market_state(self):
        state = {}
        total_apy = 0
        for name, data in self.protocols.items():
            drift = random.uniform(-0.005, 0.005)
            current_apy = data["base_apy"] + drift
            weight_drift = random.uniform(-0.02, 0.02)
            state[name] = {
                "apy": current_apy * 100,
                "allocation": (data["weight"] + weight_drift) * 100,
                "target": data["weight"] * 100
            }
            total_apy += current_apy * data["weight"]
        return state, total_apy * 100

    def deploy(self, addr, amt, mode):
        # Strict server-side enforcement of the 10k floor
        balance = self.get_wallet_balance(addr)
        if mode == "live" and (amt < self.institutional_floor or balance < self.institutional_floor):
            return f"CRITICAL FAILURE: {addr[:8]} insufficient liquidity. Required: $10,000. Found: ${balance:,.2f}"

        self.active_deployments[addr] = {
            "principal": amt,
            "start_time": datetime.now(),
            "strategy": "INSTITUTIONAL_ALM",
            "mode": mode
        }
        tag = "[SANDBOX]" if mode == "sandbox" else "[LIVE]"
        return f"{tag} ENGINE INITIALIZED: Rebalancing active for {addr[:8]}."

kernel = VaultLogicKernel()
app = FastAPI()
audit_logs = ["VAULTLOGIC V4.3.2: MONITORING NETWORK..."]

class EngineInit(BaseModel):
    address: str
    amount: float
    is_sandbox: bool = False

@app.get("/wallet-check/{address}")
async def check_wallet(address: str):
    balance = kernel.get_wallet_balance(address)
    return {
        "address": address,
        "balance": balance,
        "eligible": balance >= kernel.institutional_floor
    }

@app.get("/stats/{address}")
async def get_stats(address: str):
    stats = None
    if address in kernel.active_deployments:
        data = kernel.active_deployments[address]
        elapsed = (datetime.now() - data['start_time']).total_seconds()
        market_state, net_apy = kernel.get_market_state()
        profit = data['principal'] * (net_apy / 100 / (365 * 24 * 3600)) * elapsed
        stats = {
            "principal": data['principal'], 
            "net_profit": profit,
            "apy": net_apy,
            "market_state": market_state
        }
    return {"stats": stats, "logs": audit_logs}

@app.post("/activate")
async def activate(data: EngineInit):
    mode = "sandbox" if data.is_sandbox else "live"
    msg = kernel.deploy(data.address, data.amount, mode)
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] {msg.upper()}")
    if len(audit_logs) > 30: audit_logs.pop(0)
    
    if "FAILURE" in msg:
        return {"status": "error", "message": "Insufficient Balance"}
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Rebalancing Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body { background: #010204; color: #f8fafc; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .glass { background: rgba(10, 15, 25, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
        .accent-gradient { background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); }
        .error-gradient { background: linear-gradient(135deg, #ef4444 0%, #991b1b 100%); }
        .rebalance-bar { transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1); }
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
    </style>
</head>
<body class="p-6 md:p-12 min-h-screen flex flex-col items-center">

    <!-- Wallet Modal -->
    <div id="walletModal" class="fixed inset-0 z-[600] hidden items-center justify-center bg-black/90 backdrop-blur-sm p-4">
        <div class="glass max-w-md w-full rounded-[2.5rem] p-8 border border-white/10">
            <h3 class="font-black text-lg uppercase italic tracking-tighter text-sky-400 mb-6">Connect Identity</h3>
            <div class="space-y-3">
                <div onclick="connectWith('0x1Whale...')" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-sky-500/30 bg-sky-500/5 hover:bg-sky-500/10 transition-all">
                    <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-white text-[10px]">HIGH</div>
                    <p class="text-[11px] font-black uppercase tracking-widest">Connect Whale Wallet (>$10k)</p>
                </div>
                <div onclick="connectWith('0x9Small...')" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer hover:bg-white/5 transition-all">
                    <div class="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center text-red-500 font-bold text-[10px]">LOW</div>
                    <p class="text-[11px] font-black uppercase tracking-widest text-slate-300">Connect Retail Wallet (<$10k)</p>
                </div>
                <button onclick="closeWallets()" class="w-full mt-4 text-[10px] text-slate-500 uppercase font-black">Cancel</button>
            </div>
        </div>
    </div>

    <header class="max-w-7xl w-full flex justify-between items-center mb-12">
        <div class="flex items-center gap-5">
            <div class="w-14 h-14 accent-gradient rounded-2xl flex items-center justify-center text-white font-black text-3xl italic">V</div>
            <div>
                <h1 class="text-3xl font-black italic uppercase tracking-tighter leading-none">VaultLogic</h1>
                <p class="text-[10px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-1.5">ALM Engine V4.3.2</p>
            </div>
        </div>
        <div id="authGroup">
            <button onclick="openWallets()" class="bg-white text-black px-10 py-4 rounded-2xl font-black text-[12px] uppercase tracking-[0.2em]">Connect</button>
        </div>
        <div id="walletDisplay" class="hidden glass px-6 py-3 rounded-2xl flex items-center gap-5">
            <span id="addrText" class="text-[11px] font-mono font-bold text-slate-300">0x...</span>
            <div class="h-4 w-px bg-white/10"></div>
            <span id="balanceText" class="text-[11px] font-black text-sky-400">$0.00</span>
        </div>
    </header>

    <main class="max-w-7xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 relative">
        <!-- Auth Required Overlay -->
        <div id="blockOverlay" class="absolute inset-0 z-10 flex flex-col items-center pt-32 text-center pointer-events-none">
            <h2 class="text-3xl font-black italic uppercase text-slate-800/40 tracking-tighter">Auth Required</h2>
        </div>

        <!-- Controls -->
        <div class="lg:col-span-4 space-y-6">
            <div id="strategyCard" class="glass p-10 rounded-[2.5rem] opacity-10 blur-sm pointer-events-none transition-all">
                <div class="flex justify-between items-center mb-8">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.5em] text-sky-500">Parameters</h3>
                    <span id="eligibilityBadge" class="text-[9px] font-black uppercase px-2 py-1 rounded bg-red-500/20 text-red-500 hidden">Ineligible</span>
                </div>
                
                <div class="space-y-10">
                    <div>
                        <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-4">
                            <span>Target Principal</span>
                            <span id="amtVal" class="text-sky-400 font-mono text-base font-black">$0</span>
                        </div>
                        <input type="range" id="amtRange" min="0" max="100000" step="1000" value="0" class="w-full accent-sky-500"
                               oninput="updateAmtDisplay(this.value)">
                    </div>
                    <button id="deployBtn" onclick="initKernel()" disabled class="w-full py-6 bg-slate-800 text-slate-500 font-black rounded-3xl text-[11px] uppercase tracking-[0.3em] transition-all">
                        Check Wallet First
                    </button>
                    <p id="floorWarning" class="text-[9px] text-center uppercase font-bold text-slate-600 tracking-widest hidden">Minimum $10,000 required for institutional rebalancing</p>
                </div>
            </div>
        </div>

        <!-- Dashboard -->
        <div id="mainTerminal" class="lg:col-span-8 glass p-10 rounded-[2.5rem] opacity-10 blur-sm pointer-events-none transition-all flex flex-col gap-8">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="p-8 rounded-[2rem] bg-white/[0.02] border border-white/5">
                    <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Vault Balance</p>
                    <h2 id="principalDisplay" class="text-4xl font-black italic tracking-tighter">$0</h2>
                </div>
                <div class="p-8 rounded-[2rem] bg-white/[0.02] border border-white/5">
                    <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Engine Profit</p>
                    <h2 id="liveProfit" class="text-4xl font-black text-emerald-400 italic tracking-tighter tabular-nums">$0.0000</h2>
                </div>
            </div>

            <div class="p-8 rounded-[2rem] bg-white/[0.01] border border-white/5">
                <div class="flex justify-between items-center mb-6">
                    <h4 class="text-[11px] font-black uppercase tracking-[0.3em] text-slate-400">Rebalancing Monitor</h4>
                    <span id="netApyText" class="text-[10px] font-black text-emerald-500">APY: 0.00%</span>
                </div>
                <div id="rebalanceContainer" class="space-y-6"></div>
            </div>

            <div id="logOutput" class="font-mono text-[10px] space-y-2 h-40 overflow-y-auto custom-scroll pr-4 opacity-60"></div>
        </div>
    </main>

    <script>
        let walletAddress = null;
        let walletBalance = 0;
        let isEligible = false;

        function openWallets() { document.getElementById('walletModal').classList.replace('hidden', 'flex'); }
        function closeWallets() { document.getElementById('walletModal').classList.replace('flex', 'hidden'); }

        async function connectWith(addrPrefix) {
            walletAddress = addrPrefix === '0x1Whale...' ? "0x1" + Math.random().toString(16).slice(2,39) : "0x9" + Math.random().toString(16).slice(2,39);
            closeWallets();
            
            // Step 1: Perform balance check against the kernel
            const res = await fetch('/wallet-check/' + walletAddress);
            const data = await res.json();
            
            walletBalance = data.balance;
            isEligible = data.eligible;
            
            onAuthSuccess();
        }

        function onAuthSuccess() {
            document.getElementById('authGroup').classList.add('hidden');
            document.getElementById('blockOverlay').classList.add('hidden');
            document.getElementById('walletDisplay').classList.remove('hidden');
            document.getElementById('addrText').innerText = walletAddress.slice(0,10) + "...";
            document.getElementById('balanceText').innerText = "$" + walletBalance.toLocaleString(undefined, {minimumFractionDigits: 2});
            
            document.getElementById('strategyCard').classList.remove('opacity-10', 'pointer-events-none', 'blur-sm');
            document.getElementById('mainTerminal').classList.remove('opacity-10', 'pointer-events-none', 'blur-sm');
            
            updateEligibilityUI();
            startSync();
        }

        function updateAmtDisplay(val) {
            document.getElementById('amtVal').innerText = '$' + parseInt(val).toLocaleString();
            updateEligibilityUI();
        }

        function updateEligibilityUI() {
            const amount = parseInt(document.getElementById('amtRange').value);
            const btn = document.getElementById('deployBtn');
            const badge = document.getElementById('eligibilityBadge');
            const warning = document.getElementById('floorWarning');

            if (!isEligible || amount < 10000) {
                btn.disabled = true;
                btn.className = "w-full py-6 bg-slate-800 text-slate-500 font-black rounded-3xl text-[11px] uppercase tracking-[0.3em]";
                btn.innerText = !isEligible ? "Insufficient Balance" : "Increase Principal";
                badge.classList.remove('hidden');
                warning.classList.remove('hidden');
            } else {
                btn.disabled = false;
                btn.className = "w-full py-6 accent-gradient text-white font-black rounded-3xl text-[11px] uppercase tracking-[0.3em] shadow-xl shadow-sky-500/20";
                btn.innerText = "Initialize Engine";
                badge.classList.add('hidden');
                warning.classList.add('hidden');
            }
        }

        async function initKernel() {
            const amount = parseFloat(document.getElementById('amtRange').value);
            const btn = document.getElementById('deployBtn');
            
            const res = await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: walletAddress, amount: amount, is_sandbox: false })
            });
            const data = await res.json();
            
            if(data.status === 'success') {
                btn.innerText = "ALGORITHM ENGAGED";
                btn.disabled = true;
                btn.className = "w-full py-6 bg-emerald-500/20 text-emerald-500 font-black rounded-3xl text-[11px] uppercase tracking-[0.3em]";
            }
        }

        function startSync() {
            setInterval(async () => {
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
                        document.getElementById('logOutput').innerHTML = data.logs.map(l => `<div class="mb-1 border-l border-white/10 pl-3 py-1"> ${l.split('] ')[1] || l}</div>`).reverse().join('');
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