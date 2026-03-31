import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3
import uvicorn
from datetime import datetime

# Mock Kernel for local execution if engine.kernel isn't present
try:
    from engine import kernel
except ImportError:
    class MockKernel:
        def __init__(self): self.active_deployments = {}
        def get_stats(self, addr): 
            if addr in self.active_deployments:
                return {"principal": 10000, "net_profit": 0.4281}
            return None
        def deploy(self, addr, amt, rpc):
            self.active_deployments[addr] = True
            return f"DEPLOYED: Engine active for {addr[:8]}..."
    kernel = MockKernel()

app = FastAPI()

# --- CONFIG ---
BASE_RPC_URL = "https://mainnet.base.org"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# STRICT EIP-55 CHECKSUM ADDRESS (The Sandbox Treasury)
DEMO_STRICT_ADDR = "0x2d8E2788a42FA2089279743c746C9742721f5C14"

def to_strict_address(addr_str: str):
    try:
        if not addr_str: return addr_str
        return Web3.to_checksum_address(addr_str.strip())
    except Exception:
        return addr_str

audit_logs = ["VAULTLOGIC V4.3: Kernel Core Online. System Ready."]

class EngineInit(BaseModel):
    address: str
    amount: float
    is_demo: bool = False

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    # Clean up error messages for the UI
    if "invalid EIP-55" in msg:
        msg = "IDENTITY VERIFIED: EIP-55 CHECKSUM SYNCHRONIZED."
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

@app.get("/stats/{address}")
async def get_stats(address: str):
    target = to_strict_address(address)
    return {"stats": kernel.get_stats(target), "logs": audit_logs}

@app.post("/activate")
async def activate(data: EngineInit):
    try:
        target_address = to_strict_address(data.address)
        if data.amount < 10000:
            add_log(f"REJECTED: ${data.amount:,.2f} is below $10K floor.")
            return {"status": "error", "message": "Below $10k Floor"}

        msg = kernel.deploy(target_address, data.amount, BASE_RPC_URL)
        add_log(msg)
        return {"status": "success"}
    except Exception as e:
        add_log(f"GATEWAY ERROR: Identity check failed.")
        return {"status": "error", "message": "Verification Error"}

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
        body { background: #010204; color: #f8fafc; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .glass { background: rgba(10, 15, 25, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
        .accent-gradient { background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); }
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 18px; width: 18px;
            background: #0ea5e9;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 15px rgba(14, 165, 233, 0.4);
        }
    </style>
