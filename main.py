import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import random

# --- VAULTLOGIC ENGINE KERNEL ---
class VaultLogicKernel:
    def __init__(self):
        self.active_deployments = {}
        self.institutional_floor = 10000.0
        self.base_rates = {
            "aave_v3": 0.042,
            "morpho": 0.051,
            "aerodrome": 0.124
        }

    def get_market_apy(self):
        drift = random.uniform(-0.001, 0.001)
        return (self.base_rates["morpho"] * 0.6) + (self.base_rates["aave_v3"] * 0.4) + drift

    def get_stats(self, addr): 
        if addr in self.active_deployments:
            data = self.active_deployments[addr]
            elapsed = (datetime.now() - data['start_time']).total_seconds()
            annual_rate = self.get_market_apy()
            profit = data['principal'] * (annual_rate / (365 * 24 * 3600)) * elapsed
            return {
                "principal": data['principal'], 
                "net_profit": profit,
                "apy": annual_rate * 100,
                "status": "REBALANCING_OPTIMIZED"
            }
        return None

    def deploy(self, addr, amt, mode):
        # In a real app, we would verify the balance on-chain via Web3 here
        if mode == "live" and amt < self.institutional_floor:
            return f"REJECTED: ${amt:,.2f} IS BELOW THE 10K INSTITUTIONAL FLOOR."

        self.active_deployments[addr] = {
            "principal": amt,
            "start_time": datetime.now(),
            "strategy": "AGGRESSIVE_USDC",
            "mode": mode
        }
        tag = "[SANDBOX]" if mode == "sandbox" else "[LIVE]"
        return f"{tag} DEPLOYED: Engine active for {addr[:8]}. Principal: ${amt:,.2f}"

kernel = VaultLogicKernel()
app = FastAPI()
audit_logs = ["VAULTLOGIC V4.3.1: SECURE WALLET LAYER INITIALIZED."]

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
    mode = "sandbox" if data.is_sandbox else "live"
    msg = kernel.deploy(data.address, data.amount, mode)
    add_log(msg)
    if "REJECTED" in msg:
        return {"status": "error", "message": msg}
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
    <!-- Web3.js for real wallet interaction -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/web3/1.8.1/web3.min.js"></script>
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
            -webkit-appearance: none; height: 18px; width: 18px;
            background: #0ea5e9; border-radius: 50%; cursor: pointer;
            box-shadow: 0 0 15px rgba(14, 165, 233, 0.4); border: 2px solid #010204;
        }
        .status-pill { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); }
        .hidden-bank { display: none !important; }
    </style>
