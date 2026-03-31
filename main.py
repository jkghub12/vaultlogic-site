import asyncio
import random
import os
import httpx
import uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from eth_utils import to_checksum_address, is_address

app = FastAPI()

# --- INDUSTRIAL KERNEL ENGINE (V3.5 - FIAT BRIDGE ENABLED) ---
class KernelEngine:
    def __init__(self):
        self.active_deployments = {}
        self.current_venue = "AAVE_V3"
        self.base_apy = 0.0582 
        self.venues = ["AAVE_V3", "COMPOUND_V3", "MORPHO_BLUE", "AERODROME_LP"]

    def deploy(self, address, amount, rpc, source="CRYPTO"):
        self.active_deployments[address] = {
            "principal": amount,
            "net_profit": 0.0,
            "start_time": datetime.now(),
            "status": "ACTIVE",
            "venue": self.current_venue,
            "source": source # Track if this is a Bank Bridge or Native Crypto
        }
        source_label = "BANK-TO-USDC BRIDGE" if source == "BANK" else "NATIVE WALLET"
        return f"SUCCESS: [Source: {source_label}] Asset Allocation of ${amount:,.2f} deployed to {address[:10]}."

    def get_stats(self, address):
        return self.active_deployments.get(address)

    def rebalance(self):
        new_venue = random.choice([v for v in self.venues if v != self.current_venue])
        old_venue = self.current_venue
        self.current_venue = new_venue
        for addr in self.active_deployments:
            self.active_deployments[addr]["venue"] = new_venue
        return f"REBALANCING: Yield spike detected. Migrating liquidity from {old_venue} to {new_venue}..."

    def tick(self):
        for addr in self.active_deployments:
            multiplier = 1.15 if random.random() > 0.8 else 1.0
            growth = (self.active_deployments[addr]["principal"] * (self.base_apy / 365 / 24 / 60)) * multiplier
            self.active_deployments[addr]["net_profit"] += growth

kernel = KernelEngine()

# --- CONFIG & GLOBALS ---
PORT = int(os.environ.get("PORT", 8000))
BASE_RPC_URL = "https://mainnet.base.org"
audit_logs = ["VaultLogic v3.5-FIAT-BRIDGE: System online. Plaid-to-USDC API ready."]

class EngineInit(BaseModel):
    address: str
    amount: float
    simulate: bool = False
    source: str = "CRYPTO" # Added source tracking

def safe_checksum(address: str):
    try:
        if address.startswith("vault_"): return address # Handle temp vault IDs
        if is_address(address): return to_checksum_address(address)
        return address
    except Exception: return address

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def background_kernel_loop():
    while True:
        await asyncio.sleep(5)
        kernel.tick()
        if random.random() > 0.90:
            event = kernel.rebalance()
            if event: add_log(event)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str):
    stats = kernel.get_stats(safe_checksum(address))
    return {"stats": stats, "logs": audit_logs}

@app.post("/activate")
async def activate_deployment(data: EngineInit):
    addr = safe_checksum(data.address)
    msg = kernel.deploy(addr, data.amount, BASE_RPC_URL, data.source)
    add_log(msg)
    return {"status": "success"}

