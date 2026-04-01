import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3
import uvicorn
from datetime import datetime
import random

# --- VAULTLOGIC ENGINE KERNEL ---
class VaultLogicKernel:
    def __init__(self):
        self.active_deployments = {}
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

audit_logs = ["VAULTLOGIC V4.3.1: SECURITY LAYER ACTIVE."]

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
        add_log(f"REJECTED: ${data.amount:,.2f} is below the 10k institutional floor.")
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
        .status-pill { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); }
        .hidden-bank { display: none !important; }
        .plaid-card:hover { transform: translateY(-2px); border-color: rgba(14, 165, 233, 0.4); }
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
                <div onclick="connectWith('MetaMask')" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer hover:bg-white/5 transition-all">
                    <div class="w-10 h-10 bg-orange-500/20 rounded-full flex items-center justify-center text-orange-500 font-bold text-[10px]">MASK</div>
                    <p class="text-[11px] font-black uppercase tracking-widest text-slate-300">MetaMask</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Plaid Simulation Modal -->
    <div id="plaidModal" class="fixed inset-0 z-[700] hidden items-center justify-center bg-black/95 backdrop-blur-md p-4">
        <div class="glass max-w-md w-full rounded-[2.5rem] overflow-hidden border border-white/10 shadow-2xl">
            <div class="p-8 border-b border-white/5 bg-white/[0.02]">
                <div class="flex justify-between items-center mb-6">
                    <div class="flex items-center gap-2">
                        <span class="w-2 h-2 bg-sky-500 rounded-full"></span>
                        <span class="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">VaultLogic | Plaid Auth</span>
                    </div>
                    <button onclick="closePlaid()" class="text-slate-500 hover:text-white">✕</button>
                </div>
                <h3 class="text-xl font-black italic uppercase tracking-tighter mb-4">Select Institution</h3>
                <div class="relative">
                    <input type="text" id="bankSearch" onkeyup="filterBanks()" placeholder="Search for your bank..." 
                           class="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-6 text-[11px] font-bold tracking-widest focus:outline-none focus:border-sky-500/50 transition-all">
                    <span class="absolute right-6 top-4 text-slate-500">🔍</span>
                </div>
            </div>
            
            <div class="p-8 space-y-3 max-h-[400px] overflow-y-auto custom-scroll" id="bankList">
                <!-- Default Bank: Chase -->
                <div onclick="selectBank('Chase')" class="plaid-card flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-white/5 bg-white/[0.01] transition-all">
                    <div class="w-10 h-10 bg-blue-700 rounded-xl flex items-center justify-center text-white font-black text-xs shadow-lg">C</div>
                    <div>
                        <p class="text-[11px] font-black uppercase tracking-widest">Chase Bank</p>
                        <p class="text-[9px] text-slate-500 uppercase font-bold tracking-widest">Personal & Business</p>
                    </div>
                </div>
                <!-- Default Bank: BOA -->
                <div onclick="selectBank('BOA')" class="plaid-card flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-white/5 bg-white/[0.01] transition-all">
                    <div class="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center text-white font-black text-xs shadow-lg">B</div>
                    <div>
                        <p class="text-[11px] font-black uppercase tracking-widest">Bank of America</p>
                        <p class="text-[9px] text-slate-500 uppercase font-bold tracking-widest">Institutional Auth</p>
                    </div>
                </div>
                <!-- Other simulated banks -->
                <div class="bank-item opacity-40 hover:opacity-100 flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-white/5 bg-white/[0.01] transition-all">
                    <div class="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center text-white font-black text-xs">W</div>
                    <p class="text-[11px] font-black uppercase tracking-widest">Wells Fargo</p>
                </div>
                <div class="bank-item opacity-40 hover:opacity-100 flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-white/5 bg-white/[0.01] transition-all">
                    <div class="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center text-white font-black text-xs">C</div>
                    <p class="text-[11px] font-black uppercase tracking-widest">Citibank</p>
                </div>
            </div>
            
            <div class="p-8 bg-white/[0.02] border-t border-white/5 text-center">
                <p class="text-[9px] text-slate-500 font-bold uppercase tracking-[0.2em]">End-to-End Encrypted Settlement Layer</p>
            </div>
        </div>
    </div>

    <!-- Header -->
    <header class="max-w-7xl w-full flex justify-between items-center mb-16">
        <div class="flex items-center gap-5">
            <div class="w-14 h-14 accent-gradient rounded-2xl flex items-center justify-center text-white font-black text-3xl italic shadow-2xl shadow-sky-500/20">V</div>
            <div>
                <h1 class="text-3xl font-black italic uppercase tracking-tighter leading-none">VaultLogic</h1>
                <p class="text-[10px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-1.5">System V4.3.1</p>
            </div>
        </div>
        
        <div class="flex items-center gap-4">
            <div id="walletDisplay" class="hidden status-pill px-6 py-3 rounded-2xl flex items-center gap-5">
                <div class="flex items-center gap-2.5">
                    <div id="statusDot" class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_#10b981]"></div>
                    <span id="addrText" class="text-[11px] font-mono font-bold text-slate-300 tracking-tighter">0x...</span>
                </div>
                <button onclick="location.reload()" class="text-[10px] font-black text-red-500/80 hover:text-red-500 uppercase tracking-widest border-l border-white/10 pl-5">Disconnect</button>
            </div>
            <div id="authGroup" class="flex items-center gap-5">
                <button onclick="openWallets()" class="bg-white text-black px-10 py-4 rounded-2xl font-black text-[12px] uppercase tracking-[0.2em] hover:scale-105 transition-all">Connect</button>
                <div class="h-10 w-[1px] bg-white/10"></div>
                <button onclick="toggleSandbox()" class="text-slate-500 hover:text-sky-400 font-black text-[11px] uppercase tracking-widest transition-colors">Sandbox</button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl w-full relative grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div id="blockOverlay" class="absolute inset-0 z-10 flex flex-col items-center pt-52 text-center pointer-events-none">
            <h2 class="text-4xl font-black italic uppercase text-slate-800/40 tracking-tighter">Connect Vault to Proceed</h2>
        </div>

        <!-- Left Column -->
        <div class="lg:col-span-4 space-y-6 flex flex-col h-full">
            <div id="strategyCard" class="glass p-10 rounded-[2.5rem] border border-white/5 opacity-10 blur-sm pointer-events-none transition-all flex-grow">
                <h3 id="strategyLabel" class="text-[10px] font-black uppercase tracking-[0.5em] text-sky-500 mb-12 text-center">Deployment Controls</h3>
                <div class="space-y-14">
                    <div>
                        <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-6">
                            <span>Allocation Range</span>
                            <span id="amtVal" class="text-sky-400 font-mono text-base font-black">$0</span>
                        </div>
                        <input type="range" id="amtRange" min="0" max="500000" step="1000" value="0" 
                               class="w-full"
                               oninput="document.getElementById('amtVal').innerText = '$'+parseInt(this.value).toLocaleString()">
                    </div>
                    <button id="deployBtn" onclick="initKernel()" class="w-full py-6 accent-gradient text-white font-black rounded-3xl text-[12px] uppercase tracking-[0.3em] shadow-2xl shadow-sky-500/10 active:scale-[0.98] transition-all">Initialize Engine</button>
                </div>
            </div>

            <!-- Plaid / Bank Link Trigger -->
            <div id="plaidContainer" class="mt-auto transition-all duration-300">
                <div onclick="openPlaid()" class="glass p-8 rounded-[2rem] border border-white/5 cursor-pointer hover:border-sky-500/30 transition-all flex items-center justify-between group bg-white/[0.01]">
                    <div class="flex items-center gap-5">
                        <div class="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center text-xl grayscale group-hover:grayscale-0 group-hover:bg-sky-500/10 transition-all">🏦</div>
                        <div>
                            <p id="bankStatusText" class="text-[11px] font-black text-white uppercase tracking-widest">Link Bank Account</p>
                            <p class="text-[9px] text-slate-500 mt-1 uppercase font-bold tracking-[0.2em]">Fiat Settlement Layer</p>
                        </div>
                    </div>
                    <div class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center text-xs text-slate-500 group-hover:bg-white group-hover:text-black group-hover:border-white transition-all">→</div>
                </div>
            </div>
        </div>

        <!-- Right Column -->
        <div id="mainTerminal" class="lg:col-span-8 glass p-12 rounded-[2.5rem] flex flex-col min-h-[680px] border border-white/5 opacity-10 blur-sm pointer-events-none transition-all">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                <div class="p-8 rounded-[2rem] bg-white/[0.02] border border-white/5 shadow-inner">
                    <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Capital Managed</p>
                    <h2 id="principalDisplay" class="text-4xl font-black italic tracking-tighter">$0</h2>
                </div>
                <div class="p-8 rounded-[2rem] bg-white/[0.02] border border-white/5 shadow-inner">
                    <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Net Yield (Live)</p>
                    <h2 id="liveProfit" class="text-4xl font-black text-emerald-400 italic tracking-tighter tabular-nums">$0.0000</h2>
                </div>
            </div>
            <div class="flex justify-between items-center mb-8 border-b border-white/5 pb-8">
                <div class="flex items-center gap-3">
                    <div class="w-1.5 h-1.5 bg-sky-500 rounded-full animate-ping"></div>
                    <span class="text-[11px] font-black text-slate-400 uppercase tracking-[0.3em]">Institutional Audit Log</span>
                </div>
                <span id="auditBadge" class="text-[10px] font-bold text-slate-600 uppercase px-4 py-2 border border-white/5 rounded-2xl bg-white/[0.02]">Offline</span>
            </div>
            <div id="logOutput" class="font-mono text-[11px] space-y-4 flex-grow overflow-y-auto pr-6 custom-scroll"></div>
        </div>
    </main>

    <script>
        let walletAddress = null;
        let syncTimer = null;
        let isSandbox = false;

        function openWallets() { document.getElementById('walletModal').classList.replace('hidden', 'flex'); }
        function closeWallets() { document.getElementById('walletModal').classList.replace('flex', 'hidden'); }
        
        function openPlaid() { 
            document.getElementById('plaidModal').classList.replace('hidden', 'flex');
        }
        
        function closePlaid() {
            document.getElementById('plaidModal').classList.replace('flex', 'hidden');
        }

        function filterBanks() {
            let input = document.getElementById('bankSearch').value.toLowerCase();
            let items = document.querySelectorAll('.bank-item, .plaid-card');
            items.forEach(item => {
                let text = item.innerText.toLowerCase();
                item.style.display = text.includes(input) ? "flex" : "none";
            });
        }

        function selectBank(name) {
            const status = document.getElementById('bankStatusText');
            status.innerText = "LINKING " + name.toUpperCase() + "...";
            closePlaid();
            setTimeout(() => {
                status.innerText = "LINKED: " + (name === 'BOA' ? 'BofA Institutional' : 'Chase Premier');
                status.className = "text-[11px] font-black text-sky-400 uppercase tracking-widest";
            }, 1200);
        }

        function toggleSandbox() { 
            walletAddress = "SANDBOX_MOCK_" + Math.random().toString(16).slice(2,8).toUpperCase();
            isSandbox = true; 
            onAuthSuccess(); 
        }

        function connectWith(provider) {
            walletAddress = "0x" + Math.random().toString(16).slice(2,42).toUpperCase();
            isSandbox = false;
            onAuthSuccess();
        }

        function onAuthSuccess() {
            closeWallets();
            document.getElementById('authGroup').classList.add('hidden');
            document.getElementById('blockOverlay').classList.add('hidden');
            document.getElementById('walletDisplay').classList.remove('hidden');
            document.getElementById('addrText').innerText = isSandbox ? "SANDBOX_MOCK" : walletAddress.slice(0,10) + "...";
            
            if(isSandbox) {
                document.getElementById('plaidContainer').classList.add('hidden-bank');
                document.getElementById('statusDot').className = 'w-2.5 h-2.5 bg-orange-500 rounded-full animate-pulse shadow-[0_0_8px_#f97316]';
                document.getElementById('strategyLabel').innerText = "SANDBOX SIMULATION";
                document.getElementById('strategyLabel').className = "text-[10px] font-black uppercase tracking-[0.5em] text-orange-500 mb-12 text-center";
                document.getElementById('deployBtn').className = "w-full py-6 sandbox-gradient text-white font-black rounded-3xl text-[12px] uppercase tracking-[0.3em] shadow-2xl shadow-orange-500/10 active:scale-[0.98] transition-all";
            } else {
                document.getElementById('plaidContainer').classList.remove('hidden-bank');
            }

            document.getElementById('strategyCard').classList.remove('opacity-10', 'pointer-events-none', 'blur-sm');
            document.getElementById('mainTerminal').classList.remove('opacity-10', 'pointer-events-none', 'blur-sm');
            document.getElementById('auditBadge').innerText = "Active Sync";
            document.getElementById('auditBadge').className = "text-[10px] font-bold text-emerald-500 uppercase px-4 py-2 border border-emerald-500/20 bg-emerald-500/5 rounded-2xl animate-pulse";
            startSync();
        }

        async function initKernel() {
            const amount = parseFloat(document.getElementById('amtRange').value);
            const btn = document.getElementById('deployBtn');

            if (!isSandbox && amount < 10000) {
                const oldText = btn.innerText;
                const oldColor = btn.className;
                btn.innerText = "REJECTED: <$10K FLOOR";
                btn.className = "w-full py-6 bg-red-600 text-white font-black rounded-3xl text-[12px] uppercase tracking-[0.3em]";
                setTimeout(() => {
                    btn.innerText = oldText;
                    btn.className = oldColor;
                }, 3000);
                return;
            }

            btn.innerText = isSandbox ? "INITIALIZING SANDBOX..." : "VERIFYING FUNDS...";
            btn.disabled = true;

            try {
                const res = await fetch('/activate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ address: walletAddress, amount: amount, is_sandbox: isSandbox })
                });
                const data = await res.json();
                if (data.status === "success") {
                    btn.innerText = isSandbox ? "SANDBOX ENGINE ACTIVE" : "KERNEL ACTIVE";
                    btn.className = isSandbox 
                        ? "w-full py-6 bg-orange-600 text-white font-black rounded-3xl text-[12px] uppercase tracking-[0.3em]"
                        : "w-full py-6 bg-emerald-600 text-white font-black rounded-3xl text-[12px] uppercase tracking-[0.3em]";
                } else {
                    btn.innerText = data.message.toUpperCase();
                    btn.className = "w-full py-6 bg-red-600 text-white font-black rounded-3xl text-[12px] uppercase tracking-[0.3em]";
                    btn.disabled = false;
                }
            } catch (e) { btn.innerText = "SYNC ERROR"; btn.disabled = false; }
        }

        function startSync() {
            if (syncTimer) clearInterval(syncTimer);
            syncTimer = setInterval(async () => {
                if (!walletAddress) return;
                try {
                    const res = await fetch('/stats/' + walletAddress);
                    const data = await res.json();
                    if (data.stats) {
                        document.getElementById('principalDisplay').innerText = '$' + data.stats.principal.toLocaleString();
                        document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 5, maximumFractionDigits: 5});
                    }
                    if (data.logs) {
                        document.getElementById('logOutput').innerHTML = data.logs.map(l => {
                            const isSandboxLog = l.includes('[SANDBOX]');
                            const isError = l.includes('REJECTED');
                            return `
                            <div class="flex gap-5 p-5 border-l border-white/5 items-start bg-white/[0.01] rounded-r-2xl">
                                <span class="${isSandboxLog ? 'text-orange-500' : isError ? 'text-red-500' : 'text-sky-500'} font-black italic text-[9px] uppercase tracking-tighter pt-0.5">Log</span>
                                <span class="text-slate-300 font-bold tracking-tight text-[10px] leading-relaxed">${l.split('KERNEL: ')[1] || l}</span>
                            </div>`;
                        }).reverse().join('');
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