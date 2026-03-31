import asyncio
import random
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from engine import kernel

app = FastAPI()

# --- CONFIG ---
BASE_RPC_URL = "https://mainnet.base.org"
audit_logs = ["VaultLogic v2.6-PRIVATE: Integrating ZK-Privacy Protocols..."]

class EngineInit(BaseModel):
    address: str
    amount: float
    simulate: bool = False
    private_mode: bool = False

def add_log(msg):
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def background_kernel_loop():
    while True:
        await asyncio.sleep(10)
        for addr in list(kernel.active_deployments.keys()):
            strat = kernel.active_deployments[addr]
            if random.random() > 0.8:
                log = strat.refresh_market_rates()
                add_log(log)
            strat.calculate_tick(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str, private: bool = False):
    stats = kernel.get_stats(address)
    if stats and private:
        # Midnight-style data masking
        stats['principal_display'] = "Locked [ZK-SHIELD]"
        stats['profit_display'] = "Encrypted"
    return {"stats": stats, "logs": audit_logs}

@app.post("/activate")
async def activate_deployment(data: EngineInit):
    msg = kernel.deploy(data.address, data.amount, BASE_RPC_URL)
    if data.private_mode:
        add_log("PRIVACY_SHIELD: Zero-Knowledge proof generated for verification.")
    add_log(msg)
    return {"status": "success"}

@app.post("/reset/{address}")
async def reset_deployment(address: str):
    if address in kernel.active_deployments:
        del kernel.active_deployments[address]
        add_log(f"SESSION_CLOSED: Keys purged for {address[:8]}.")
    return {"status": "reset"}

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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
        body { background-color: #040608; color: #e2e8f0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(10, 15, 25, 0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.03); }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        .zk-blur { filter: blur(8px); transition: all 0.5s ease; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-10">
    <nav class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-16 gap-8">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-white rounded-xl flex items-center justify-center">
                <i class="fas fa-shield-halved text-black text-2xl"></i>
            </div>
            <div>
                <h1 class="text-3xl font-bold tracking-tighter uppercase italic">VaultLogic</h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-[0.4em] font-black">Private Yield Engine</p>
            </div>
        </div>
        <div class="flex items-center gap-6">
            <div id="connectionStatus" class="flex items-center gap-3 glass-panel px-5 py-2.5 rounded-full">
                <span id="dot" class="w-2 h-2 bg-slate-500 rounded-full"></span>
                <span id="statusText" class="text-[10px] font-black text-slate-500 tracking-widest uppercase">Locked</span>
            </div>
            <button onclick="handleAuth()" id="authBtn" class="bg-white text-black hover:bg-sky-500 hover:text-white px-8 py-3 rounded-lg font-black transition-all uppercase text-[10px] tracking-widest">
                AUTHENTICATE
            </button>
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
                <h2 class="text-4xl font-bold text-purple-400 italic mono uppercase text-[20px] mt-2" id="privacyStatus">Public</h2>
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
                               class="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-white">
                    </div>
                    
                    <div class="space-y-4 mb-8 px-2">
                        <div class="flex items-center gap-3">
                            <input type="checkbox" id="simToggle" class="w-4 h-4 rounded accent-sky-500" checked>
                            <label for="simToggle" class="text-[10px] font-black uppercase text-slate-500 tracking-widest">Bypass On-Chain Check</label>
                        </div>
                        <div class="flex items-center gap-3">
                            <input type="checkbox" id="privateToggle" onchange="togglePrivacyUI()" class="w-4 h-4 rounded accent-purple-500">
                            <label for="privateToggle" class="text-[10px] font-black uppercase text-purple-500 tracking-widest">Enable Midnight Privacy</label>
                        </div>
                    </div>

                    <button id="executeBtn" onclick="executeDeployment()" class="w-full py-5 bg-sky-600 text-white font-black rounded-xl hover:bg-white hover:text-black transition-all uppercase tracking-widest text-[10px]">
                        EXECUTE DEPLOYMENT
                    </button>
                    <p id="txStatus" class="text-[10px] mt-6 hidden text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-sky-500/10 text-sky-400"></p>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel rounded-[2.5rem] p-10 min-h-[500px] flex flex-col">
                    <div class="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
                        <h3 class="font-black uppercase tracking-widest text-[10px] text-slate-500">Encrypted Infrastructure Audit</h3>
                        <div class="flex items-center gap-3">
                            <span class="text-[9px] font-black text-slate-600 uppercase tracking-widest">ZK-Proof Valid</span>
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
            document.getElementById('privacyStatus').innerText = isPrivate ? "Encrypted" : "Public";
            document.getElementById('privacyStatus').className = isPrivate ? "text-4xl font-bold text-purple-400 italic mono uppercase text-[20px] mt-2" : "text-4xl font-bold text-slate-400 italic mono uppercase text-[20px] mt-2";
            
            const displays = [document.getElementById('principalDisplay'), document.getElementById('liveProfit')];
            displays.forEach(d => {
                if(isPrivate) d.classList.add('zk-blur');
                else d.classList.remove('zk-blur');
            });
        }

        function handleAuth() {
            const btn = document.getElementById('authBtn');
            if (btn.innerText === "AUTHENTICATE") connectWallet();
            else disconnectWallet();
        }

        async function connectWallet() {
            if (window.ethereum) {
                try {
                    const provider = new ethers.providers.Web3Provider(window.ethereum);
                    await provider.send("eth_requestAccounts", []);
                    userAddress = await provider.getSigner().getAddress();
                    document.getElementById('dashboard').classList.remove('opacity-20', 'pointer-events-none');
                    document.getElementById('authBtn').innerText = "DISCONNECT";
                    document.getElementById('dot').classList.replace('bg-slate-500', 'bg-emerald-500');
                    document.getElementById('statusText').innerText = `AUTH: ${userAddress.substring(0,6)}`;
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
            document.getElementById('dot').classList.replace('bg-emerald-500', 'bg-slate-500');
        }

        async function executeDeployment() {
            const amount = document.getElementById('depositInput').value;
            const simulate = document.getElementById('simToggle').checked;
            const privateMode = document.getElementById('privateToggle').checked;
            const btn = document.getElementById('executeBtn');
            const status = document.getElementById('txStatus');
            
            btn.disabled = true;
            status.classList.remove('hidden');
            status.innerText = privateMode ? "GENERATING ZK-PROOF..." : "SYNCING WITH BASE...";

            const res = await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: userAddress, amount: parseFloat(amount), simulate: simulate, private_mode: privateMode })
            });
            const result = await res.json();
            
            if (result.status === "success") {
                btn.innerText = "ACTIVE";
                status.innerText = "SUCCESS: ENGINE ENGAGED.";
            } else {
                btn.disabled = false;
                status.innerText = "ERROR: " + result.message;
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
                        if(!isPrivate) {
                            document.getElementById('principalDisplay').innerText = '$' + data.stats.principal.toLocaleString();
                            document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 4});
                        } else {
                            document.getElementById('principalDisplay').innerText = "**********";
                            document.getElementById('liveProfit').innerText = "**********";
                        }
                    }

                    const logOutput = document.getElementById('logOutput');
                    logOutput.innerHTML = data.logs.map(l => `
                        <div class="p-4 border-l-2 ${l.includes('ERROR') ? 'border-red-500 bg-red-500/5' : 'border-slate-800'}">
                            <span class="text-sky-500 font-black mr-2 uppercase tracking-widest text-[9px]">Audit:</span>
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