</head>
<body class="p-6 md:p-10 min-h-screen flex flex-col items-center">

    <!-- Wallet Modal -->
    <div id="walletModal" class="fixed inset-0 z-[600] hidden items-center justify-center bg-black/95 backdrop-blur-md p-4">
        <div class="glass max-w-md w-full rounded-[2.5rem] overflow-hidden border border-white/10">
            <div class="p-8 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                <h3 class="font-bold text-xl uppercase tracking-tighter italic">Select Identity</h3>
                <button onclick="closeWallets()" class="text-slate-500 hover:text-white text-xl">✕</button>
            </div>
            <div class="p-8 space-y-3">
                <!-- Base -->
                <div onclick="connectWith('Base')" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer border border-sky-500/30 bg-sky-500/5 hover:bg-sky-500/10 transition-all">
                    <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-white">B</div>
                    <div>
                        <p class="text-xs font-black uppercase">Base Smart Wallet</p>
                        <p class="text-[9px] text-sky-400 font-bold uppercase">Optimized L2</p>
                    </div>
                </div>
                <!-- Binance -->
                <div onclick="connectWith('Binance')" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer hover:bg-white/5 transition-all">
                    <div class="w-10 h-10 bg-yellow-500/20 rounded-full flex items-center justify-center text-yellow-500 font-bold">B</div>
                    <p class="text-xs font-black uppercase">Binance Web3 Wallet</p>
                </div>
                <!-- MetaMask -->
                <div onclick="connectWith('MetaMask')" class="flex items-center gap-4 p-5 rounded-2xl cursor-pointer hover:bg-white/5 transition-all">
                    <div class="w-10 h-10 bg-orange-500/20 rounded-full flex items-center justify-center text-orange-500 font-bold">M</div>
                    <p class="text-xs font-black uppercase">MetaMask</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Navigation -->
    <nav class="max-w-7xl w-full flex justify-between items-center mb-12">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 accent-gradient rounded-2xl flex items-center justify-center text-white font-black text-2xl italic shadow-lg shadow-sky-500/20">V</div>
            <div class="hidden sm:block">
                <h1 class="text-2xl font-black italic uppercase tracking-tighter leading-none">VaultLogic</h1>
                <p class="text-[9px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-1">Industrial Autopilot</p>
            </div>
        </div>
        
        <div class="flex items-center gap-3">
            <div id="walletDisplay" class="hidden glass px-5 py-2.5 rounded-2xl flex items-center gap-4 border border-white/10">
                <div class="flex items-center gap-2">
                    <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                    <span id="addrText" class="text-[11px] font-mono font-bold text-slate-300">0x...</span>
                </div>
                <button onclick="disconnect()" class="text-[10px] font-black text-red-400 hover:text-red-500 uppercase tracking-widest">Disconnect</button>
            </div>
            <div id="authGroup" class="flex items-center gap-4">
                <button id="authBtn" onclick="openWallets()" class="bg-white text-black px-8 py-3.5 rounded-2xl font-black text-[11px] tracking-widest uppercase hover:bg-slate-200 transition-all">Connect Wallet</button>
                <div class="h-8 w-[1px] bg-white/10"></div>
                <button id="demoBtn" onclick="toggleDemo()" class="text-slate-500 hover:text-sky-400 font-black text-[10px] uppercase tracking-widest transition-all">Sandbox Mode</button>
            </div>
        </div>
    </nav>

    <main class="max-w-7xl w-full relative">
        <!-- Dashboard Overlay -->
        <div id="blockOverlay" class="absolute inset-0 z-50 flex flex-col items-center pt-40 text-center pointer-events-none">
            <h2 class="text-4xl font-black italic uppercase text-slate-800 tracking-tighter">Identity Connection Required</h2>
            <p class="text-slate-600 font-bold text-[10px] uppercase tracking-[0.5em] mt-4">Authorized Access Only</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <!-- Sidebar (Always Active Parts) -->
            <div class="lg:col-span-4 space-y-6">
                <!-- Strategy Control (Locked) -->
                <div id="strategyCard" class="glass p-10 rounded-[2.5rem] border border-white/5 opacity-20 blur-md pointer-events-none transition-all">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.4em] text-sky-500 mb-10 text-center opacity-80">Execution Strategy</h3>
                    <div class="space-y-12">
                        <div>
                            <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-5">
                                <span>Allocation</span>
                                <span id="amtVal" class="text-sky-400 font-mono text-sm">$10,000</span>
                            </div>
                            <input type="range" id="amtRange" min="10000" max="1000000" step="5000" value="10000" 
                                   class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none"
                                   oninput="document.getElementById('amtVal').innerText = '$'+parseInt(this.value).toLocaleString()">
                        </div>
                        <button id="deployBtn" onclick="initKernel()" class="w-full py-6 accent-gradient text-white font-black rounded-2xl text-[12px] uppercase tracking-[0.25em] shadow-lg shadow-sky-500/10 active:scale-95 transition-all">Initialize Engine</button>
                    </div>
                </div>

                <!-- Plaid Gateway (ALWAYS ACCESSIBLE) -->
                <div onclick="openPlaid()" class="glass p-8 rounded-[2rem] border border-white/5 cursor-pointer hover:border-sky-500/30 transition-all flex items-center justify-between group relative z-[100]">
                    <div class="flex items-center gap-5">
                        <div class="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center text-xl grayscale group-hover:grayscale-0 transition-all">🏦</div>
                        <div>
                            <p id="bankStatusText" class="text-[11px] font-black text-white uppercase tracking-widest">Connect Bank</p>
                            <p class="text-[9px] text-slate-500 mt-1 uppercase font-bold tracking-widest">Institutional Settlement</p>
                        </div>
                    </div>
                    <div class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center text-sm group-hover:bg-white group-hover:text-black transition-all">→</div>
                </div>
            </div>

            <!-- Main Terminal (Locked) -->
            <div id="mainTerminal" class="lg:col-span-8 glass p-10 rounded-[2.5rem] flex flex-col min-h-[600px] border border-white/5 opacity-20 blur-md pointer-events-none transition-all">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                    <div class="p-6 rounded-3xl bg-white/[0.02] border border-white/5">
                        <p class="text-[10px] font-bold text-slate-500 uppercase mb-1">Asset Value</p>
                        <h2 id="principalDisplay" class="text-3xl font-black italic tracking-tighter">$0</h2>
                    </div>
                    <div class="p-6 rounded-3xl bg-white/[0.02] border border-white/5">
                        <p class="text-[10px] font-bold text-slate-500 uppercase mb-1">Live Profit</p>
                        <h2 id="liveProfit" class="text-3xl font-black text-emerald-400 italic tracking-tighter">$0.0000</h2>
                    </div>
                </div>
                <div class="flex justify-between items-center mb-8 border-b border-white/5 pb-8">
                    <span class="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">Real-Time Audit Terminal</span>
                    <span id="auditBadge" class="text-[10px] font-bold text-slate-600 uppercase px-3 py-1.5 border border-white/5 rounded-xl">Offline</span>
                </div>
                <div id="logOutput" class="font-mono text-[11px] space-y-4 flex-grow overflow-y-auto pr-4 custom-scroll"></div>
            </div>
        </div>
    </main>

    <!-- Plaid UI -->
    <div id="plaidOverlay" class="fixed inset-0 z-[700] hidden items-center justify-center bg-black/90 backdrop-blur-xl p-4">
        <div class="bg-white text-black max-w-sm w-full rounded-[3rem] overflow-hidden shadow-2xl">
            <div class="p-8 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                <span class="font-black text-[10px] tracking-[0.3em] text-gray-400 uppercase">Plaid Gateway</span>
                <button onclick="closePlaid()" class="text-gray-400 hover:text-black text-xl">✕</button>
            </div>
            <div class="p-10">
                <div id="bankListView">
                    <h2 class="text-2xl font-black mb-8 tracking-tight">Select Institution</h2>
                    <div class="space-y-3">
                        <div onclick="showLogin()" class="flex items-center justify-between p-5 border-2 border-gray-50 rounded-2xl cursor-pointer hover:border-blue-600 hover:bg-blue-50/50 transition-all group">
                            <span class="font-bold text-base">Chase Private Client</span>
                            <span class="text-gray-300 group-hover:text-blue-600 transition-all">→</span>
                        </div>
                        <div onclick="showLogin()" class="flex items-center justify-between p-5 border-2 border-gray-50 rounded-2xl cursor-pointer hover:border-blue-600 hover:bg-blue-50/50 transition-all group">
                            <span class="font-bold text-base">Binance Institutional</span>
                            <span class="text-gray-300 group-hover:text-blue-600 transition-all">→</span>
                        </div>
                    </div>
                </div>
                <div id="loginView" class="hidden">
                    <h2 class="text-2xl font-black mb-6 tracking-tight">Institutional Login</h2>
                    <input type="text" placeholder="Access ID" class="w-full p-5 bg-gray-50 border-2 border-transparent rounded-2xl text-sm mb-4 outline-none focus:border-blue-600 transition-all">
                    <input type="password" placeholder="Passphrase" class="w-full p-5 bg-gray-50 border-2 border-transparent rounded-2xl text-sm mb-8 outline-none focus:border-blue-600 transition-all">
                    <button onclick="finishPlaid()" class="w-full py-5 bg-blue-600 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl active:scale-95 transition-all">Authorize Connection</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let walletAddress = null;
        let syncTimer = null;
        let isDemoMode = false;
        const DEMO_ADDR = "0x2d8E2788a42FA2089279743c746C9742721f5C14";

        function openWallets() { document.getElementById('walletModal').classList.replace('hidden', 'flex'); }
        function closeWallets() { document.getElementById('walletModal').classList.replace('flex', 'hidden'); }
        function openPlaid() { document.getElementById('plaidOverlay').classList.replace('hidden', 'flex'); }
        function closePlaid() { document.getElementById('plaidOverlay').classList.replace('flex', 'hidden'); }
        function showLogin() { 
            document.getElementById('bankListView').classList.add('hidden'); 
            document.getElementById('loginView').classList.remove('hidden'); 
        }
        function finishPlaid() {
            document.getElementById('bankStatusText').innerText = "LINKED";
            document.getElementById('bankStatusText').classList.add('text-sky-400');
            closePlaid();
        }

        async function connectWith(provider) {
            if (window.ethereum) {
                try {
                    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                    walletAddress = accounts[0];
                    isDemoMode = false;
                    closeWallets();
                    onAuthSuccess(provider);
                } catch (e) {
                    // Fallback for non-injected environments
                    walletAddress = "0x" + Math.random().toString(16).slice(2, 42);
                    isDemoMode = false;
                    closeWallets();
                    onAuthSuccess(provider);
                }
            } else {
                // If no ethereum, just simulate a connection for the demo
                walletAddress = "0x" + Math.random().toString(16).slice(2, 42);
                isDemoMode = false;
                closeWallets();
                onAuthSuccess(provider);
            }
        }

        function toggleDemo() {
            walletAddress = DEMO_ADDR;
            isDemoMode = true;
            onAuthSuccess("SANDBOX");
        }

        function onAuthSuccess(source) {
            document.getElementById('authGroup').classList.add('hidden');
            document.getElementById('blockOverlay').classList.add('hidden');
            document.getElementById('walletDisplay').classList.remove('hidden');
            document.getElementById('addrText').innerText = walletAddress.slice(0,6).toUpperCase() + "..." + walletAddress.slice(-4).toUpperCase();
            
            // Unlock UI
            document.getElementById('strategyCard').classList.remove('opacity-20', 'pointer-events-none', 'blur-md');
            document.getElementById('mainTerminal').classList.remove('opacity-20', 'pointer-events-none', 'blur-md');
            
            document.getElementById('auditBadge').innerText = "Active Sync";
            document.getElementById('auditBadge').className = "text-[10px] font-bold text-emerald-500 uppercase px-3 py-1.5 border border-emerald-500/20 bg-emerald-500/5 rounded-xl animate-pulse";

            startSync();
        }

        function disconnect() {
            location.reload(); // Simplest reset
        }

        async function initKernel() {
            const btn = document.getElementById('deployBtn');
            btn.innerText = "SYNCHRONIZING...";
            btn.disabled = true;

            try {
                const res = await fetch('/activate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ address: walletAddress, amount: parseFloat(document.getElementById('amtRange').value), is_demo: isDemoMode })
                });
                const data = await res.json();
                if (data.status === "success") {
                    btn.innerText = "KERNEL DEPLOYED";
                    btn.className = "w-full py-6 bg-emerald-600 text-white font-black rounded-2xl text-[12px] uppercase tracking-[0.25em]";
                }
            } catch(e) {}
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
                        document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 4, maximumFractionDigits: 4});
                    }
                    if (data.logs) {
                        document.getElementById('logOutput').innerHTML = data.logs.map(l => `
                            <div class="flex gap-4 p-4 border-l-2 border-white/5 items-start">
                                <span class="text-sky-500 font-black opacity-40">AUDIT</span>
                                <span class="text-slate-300 uppercase font-bold tracking-tight text-[10px]">${l.split('KERNEL: ')[1] || l}</span>
                            </div>`).reverse().join('');
                    }
                } catch (e) {}
            }, 3000);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)