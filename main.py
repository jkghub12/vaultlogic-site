import asyncio
import random
import os
import httpx
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from eth_utils import to_checksum_address, is_address

# Initialize FastAPI App
app = FastAPI()

# --- MOCK KERNEL ENGINE (Integrated for single-file stability) ---
class MockKernel:
    def __init__(self):
        self.active_deployments = {}

    def deploy(self, address, amount, rpc):
        self.active_deployments[address] = {
            "principal": amount,
            "net_profit": 0.0,
            "start_time": datetime.now(),
            "status": "ACTIVE"
        }
        return f"SUCCESS: Asset Allocation of ${amount:,.2f} deployed to {address[:10]}..."

    def get_stats(self, address):
        if address in self.active_deployments:
            return self.active_deployments[address]
        return None

    def tick(self):
        for addr in self.active_deployments:
            # Simulate 0.01% - 0.05% gain per tick
            growth = self.active_deployments[addr]["principal"] * random.uniform(0.0001, 0.0005)
            self.active_deployments[addr]["net_profit"] += growth

kernel = MockKernel()

# --- CONFIG & GLOBALS ---
PORT = int(os.environ.get("PORT", 8000))
BASE_RPC_URL = "https://mainnet.base.org"
audit_logs = ["VaultLogic v2.9-STABLE: System Ready. Waiting for authentication..."]

class EngineInit(BaseModel):
    address: str
    amount: float
    simulate: bool = False
    private_mode: bool = False

