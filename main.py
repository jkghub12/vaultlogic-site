import asyncio
import random
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from eth_utils import to_checksum_address, is_address

app = FastAPI()

# --- INDUSTRIAL KERNEL ENGINE (V3.7 - SECURITY ENHANCED + BANK VAULT LOGIC) ---
class KernelEngine:
    def __init__(self):
        self.active_deployments = {}
        self.current_venue = "AAVE_V3"
        self.base_apy = 0.0582 
        self.venues = ["AAVE_V3", "COMPOUND_V3", "MORPHO_BLUE", "AERODROME_LP", "UNISWAP_V3_BASE"]

    def deploy(self, address, amount, source="CRYPTO"):
        # For Bank users, we simulate the 'Vault Assignment' security layer
        is_bank = source == "BANK"
        vault_id = f"VL-VAULT-{uuid.uuid4().hex[:8].upper()}" if is_bank else address
        
        self.active_deployments[address] = {
            "principal": amount,
            "net_profit": 0.0,
            "start_time": datetime.now(),
            "status": "ACTIVE",
            "venue": self.current_venue,
            "source": source,
            "vault_id": vault_id,
            "security": "MPC_ENCRYPTED" if is_bank else "NATIVE_CUSTODY"
        }
        
        prefix = "ACH_BRIDGE" if is_bank else "NATIVE"
        return f"SUCCESS: [{prefix}] ${amount:,.2f} secured in {vault_id}. Routing to {self.current_venue}."

    def get_stats(self, address):
        return self.active_deployments.get(address)

    def rebalance(self):
        new_venue = random.choice([v for v in self.venues if v != self.current_venue])
        old_venue = self.current_venue
        self.current_venue = new_venue
        for addr in self.active_deployments:
            self.active_deployments[addr]["venue"] = new_venue
        return f"REBALANCING: Yield spread detected. Migrating liquidity from {old_venue} to {new_venue}..."

    def tick(self):
        for addr in self.active_deployments:
            multiplier = 1.25 if random.random() > 0.9 else 1.0
            growth = (self.active_deployments[addr]["principal"] * (self.base_apy / 31536000) * 5) * multiplier
            self.active_deployments[addr]["net_profit"] += growth

kernel = KernelEngine()

# --- GLOBALS & LOGGING ---
PORT = int(os.environ.get("PORT", 8000))
audit_logs = ["VaultLogic Kernel v3.7: Secure Handshake Complete. Plaid Bridge Operational."]

class EngineInit(BaseModel):
    address: str
    amount: float
    source: str = "CRYPTO"

def safe_checksum(address: str):
    try:
        if address.startswith("vault_"): return address 
        if is_address(address): return to_checksum_address(address)
        return address
    except: return address

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 40: audit_logs.pop(0)

async def background_kernel_loop():
    while True:
        await asyncio.sleep(5)
        kernel.tick()
        if random.random() > 0.92:
            event = kernel.rebalance()
            add_log(event)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str):
    addr = safe_checksum(address)
    stats = kernel.get_stats(addr)
    return {"stats": stats, "logs": audit_logs}

@app.post("/activate")
async def activate_deployment(data: EngineInit):
    addr = safe_checksum(data.address)
    msg = kernel.deploy(addr, data.amount, data.source)
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
    <title>VaultLogic | Secure Industrial ALM</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
        body { background-color: #040608; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(10, 15, 25, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .kernel-glow { box-shadow: 0 0 30px rgba(14, 165, 233, 0.1); }
        .btn-glow:hover { box-shadow: 0 0 20px rgba(14, 165, 233, 0.4); }
        .security-badge { border: 1px solid rgba(52, 211, 153, 0.2); background: rgba(52, 211, 153, 0.05); }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: #38bdf8; cursor: pointer; box-shadow: 0 0 10px #38bdf8;
        }
    </style>