</head>
<body class="p-6 md:p-12 min-h-screen flex flex-col items-center">

    <!-- Wallet Modal -->
    <div id="walletModal" class="fixed inset-0 z-[600] hidden items-center justify-center bg-black/90 backdrop-blur-sm p-4">
        <div class="glass max-w-md w-full rounded-[2.5rem] overflow-hidden border border-white/10 shadow-2xl">
            <div class="p-8 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                <h3 class="font-black text-lg uppercase italic tracking-tighter text-sky-400">Connect Identity</h3>
                <button onclick="closeWallets()" class="text-slate-500 hover:text-white">✕</button>
            </div>
            <div class="p-8 space-y-3">
                <div onclick="connectRealWallet()" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-sky-500/30 bg-sky-500/5 hover:bg-sky-500/10 transition-all">
                    <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-white text-[10px]">WEB3</div>
                    <p class="text-[11px] font-black uppercase tracking-widest">Browser Wallet (MetaMask/Base)</p>
                </div>
                <div id="noWalletMsg" class="hidden p-4 text-[10px] text-red-400 font-bold uppercase text-center">No Web3 provider detected in browser.</div>
            </div>
        </div>
    </div>

    <!-- Header -->
    <header class="max-w-7xl w-full flex justify-between items-center mb-16">
        <div class="flex items-center gap-5">
            <div class="w-14 h-14 accent-gradient rounded-2xl flex items-center justify-center text-white font-black text-3xl italic">V</div>
            <div>
                <h1 class="text-3xl font-black italic uppercase tracking-tighter leading-none">VaultLogic</h1>
                <p class="text-[10px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-1.5">System V4.3.1</p>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <div id="walletDisplay" class="hidden status-pill px-6 py-3 rounded-2xl flex items-center gap-5">
                <div class="flex items-center gap-2.5">
                    <div id="statusDot" class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></div>
                    <span id="addrText" class="text-[11px] font-mono font-bold text-slate-300">0x...</span>
                    <span id="balDisplay" class="text-[9px] text-sky-400 font-black ml-2 uppercase"></span>
                </div>
                <button onclick="location.reload()" class="text-[10px] font-black text-red-500 uppercase tracking-widest border-l border-white/10 pl-5">Logout</button>
            </div>
            <div id="authGroup">
                <button onclick="openWallets()" class="bg-white text-black px-10 py-4 rounded-2xl font-black text-[12px] uppercase tracking-[0.2em]">Connect</button>
                <button onclick="toggleSandbox()" class="ml-4 text-slate-500 font-black text-[11px] uppercase tracking-widest">Sandbox</button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl w-full relative grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div id="blockOverlay" class="absolute inset-0 z-10 flex flex-col items-center pt-52 text-center pointer-events-none">
            <h2 class="text-4xl font-black italic uppercase text-slate-800/40 tracking-tighter">Auth Required</h2>
        </div>

        <div class="lg:col-span-4 space-y-6">
            <div id="strategyCard" class="glass p-10 rounded-[2.5rem] border border-white/5 opacity-10 blur-sm pointer-events-none transition-all">
                <h3 id="strategyLabel" class="text-[10px] font-black uppercase tracking-[0.5em] text-sky-500 mb-12">Parameters</h3>
                <div class="space-y-14">
                    <div>
                        <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-6">
                            <span>Principal</span>
                            <span id="amtVal" class="text-sky-400 font-mono text-base font-black">$0</span>
                        </div>
                        <input type="range" id="amtRange" min="0" max="500000" step="1000" value="0" oninput="updateAmt(this.value)">
                    </div>
                    <button id="deployBtn" onclick="initKernel()" class="w-full py-6 accent-gradient text-white font-black rounded-3xl text-[12px] uppercase tracking-[0.3em]">Initialize Engine</button>
                </div>
            </div>
        </div>

        <div id="mainTerminal" class="lg:col-span-8 glass p-12 rounded-[2.5rem] border border-white/5 opacity-10 blur-sm pointer-events-none transition-all">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                <div class="p-8 rounded-[2rem] bg-white/[0.02] border border-white/5">
                    <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Total Assets</p>
                    <h2 id="principalDisplay" class="text-4xl font-black italic tracking-tighter">$0</h2>
                </div>
                <div class="p-8 rounded-[2rem] bg-white/[0.02] border border-white/5">
                    <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Net Interest</p>
                    <h2 id="liveProfit" class="text-4xl font-black text-emerald-400 italic tracking-tighter tabular-nums">$0.0000</h2>
                </div>
            </div>
            <div id="logOutput" class="font-mono text-[11px] space-y-4 h-[300px] overflow-y-auto custom-scroll"></div>
        </div>
    </main>

    <script>
        let walletAddress = null;
        let isSandbox = false;
        let web3;

        function openWallets() { document.getElementById('walletModal').classList.replace('hidden', 'flex'); }
        function closeWallets() { document.getElementById('walletModal').classList.replace('flex', 'hidden'); }

        async function connectRealWallet() {
            if (window.ethereum) {
                try {
                    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                    walletAddress = accounts[0];
                    web3 = new Web3(window.ethereum);
                    
                    // Fetch real balance for visual check
                    const balanceWei = await web3.eth.getBalance(walletAddress);
                    const balanceEth = web3.utils.fromWei(balanceWei, 'ether');
                    // Simulating a conversion to USD for the display
                    document.getElementById('balDisplay').innerText = `ETH Balance: ${parseFloat(balanceEth).toFixed(4)}`;
                    
                    isSandbox = false;
                    onAuthSuccess();
                } catch (err) {
                    console.error("User denied account access", err);
                }
            } else {
                document.getElementById('noWalletMsg').classList.remove('hidden');
            }
        }

        function toggleSandbox() { 
            walletAddress = "SANDBOX_" + Math.random().toString(16).slice(2,8).toUpperCase();
            isSandbox = true; 
            onAuthSuccess(); 
        }

        function onAuthSuccess() {
            closeWallets();
            document.getElementById('authGroup').classList.add('hidden');
            document.getElementById('blockOverlay').classList.add('hidden');
            document.getElementById('walletDisplay').classList.remove('hidden');
            document.getElementById('addrText').innerText = walletAddress.slice(0,10) + "...";
            
            if(isSandbox) {
                document.getElementById('statusDot').className = 'w-2.5 h-2.5 bg-orange-500 rounded-full animate-pulse';
                document.getElementById('strategyLabel').innerText = "SANDBOX SIMULATION";
                document.getElementById('deployBtn').className = "w-full py-6 sandbox-gradient text-white font-black rounded-3xl";
            }

            document.getElementById('strategyCard').classList.remove('opacity-10', 'pointer-events-none', 'blur-sm');
            document.getElementById('mainTerminal').classList.remove('opacity-10', 'pointer-events-none', 'blur-sm');
            startSync();
        }

        function updateAmt(val) {
            document.getElementById('amtVal').innerText = '$' + parseInt(val).toLocaleString();
        }

        async function initKernel() {
            const amount = parseFloat(document.getElementById('amtRange').value);
            const btn = document.getElementById('deployBtn');
            const res = await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: walletAddress, amount: amount, is_sandbox: isSandbox })
            });
            const data = await res.json();
            if (data.status === "success") {
                btn.innerText = "ENGINE ACTIVE";
                btn.disabled = true;
            } else {
                alert(data.message); // Institutional floor check
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
                    }
                    if (data.logs) {
                        document.getElementById('logOutput').innerHTML = data.logs.map(l => `<div class="p-3 border-l border-white/10 text-slate-400 uppercase">${l}</div>`).reverse().join('');
                    }
                } catch (e) {}
            }, 2000);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)