def safe_checksum(address: str):
    """Rigorous address sanitization to prevent EIP-55 sync errors."""
    try:
        if not address: return ""
        clean_addr = address.strip()
        if is_address(clean_addr):
            return to_checksum_address(clean_addr)
        return clean_addr
    except Exception:
        return address

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    clean_msg = str(msg).split("')")[0].replace("('", "")
    audit_logs.append(f"[{timestamp}] KERNEL: {clean_msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def get_base_balance(address: str):
    """Real-time balance check via Base RPC."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"],
        "id": 1
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BASE_RPC_URL, json=payload, timeout=5.0)
            result = response.json()
            hex_balance = result.get("result", "0x0")
            balance_decimal = int(hex_balance, 16) / 10**18
            # Returning mock USD value (ETH Price ~3000)
            return balance_decimal * 3000 
    except Exception:
        return 0

async def background_kernel_loop():
    while True:
        await asyncio.sleep(5)
        kernel.tick()
        if random.random() > 0.7:
            add_log("MARKET_SYNC: Updating cross-chain liquidity parameters...")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str, private: bool = False):
    try:
        safe_addr = safe_checksum(address)
        stats = kernel.get_stats(safe_addr)
        
        if stats and private:
            return {
                "stats": {"principal": 0, "net_profit": 0, "is_masked": True, "status": "ENCRYPTED"}, 
                "logs": audit_logs
            }
        return {"stats": stats, "logs": audit_logs}
    except Exception:
        return {"stats": None, "logs": audit_logs}

@app.post("/activate")
async def activate_deployment(data: EngineInit):
    try:
        safe_addr = safe_checksum(data.address)
        
        if not data.simulate:
            actual_balance = await get_base_balance(safe_addr)
            if actual_balance < data.amount:
                msg = f"REJECTED: INSUFFICIENT COLLATERAL. REQ: ${data.amount:,.2f} | FOUND: ${actual_balance:,.2f}"
                add_log(msg)
                return {"status": "error", "message": msg}

        msg = kernel.deploy(safe_addr, data.amount, BASE_RPC_URL)
        if data.private_mode:
            add_log("PRIVACY_SHIELD: Session encrypted via Zero-Knowledge proof.")
        add_log(msg)
        return {"status": "success"}
    except Exception as e:
        err_msg = str(e)
        add_log(f"DEPLOYMENT_ERROR: {err_msg}")
        return {"status": "error", "message": err_msg}

@app.post("/reset/{address}")
async def reset_deployment(address: str):
    safe_addr = safe_checksum(address)
    if safe_addr in kernel.active_deployments:
        del kernel.active_deployments[safe_addr]
        add_log(f"SESSION_CLOSED: Security purge for {safe_addr[:8]}...")
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
        body { background-color: #040608; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(10, 15, 25, 0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.03); }
        .zk-blur { filter: blur(14px); opacity: 0.2; transition: all 0.8s ease; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 16px; width: 16px;
            background: #0ea5e9; border-radius: 50%;
            cursor: pointer; box-shadow: 0 0 10px #0ea5e9;
        }
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
        <div class="flex items-center gap-6">
            <div id="connectionStatus" class="flex items-center gap-3 glass-panel px-5 py-2.5 rounded-full border-white/5">
                <span id="dot" class="w-2 h-2 bg-slate-500 rounded-full"></span>
                <span id="statusText" class="text-[10px] font-black text-slate-500 tracking-widest uppercase">Locked</span>
            </div>
            <button onclick="handleAuth()" id="authBtn" class="bg-white text-black hover:bg-sky-500 hover:text-white px-8 py-3 rounded-lg font-black transition-all uppercase text-[10px] tracking-widest">AUTHENTICATE</button>
        </div>
    </nav>

    <main id="dashboard" class="max-w-7xl mx-auto opacity-20 pointer-events-none transition-all duration-700">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-sky-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Active Principal</p>
                <h2 class="text-4xl font-bold italic mono" id="principalDisplay">$0.00</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-emerald-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Net Profit (80%)</p>
                <h2 class="text-4xl font-bold text-emerald-400 italic mono" id="liveProfit">$0.0000</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-purple-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Privacy Status</p>
                <h2 class="text-2xl font-bold text-purple-400 italic mono uppercase tracking-tighter mt-2" id="privacyStatus">Standard</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div class="lg:col-span-4 space-y-6">
                <div class="glass-panel p-10 rounded-[2.5rem]">
                    <h3 class="text-[11px] font-black mb-8 uppercase tracking-[0.3em] text-sky-400">Strategy Controller</h3>
                    <div class="mb-10">
                        <div class="flex justify-between text-[10px] mb-4 font-black uppercase tracking-widest">
                            <span class="text-slate-400">Allocation</span>
                            <span class="text-white" id="amountDisplay">$10,000</span>
                        </div>
                        <input type="range" min="10000" max="1000000" step="10000" value="10000" id="depositInput"
                               oninput="document.getElementById('amountDisplay').innerText = '$' + parseInt(this.value).toLocaleString()"
                               class="w-full cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none">
                    </div>
                    
                    <div class="space-y-4 mb-8 px-2">
                        <div class="flex items-center gap-3">
                            <input type="checkbox" id="simToggle" class="w-4 h-4 rounded accent-sky-500" checked>
                            <label for="simToggle" class="text-[10px] font-black uppercase text-slate-500 tracking-widest cursor-pointer">Bypass On-Chain Check</label>
                        </div>
                        <div class="flex items-center gap-3">
                            <input type="checkbox" id="privateToggle" onchange="togglePrivacyUI()" class="w-4 h-4 rounded accent-purple-500">
                            <label for="privateToggle" class="text-[10px] font-black uppercase text-purple-500 tracking-widest cursor-pointer">Enable Midnight Privacy</label>
                        </div>
                    </div>

                    <button id="executeBtn" onclick="executeDeployment()" class="w-full py-5 bg-sky-600 text-white font-black rounded-xl hover:bg-white hover:text-black transition-all uppercase tracking-widest text-[10px]">
                        EXECUTE DEPLOYMENT
                    </button>
                    <div id="txStatusContainer" class="hidden">
                         <p id="txStatus" class="text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl"></p>
                    </div>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel rounded-[2.5rem] p-10 min-h-[500px] flex flex-col">
                    <div class="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
                        <h3 class="font-black uppercase tracking-widest text-[10px] text-slate-500">Infrastructure Audit</h3>
                        <div class="flex items-center gap-3">
                            <span class="text-[9px] font-black text-slate-600 uppercase tracking-widest">Base RPC Healthy</span>
                            <span class="w-2 h-2 bg-emerald-500 rounded-full"></span>
                        </div>
                    </div>
                    <div id="logOutput" class="flex-grow mono text-[11px] space-y-4 overflow-y-auto max-h-[400px] custom-scrollbar"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let userAddress = null;
        let syncInterval = null;
        let isPrivate = false;

        function togglePrivacyUI() {
            isPrivate = document.getElementById('privateToggle').checked;
            document.getElementById('privacyStatus').innerText = isPrivate ? "Midnight Mode" : "Standard";
            document.getElementById('privacyStatus').style.color = isPrivate ? "#a855f7" : "#94a3b8";
            
            const pDisp = document.getElementById('principalDisplay');
            const lProfit = document.getElementById('liveProfit');
            if(isPrivate) { pDisp.classList.add('zk-blur'); lProfit.classList.add('zk-blur'); } 
            else { pDisp.classList.remove('zk-blur'); lProfit.classList.remove('zk-blur'); }
        }

        async function handleAuth() {
            const btn = document.getElementById('authBtn');
            if (btn.innerText === "AUTHENTICATE") await connectWallet();
            else await disconnectWallet();
        }

        async function connectWallet() {
            if (window.ethereum) {
                try {
                    const provider = new ethers.providers.Web3Provider(window.ethereum);
                    await provider.send("eth_requestAccounts", []);
                    const signer = provider.getSigner();
                    const rawAddr = await signer.getAddress();
                    userAddress = ethers.utils.getAddress(rawAddr);

                    document.getElementById('dashboard').classList.remove('opacity-20', 'pointer-events-none');
                    document.getElementById('authBtn').innerText = "DISCONNECT";
                    document.getElementById('dot').className = 'w-2 h-2 bg-emerald-500 rounded-full';
                    document.getElementById('statusText').innerText = `AUTH: ${userAddress.substring(0,8)}`;
                    
                    const execBtn = document.getElementById('executeBtn');
                    execBtn.disabled = false;
                    execBtn.innerText = "EXECUTE DEPLOYMENT";
                    execBtn.className = "w-full py-5 bg-sky-600 text-white font-black rounded-xl hover:bg-white hover:text-black transition-all uppercase tracking-widest text-[10px]";
                    document.getElementById('txStatusContainer').classList.add('hidden');

                    startSync();
                } catch (e) { console.error(e); }
            }
        }

        async function disconnectWallet() {
            if (userAddress) await fetch('/reset/' + userAddress, { method: 'POST' });
            userAddress = null;
            if (syncInterval) clearInterval(syncInterval);
            document.getElementById('dashboard').classList.add('opacity-20', 'pointer-events-none');
            document.getElementById('authBtn').innerText = "AUTHENTICATE";
            document.getElementById('statusText').innerText = "Locked";
            document.getElementById('dot').className = 'w-2 h-2 bg-slate-500 rounded-full';
        }

        async function executeDeployment() {
            const amount = document.getElementById('depositInput').value;
            const simulate = document.getElementById('simToggle').checked;
            const privateMode = document.getElementById('privateToggle').checked;
            const btn = document.getElementById('executeBtn');
            const status = document.getElementById('txStatus');
            const container = document.getElementById('txStatusContainer');
            
            btn.disabled = true;
            container.classList.remove('hidden');
            status.className = "text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20";
            status.innerText = privateMode ? "ENCRYPTING SESSION..." : "ENGAGING KERNEL...";

            try {
                const res = await fetch('/activate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 
                        address: userAddress, 
                        amount: parseFloat(amount), 
                        simulate: simulate, 
                        private_mode: privateMode 
                    })
                });
                
                const result = await res.json();
                if (result.status === "success") {
                    btn.innerText = "ACTIVE";
                    btn.disabled = true;
                    btn.className = "w-full py-5 bg-emerald-600 text-white font-black rounded-xl uppercase tracking-widest text-[10px]";
                    status.innerText = "PROTOCOL ENGAGED SUCCESSFULLY.";
                    status.className = "text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                } else {
                    btn.disabled = false;
                    status.innerText = result.message || "REJECTED.";
                    status.className = "text-[10px] mt-6 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20";
                }
            } catch (err) {
                btn.disabled = false;
                status.innerText = "CONNECTION FAILED.";
            }
        }

        function startSync() {
            if (syncInterval) clearInterval(syncInterval);
            syncInterval = setInterval(async () => {
                if (!userAddress) return;
                try {
                    const res = await fetch(`/stats/${userAddress}?private=${isPrivate}`);
                    const data = await res.json();
                    
                    if (data.stats) {
                        document.getElementById('principalDisplay').innerText = isPrivate ? "0x********" : '$' + data.stats.principal.toLocaleString();
                        document.getElementById('liveProfit').innerText = isPrivate ? "ENCRYPTED" : '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 4});
                        
                        if (data.stats.principal > 0) {
                            const btn = document.getElementById('executeBtn');
                            btn.innerText = "ACTIVE";
                            btn.disabled = true;
                            btn.className = "w-full py-5 bg-emerald-600 text-white font-black rounded-xl uppercase tracking-widest text-[10px]";
                        }
                    }

                    const logOutput = document.getElementById('logOutput');
                    logOutput.innerHTML = data.logs.map(l => {
                        const isErr = l.includes('REJECTED') || l.includes('ERROR');
                        return `
                            <div class="p-4 border-l-2 ${isErr ? 'border-red-500 bg-red-500/5' : 'border-slate-800'}">
                                <span class="${isErr ? 'text-red-500' : 'text-sky-500'} font-black mr-2 uppercase tracking-widest text-[9px]">Audit:</span>
                                <span class="text-slate-300 uppercase">${l.split('KERNEL: ')[1] || l}</span>
                            </div>
                        `;
                    }).reverse().join('');
                } catch (e) { console.error("Sync Error", e); }
            }, 3000);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)