@app.post("/reset/{address}")
async def reset_deployment(address: str):
    addr = safe_checksum(address)
    if addr in kernel.active_deployments:
        del kernel.active_deployments[addr]
        add_log(f"SESSION_CLOSED: Assets withdrawn from {addr[:12]}...")
    return {"status": "reset"}

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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
        body { background-color: #040608; color: #e2e8f0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(10, 15, 25, 0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.03); }
        .btn-glow:hover { box-shadow: 0 0 20px rgba(14, 165, 233, 0.4); }
    </style>
</head>
<body class="min-h-screen p-4 md:p-10">
    <nav class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-16 gap-8">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-white rounded-xl flex items-center justify-center"><i class="fas fa-shield-halved text-black text-2xl"></i></div>
            <div>
                <h1 class="text-3xl font-bold tracking-tighter uppercase italic">VaultLogic</h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-[0.4em] font-black">Industrial Yield Engine</p>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <div id="connectionStatus" class="flex items-center gap-3 glass-panel px-5 py-2.5 rounded-full border-white/5">
                <span id="dot" class="w-2 h-2 bg-slate-500 rounded-full"></span>
                <span id="statusText" class="text-[10px] font-black text-slate-500 tracking-widest uppercase">Locked</span>
            </div>
            <div class="flex gap-2">
                <button onclick="connectWallet()" id="walletBtn" class="bg-white text-black hover:bg-sky-500 hover:text-white px-6 py-3 rounded-lg font-black transition-all uppercase text-[10px] tracking-widest">Connect Wallet</button>
                <button onclick="connectBank()" id="bankBtn" class="bg-emerald-600 text-white hover:bg-emerald-400 px-6 py-3 rounded-lg font-black transition-all uppercase text-[10px] tracking-widest">Link Bank Account</button>
            </div>
        </div>
    </nav>

    <main id="dashboard" class="max-w-7xl mx-auto opacity-20 pointer-events-none transition-all duration-700">
        <!-- MODAL OVERLAY FOR BANK LINKING -->
        <div id="bankModal" class="fixed inset-0 bg-black/90 z-50 hidden flex items-center justify-center p-6">
            <div class="glass-panel max-w-md w-full p-10 rounded-[2.5rem] border-emerald-500/30 text-center">
                <i class="fas fa-university text-4xl text-emerald-500 mb-6"></i>
                <h2 class="text-2xl font-bold mb-2">Plaudit Bridge</h2>
                <p class="text-slate-400 text-sm mb-8">Connecting to your primary checking account. Converting balance to USDC via VaultLogic Liquidity Wrapper...</p>
                <div class="flex flex-col gap-4">
                    <button onclick="confirmBankLink()" class="w-full py-4 bg-emerald-600 rounded-xl font-black text-[11px] tracking-widest">AUTHORIZE BANK TRANSFER</button>
                    <button onclick="document.getElementById('bankModal').classList.add('hidden')" class="text-slate-500 text-[10px] uppercase font-black">Cancel</button>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-sky-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Managed Assets</p>
                <h2 class="text-4xl font-bold italic mono" id="principalDisplay">$0.00</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-emerald-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Net Realized Gain</p>
                <h2 class="text-4xl font-bold text-emerald-400 italic mono" id="liveProfit">$0.0000</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-purple-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Active Venue</p>
                <h2 class="text-2xl font-bold text-purple-400 italic mono uppercase tracking-tighter mt-2" id="venueDisplay">SCANNING...</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div class="lg:col-span-4 space-y-6">
                <div class="glass-panel p-10 rounded-[2.5rem]">
                    <div class="flex justify-between items-center mb-8">
                        <h3 class="text-[11px] font-black uppercase tracking-[0.3em] text-sky-400">Vault Controller</h3>
                        <span id="sourceTag" class="text-[9px] bg-slate-800 px-3 py-1 rounded-full font-black text-slate-400 uppercase tracking-widest">CRYPTO NATIVE</span>
                    </div>
                    <div class="mb-10">
                        <div class="flex justify-between text-[10px] mb-4 font-black uppercase tracking-widest">
                            <span class="text-slate-400">Target Allocation</span>
                            <span class="text-white" id="amountDisplay">$50,000</span>
                        </div>
                        <input type="range" min="1000" max="500000" step="1000" value="50000" id="depositInput"
                               oninput="document.getElementById('amountDisplay').innerText = '$' + parseInt(this.value).toLocaleString()"
                               class="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer">
                    </div>
                    <button id="executeBtn" onclick="executeDeployment()" class="w-full py-5 bg-sky-600 text-white font-black rounded-xl hover:bg-white hover:text-black transition-all uppercase tracking-widest text-[10px] btn-glow">
                        START INDUSTRIAL YIELD
                    </button>
                    <p id="txStatus" class="hidden text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl"></p>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel rounded-[2.5rem] p-10 min-h-[500px] flex flex-col">
                    <div class="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
                        <h3 class="font-black uppercase tracking-widest text-[10px] text-slate-500">Kernel Audit Stream</h3>
                        <div class="flex items-center gap-3"><span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span></div>
                    </div>
                    <div id="logOutput" class="flex-grow mono text-[11px] space-y-3 overflow-y-auto max-h-[400px] custom-scrollbar"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let userAddress = null;
        let loginSource = "CRYPTO"; 
        let syncInterval = null;

        function connectBank() {
            document.getElementById('bankModal').classList.remove('hidden');
        }

        async function confirmBankLink() {
            // Simulate Plaid Success -> Temporary Vault ID generated
            userAddress = "vault_temp_" + Math.random().toString(36).substring(7);
            loginSource = "BANK";
            document.getElementById('bankModal').classList.add('hidden');
            
            document.getElementById('dashboard').classList.remove('opacity-20', 'pointer-events-none');
            document.getElementById('dot').className = 'w-2 h-2 bg-emerald-500 rounded-full';
            document.getElementById('statusText').innerText = "BANK LINKED (USDC BRIDGE)";
            document.getElementById('sourceTag').innerText = "BANK BRIDGE";
            document.getElementById('sourceTag').className = "text-[9px] bg-emerald-900/40 px-3 py-1 rounded-full font-black text-emerald-400 uppercase tracking-widest";
            document.getElementById('walletBtn').style.display = 'none';
            document.getElementById('bankBtn').innerText = "LINKED";
            
            startSync();
        }

        async function connectWallet() {
            if (window.ethereum) {
                try {
                    const provider = new ethers.providers.Web3Provider(window.ethereum);
                    await provider.send("eth_requestAccounts", []);
                    const addr = await provider.getSigner().getAddress();
                    userAddress = addr;
                    loginSource = "CRYPTO";

                    document.getElementById('dashboard').classList.remove('opacity-20', 'pointer-events-none');
                    document.getElementById('dot').className = 'w-2 h-2 bg-emerald-500 rounded-full';
                    document.getElementById('statusText').innerText = `WALLET: ${addr.substring(0,10)}...`;
                    document.getElementById('bankBtn').style.display = 'none';
                    document.getElementById('walletBtn').innerText = "CONNECTED";
                    
                    startSync();
                } catch (e) { console.error(e); }
            }
        }

        async function executeDeployment() {
            const amount = document.getElementById('depositInput').value;
            const btn = document.getElementById('executeBtn');
            const status = document.getElementById('txStatus');
            
            btn.disabled = true;
            status.classList.remove('hidden');
            status.className = "text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20";
            status.innerText = loginSource === "BANK" ? "INITIATING ACH-TO-USDC SWAP..." : "ENGAGING SMART CONTRACT...";

            const res = await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    address: userAddress, 
                    amount: parseFloat(amount), 
                    simulate: true,
                    source: loginSource
                })
            });
            const result = await res.json();
            if (result.status === "success") {
                btn.innerText = "YIELD ACTIVE";
                status.innerText = "SUCCESS: LIQUIDITY DEPLOYED.";
                status.className = "text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
            }
        }

        function startSync() {
            if (syncInterval) clearInterval(syncInterval);
            syncInterval = setInterval(async () => {
                const res = await fetch(`/stats/${userAddress}`);
                const data = await res.json();
                if (data.stats) {
                    document.getElementById('principalDisplay').innerText = '$' + data.stats.principal.toLocaleString();
                    document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 4});
                    document.getElementById('venueDisplay').innerText = data.stats.venue.replace('_', ' ');
                }
                document.getElementById('logOutput').innerHTML = data.logs.map(l => {
                    const isRebalance = l.includes('REBALANCING');
                    return `
                        <div class="p-3 border-l-2 ${isRebalance ? 'border-purple-500 bg-purple-500/5' : 'border-slate-800'}">
                            <span class="${isRebalance ? 'text-purple-400' : 'text-sky-500'} font-black mr-2 uppercase tracking-widest text-[9px]">Log:</span>
                            <span class="text-slate-300 uppercase">${l.split('KERNEL: ')[1] || l}</span>
                        </div>
                    `;
                }).reverse().join('');
            }, 3000);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)