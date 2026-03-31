import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3
from engine import kernel # Importing our Kernel logic
import uvicorn
from datetime import datetime

app = FastAPI()

# --- CONFIG ---
BASE_RPC_URL = "https://mainnet.base.org"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

# Global Logs for the UI
audit_logs = ["VaultLogic v2.1-LIVE: System Ready. Waiting for Authentication..."]

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def background_kernel_loop():
    """Ticking the engine every 10 seconds for all active users."""
    while True:
        await asyncio.sleep(10)
        # Check all active deployments for updates
        for addr in list(kernel.active_deployments.keys()):
            msg = kernel.active_deployments[addr].calculate_tick(10)
            if msg: add_log(msg)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str):
    """API for the frontend to poll status and logs."""
    return {
        "stats": kernel.get_stats(address),
        "logs": audit_logs
    }

@app.post("/activate")
async def activate(data: EngineInit):
    """Endpoint to trigger the deployment of a new ALM strategy."""
    # Institutional Check
    if data.amount < 10000:
        add_log(f"CRITICAL REJECTION: ${data.amount:,.2f} is below the Institutional Floor.")
        return {"status": "error", "message": "Below $10k Floor"}

    # Balance Verification (Bypassed for testing if needed)
    # w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
    # ... balance checking logic ...

    msg = kernel.deploy(data.address, data.amount, BASE_RPC_URL)
    add_log(msg)
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def home():
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
        body { background: #020408; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .glass { background: rgba(10, 15, 25, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
        .accent-gradient { background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
    </style>
</head>
<body class="p-4 md:p-10 min-h-screen">
    <!-- Header -->
    <nav class="max-w-7xl mx-auto flex justify-between items-center mb-12">
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 accent-gradient rounded-xl flex items-center justify-center text-white font-black text-xl italic shadow-lg shadow-blue-500/20">V</div>
            <div>
                <h1 class="text-xl font-black italic tracking-tighter uppercase leading-none">VaultLogic</h1>
                <p class="text-[8px] text-slate-500 font-bold uppercase tracking-[0.3em] mt-1">Institutional Autopilot</p>
            </div>
        </div>
        <button id="authBtn" onclick="toggleAuth()" class="bg-white text-black px-6 py-2.5 rounded-lg font-black text-[10px] tracking-widest uppercase hover:bg-slate-200 transition-all shadow-xl shadow-white/5">Authenticate</button>
    </nav>

    <!-- Dashboard -->
    <main id="mainDash" class="max-w-7xl mx-auto opacity-20 pointer-events-none transition-all duration-700">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="glass p-8 rounded-3xl relative overflow-hidden group">
                <div class="absolute top-0 left-0 w-1 h-full bg-sky-500"></div>
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Capital Under Management</p>
                <h2 id="principalDisplay" class="text-5xl font-black italic tracking-tighter">$0</h2>
            </div>
            <div class="glass p-8 rounded-3xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Net Yield (80/20 Split)</p>
                <h2 id="liveProfit" class="text-5xl font-black text-emerald-400 italic tracking-tighter">$0.0000</h2>
            </div>
            <div class="glass p-8 rounded-3xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Kernel Status</p>
                <h2 id="statusLabel" class="text-4xl font-black text-white italic uppercase tracking-tighter">AUTHENTICATED</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <!-- Controls -->
            <div class="lg:col-span-4 glass p-10 rounded-3xl">
                <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-sky-500 mb-8">Deployment Parameters</h3>
                <div class="space-y-10">
                    <div>
                        <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-4">
                            <span>Institutional Allocation</span>
                            <span id="amtVal" class="text-white">$10,000</span>
                        </div>
                        <input type="range" id="amtRange" min="10000" max="500000" step="5000" value="10000" 
                               class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
                               oninput="document.getElementById('amtVal').innerText = '$'+parseInt(this.value).toLocaleString()">
                    </div>

                    <div class="space-y-6 pt-4 border-t border-white/5">
                        <div class="flex justify-between text-[9px] font-black uppercase text-slate-500">
                            <span>Aave V3 Lending</span>
                            <span id="lendingPerc" class="text-sky-400">100%</span>
                        </div>
                        <div class="h-1 bg-slate-900 rounded-full overflow-hidden">
                            <div id="lendingBar" class="h-full bg-sky-500 transition-all duration-1000" style="width: 100%"></div>
                        </div>
                        <div class="flex justify-between text-[9px] font-black uppercase text-slate-500">
                            <span>Aerodrome Liquidity</span>
                            <span id="lpPerc" class="text-indigo-400">0%</span>
                        </div>
                        <div class="h-1 bg-slate-900 rounded-full overflow-hidden">
                            <div id="lpBar" class="h-full bg-indigo-500 transition-all duration-1000" style="width: 0%"></div>
                        </div>
                    </div>

                    <button id="deployBtn" onclick="initKernel()" class="w-full py-5 accent-gradient text-white font-black rounded-2xl text-[11px] uppercase tracking-[0.2em] shadow-xl shadow-blue-500/10 hover:scale-[1.02] active:scale-95 transition-all">
                        Initialize ALM Kernel
                    </button>
                </div>
            </div>

            <!-- Terminal -->
            <div class="lg:col-span-8 glass p-10 rounded-3xl">
                <div class="flex justify-between items-center mb-8 border-b border-white/5 pb-6">
                    <p class="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em]">Real-Time Audit Terminal</p>
                    <div class="flex gap-2">
                        <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                        <span class="text-[9px] font-bold text-emerald-500 uppercase tracking-widest">Live Sync</span>
                    </div>
                </div>
                <div id="logOutput" class="font-mono text-[11px] space-y-3 max-h-[400px] overflow-y-auto pr-4"></div>
            </div>
        </div>
    </main>

    <script>
        let walletAddress = null;
        let syncTimer = null;

        async function toggleAuth() {
            const btn = document.getElementById('authBtn');
            
            if (!walletAddress) {
                if (typeof window.ethereum === 'undefined') {
                    btn.innerText = "NO WALLET DETECTED";
                    return;
                }

                try {
                    btn.innerText = "AUTHENTICATING...";
                    btn.disabled = true;

                    // RESTORED: Request permissions to force pop-up
                    await window.ethereum.request({
                        method: 'wallet_requestPermissions',
                        params: [{ eth_accounts: {} }]
                    });

                    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                    
                    if (accounts.length > 0) {
                        walletAddress = accounts[0];
                        btn.innerText = walletAddress.slice(0,6).toUpperCase() + "..." + walletAddress.slice(-4).toUpperCase();
                        btn.classList.add('bg-slate-800', 'text-white');
                        btn.disabled = false;
                        
                        document.getElementById('mainDash').classList.remove('opacity-20', 'pointer-events-none');
                        startSync();
                    }
                } catch (e) {
                    console.error("Auth Failed", e);
                    btn.innerText = "AUTH FAILED";
                    btn.disabled = false;
                    setTimeout(() => btn.innerText = "AUTHENTICATE", 3000);
                }
            } else {
                location.reload(); // Quick disconnect
            }
        }

        async function initKernel() {
            const amount = document.getElementById('amtRange').value;
            const btn = document.getElementById('deployBtn');
            btn.innerText = "DEPLOYING...";
            btn.disabled = true;

            try {
                const res = await fetch('/activate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ address: walletAddress, amount: parseFloat(amount) })
                });
                const data = await res.json();
                
                if (data.status === "success") {
                    btn.innerText = "KERNEL ACTIVE";
                    btn.classList.replace('accent-gradient', 'bg-emerald-600');
                    document.getElementById('statusLabel').innerText = "SYSTEM ACTIVE";
                    document.getElementById('statusLabel').classList.add('text-emerald-400');
                } else {
                    btn.innerText = data.message.toUpperCase();
                    setTimeout(() => {
                        btn.innerText = "Initialize ALM Kernel";
                        btn.disabled = false;
                    }, 3000);
                }
            } catch (e) {
                btn.innerText = "RPC ERROR";
                btn.disabled = false;
            }
        }

        function startSync() {
            syncTimer = setInterval(async () => {
                if (!walletAddress) return;
                try {
                    const res = await fetch('/stats/' + walletAddress);
                    const data = await res.json();

                    if (data.stats) {
                        document.getElementById('principalDisplay').innerText = '$' + data.stats.principal.toLocaleString();
                        document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 4});
                        document.getElementById('lendingPerc').innerText = data.stats.allocation.Lending + '%';
                        document.getElementById('lendingBar').style.width = data.stats.allocation.Lending + '%';
                        document.getElementById('lpPerc').innerText = data.stats.allocation.Liquidity + '%';
                        document.getElementById('lpBar').style.width = data.stats.allocation.Liquidity + '%';
                    }

                    const logOutput = document.getElementById('logOutput');
                    logOutput.innerHTML = data.logs.map(l => `
                        <div class="p-4 border-l-2 ${l.includes('CRITICAL') ? 'border-red-500 bg-red-500/5' : 'border-slate-800 bg-white/[0.02]'} transition-all">
                            <span class="text-sky-500 font-bold uppercase mr-3">KERNEL:</span>
                            <span class="text-slate-300 uppercase">${l.split('KERNEL: ')[1] || l}</span>
                        </div>
                    `).reverse().join('');
                } catch (e) { console.error("Sync Error", e); }
            }, 3000);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)