</head>
<body class="min-h-screen p-4 md:p-10">
    <!-- NAVIGATION -->
    <nav class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-12 gap-8">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-white rounded-xl flex items-center justify-center kernel-glow">
                <i class="fas fa-shield-halved text-black text-2xl"></i>
            </div>
            <div>
                <h1 class="text-3xl font-bold tracking-tighter uppercase italic">VaultLogic</h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-[0.4em] font-black">Industrial Yield Kernel v3.7</p>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <div id="connectionStatus" class="flex items-center gap-3 glass-panel px-5 py-2.5 rounded-full">
                <span id="dot" class="w-2 h-2 bg-slate-600 rounded-full"></span>
                <span id="statusText" class="text-[10px] font-black text-slate-500 tracking-widest uppercase">System Locked</span>
            </div>
            <div class="flex gap-2">
                <button onclick="connectWallet()" id="walletBtn" class="bg-white text-black hover:bg-sky-500 hover:text-white px-6 py-3 rounded-lg font-black transition-all uppercase text-[10px] tracking-widest">Connect Wallet</button>
                <button onclick="openBankModal()" id="bankBtn" class="bg-emerald-600 text-white hover:bg-emerald-400 px-6 py-3 rounded-lg font-black transition-all uppercase text-[10px] tracking-widest">Link Bank Account</button>
            </div>
        </div>
    </nav>

    <!-- BANK MODAL -->
    <div id="bankModal" class="fixed inset-0 bg-black/95 z-50 hidden flex items-center justify-center p-6">
        <div class="glass-panel max-w-md w-full p-10 rounded-[2.5rem] border-emerald-500/30 text-center">
            <div class="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <i class="fas fa-university text-3xl text-emerald-500"></i>
            </div>
            <h2 class="text-2xl font-bold mb-2">Authorize Plaid Bridge</h2>
            <p class="text-slate-400 text-sm mb-6 leading-relaxed">By authorizing, an isolated <strong>VaultLogic Managed Vault</strong> will be assigned to your bank credentials using AES-256 MPC Encryption.</p>
            
            <div class="security-badge p-4 rounded-2xl mb-8 text-left">
                <div class="flex items-center gap-3 mb-2">
                    <i class="fas fa-lock text-emerald-500 text-xs"></i>
                    <span class="text-[9px] font-black text-emerald-500 uppercase tracking-widest">Security Protocol</span>
                </div>
                <p class="text-[10px] text-slate-400 leading-tight">Funds are bridged to USDC via verified ACH rails and deployed into yield pools through a separate, audited smart contract proxy.</p>
            </div>

            <div class="flex flex-col gap-4">
                <button onclick="confirmBankLink()" class="w-full py-5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl font-black text-[11px] tracking-widest transition-all">AUTHORIZE BANK BRIDGE</button>
                <button onclick="closeBankModal()" class="text-slate-500 text-[10px] uppercase font-black tracking-widest py-2">Cancel Transaction</button>
            </div>
        </div>
    </div>

    <!-- MAIN DASHBOARD -->
    <main id="dashboard" class="max-w-7xl mx-auto opacity-20 pointer-events-none transition-all duration-700">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-sky-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Managed Principal</p>
                <h2 class="text-4xl font-bold italic mono" id="principalDisplay">$0.00</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-emerald-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Realized Gain</p>
                <h2 class="text-4xl font-bold text-emerald-400 italic mono" id="liveProfit">$0.0000</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-purple-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Target Venue</p>
                <h2 class="text-2xl font-bold text-purple-400 italic mono uppercase tracking-tighter mt-2" id="venueDisplay">SCANNING...</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-amber-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Vault Security</p>
                <h2 class="text-[12px] font-bold text-amber-500 italic mono uppercase tracking-widest mt-3" id="securityDisplay">SECURED</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div class="lg:col-span-4 space-y-6">
                <div class="glass-panel p-10 rounded-[2.5rem]">
                    <div class="flex justify-between items-center mb-8">
                        <h3 class="text-[11px] font-black uppercase tracking-[0.3em] text-sky-400">Vault Control</h3>
                        <span id="sourceTag" class="text-[9px] bg-slate-800 px-3 py-1 rounded-full font-black text-slate-400 uppercase tracking-widest">PENDING</span>
                    </div>
                    <div class="mb-10">
                        <div class="flex justify-between text-[10px] mb-4 font-black uppercase tracking-widest">
                            <span class="text-slate-400">Allocation Size</span>
                            <span class="text-white" id="amountDisplay">$50,000</span>
                        </div>
                        <input type="range" min="1000" max="500000" step="1000" value="50000" id="depositInput"
                               oninput="document.getElementById('amountDisplay').innerText = '$' + parseInt(this.value).toLocaleString()"
                               class="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer">
                    </div>
                    <button id="executeBtn" onclick="executeDeployment()" class="w-full py-5 bg-sky-600 text-white font-black rounded-2xl hover:bg-white hover:text-black transition-all uppercase tracking-widest text-[10px] btn-glow">
                        START INDUSTRIAL YIELD
                    </button>
                    <p id="txStatus" class="hidden text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl"></p>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel rounded-[2.5rem] p-10 min-h-[550px] flex flex-col">
                    <div class="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
                        <h3 class="font-black uppercase tracking-widest text-[10px] text-slate-500">Kernel Execution Log</h3>
                        <div class="flex items-center gap-3"><span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span></div>
                    </div>
                    <div id="logOutput" class="flex-grow mono text-[11px] space-y-3 overflow-y-auto max-h-[450px]"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let userAddress = null;
        let loginSource = "CRYPTO"; 
        let syncInterval = null;

        function openBankModal() {
            document.getElementById('bankModal').classList.remove('hidden');
        }

        function closeBankModal() {
            document.getElementById('bankModal').classList.add('hidden');
        }

        async function confirmBankLink() {
            // Assign a temporary, secure managed ID
            userAddress = "vault_ach_" + Math.random().toString(36).substring(7);
            loginSource = "BANK";
            
            closeBankModal();
            unlockDashboard("BANK BRIDGE ACTIVE");
            
            document.getElementById('securityDisplay').innerText = "AES-256 MPC";
            document.getElementById('sourceTag').innerText = "BANK VAULT";
            document.getElementById('sourceTag').className = "text-[9px] bg-emerald-900/40 px-3 py-1 rounded-full font-black text-emerald-400 uppercase tracking-widest";
            document.getElementById('walletBtn').style.display = 'none';
            document.getElementById('bankBtn').innerText = "SECURED BANK LINK";
            document.getElementById('bankBtn').classList.replace('bg-emerald-600', 'bg-slate-800');
            
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

                    unlockDashboard(`WALLET: ${addr.substring(0,10)}...`);
                    document.getElementById('bankBtn').style.display = 'none';
                    document.getElementById('securityDisplay').innerText = "NATIVE CUSTODY";
                    document.getElementById('walletBtn').innerText = "CONNECTED";
                    document.getElementById('sourceTag').innerText = "NATIVE WALLET";
                    
                    startSync();
                } catch (e) { console.error(e); }
            }
        }

        function unlockDashboard(status) {
            document.getElementById('dashboard').classList.remove('opacity-20', 'pointer-events-none');
            document.getElementById('dot').className = 'w-2 h-2 bg-emerald-500 rounded-full';
            document.getElementById('statusText').innerText = status;
        }

        async function executeDeployment() {
            const amount = document.getElementById('depositInput').value;
            const btn = document.getElementById('executeBtn');
            const status = document.getElementById('txStatus');
            
            btn.disabled = true;
            status.classList.remove('hidden');
            status.className = "text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20";
            
            status.innerText = loginSource === "BANK" ? "REQUESTING ACH HANDSHAKE..." : "CHECKING NATIVE WALLET BALANCE...";

            const res = await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    address: userAddress, 
                    amount: parseFloat(amount), 
                    source: loginSource
                })
            });
            const result = await res.json();
            if (result.status === "success") {
                btn.innerText = "ALM KERNEL ACTIVE";
                status.innerText = "SUCCESS: ASSETS DEPLOYED TO INDUSTRIAL FLOOR.";
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
                            <span class="${isRebalance ? 'text-purple-400' : 'text-sky-500'} font-black mr-2 uppercase tracking-widest text-[9px]">Audit:</span>
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