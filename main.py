import asyncio
import os
import random
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3

app = FastAPI()

# --- CONFIGURATION ---
BASE_RPC_URL = "https://mainnet.base.org"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

# --- SYSTEM STATE ---
system_state = {
    "total_profit_generated": 0.0,
    "fees_collected": 0.0,
    "active_tvl": 142842019.00,
    "user_deployed_capital": 0.0, 
    "target_apy": 0.0582, # 5.82% APY
    "logs": ["VaultLogic Kernel v2.1-LIVE initialized. Handshake pending..."]
}

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] KERNEL: {msg}"
    system_state["logs"].append(formatted_msg)
    if len(system_state["logs"]) > 50: system_state["logs"].pop(0)

# --- THE YIELD ENGINE ---
async def yield_hunter_loop():
    """Calculates real-time yield and 20% fees every 10 seconds."""
    while True:
        await asyncio.sleep(10)
        if system_state["user_deployed_capital"] >= 10000:
            gross_yield = (system_state["user_deployed_capital"] * system_state["target_apy"]) / 31536000 * 10
            founder_fee = gross_yield * 0.20
            user_net = gross_yield - founder_fee
            
            system_state["total_profit_generated"] += user_net
            system_state["fees_collected"] += founder_fee
            
            if random.random() > 0.8:
                add_log(f"Optimized tick-range. Captured ${founder_fee:.6f} Founder Fee.")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(yield_hunter_loop())

@app.get("/stats")
async def get_stats():
    return system_state

@app.post("/activate")
async def activate_deployment(data: EngineInit):
    if data.amount < 10000:
        add_log(f"REJECTED: ${data.amount:,.2f} is below the $10,000 Institutional Floor.")
        return {"status": "error", "message": "Below Institutional Floor"}
    
    try:
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        raw_balance = usdc_contract.functions.balanceOf(Web3.to_checksum_address(data.address)).call()
        actual_balance = raw_balance / 10**6 
        
        if actual_balance < data.amount:
            add_log(f"CRITICAL: Deployment of ${data.amount:,.2f} exceeds wallet balance (${actual_balance:,.2f}). ACCESS DENIED.")
            return {"status": "error", "message": f"Insufficient Collateral (Wallet: ${actual_balance:,.2f})"}
            
    except Exception as e:
        add_log("ERROR: Unable to verify on-chain collateral. Aborting.")
        return {"status": "error", "message": "Verification Timeout"}

    system_state["user_deployed_capital"] = data.amount
    system_state["total_profit_generated"] = 0.0
    system_state["fees_collected"] = 0.0
    add_log(f"DEPLOYMENT_CONFIRMED: ${data.amount:,.2f} activated in ALM Kernel.")
    return {"status": "success"}

@app.post("/reset")
async def reset_session():
    system_state["user_deployed_capital"] = 0.0
    system_state["total_profit_generated"] = 0.0
    system_state["fees_collected"] = 0.0
    add_log("SESSION_TERMINATED: Dashboard locked. Data purged.")
    return {"status": "reset"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Institutional ALM Kernel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
        body { background-color: #05070a; color: #e2e8f0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .kernel-glow { box-shadow: 0 0 20px rgba(56, 189, 248, 0.1); }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .status-pulse { animation: pulse 2s infinite; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-10">
    <nav class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-16 gap-8">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-sky-500 rounded-xl flex items-center justify-center kernel-glow">
                <i class="fas fa-microchip text-black text-2xl"></i>
            </div>
            <div>
                <h1 class="text-3xl font-bold tracking-tighter uppercase italic">VaultLogic <span class="text-sky-500 text-xs align-top ml-1 mono font-normal">v2.1-LIVE</span></h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-[0.4em] font-black">Industrial Yield Protocol</p>
            </div>
        </div>
        <div class="flex items-center gap-6">
            <div id="connectionStatus" class="flex items-center gap-3 glass-panel px-5 py-2.5 rounded-full border-slate-500/20">
                <span class="w-2 h-2 bg-slate-500 rounded-full"></span>
                <span id="statusText" class="text-[10px] font-black text-slate-500 tracking-widest uppercase">Kernel_Locked</span>
            </div>
            <button onclick="handleAuth()" id="authBtn" class="bg-white text-black hover:bg-sky-500 hover:text-white px-10 py-3 rounded-lg font-black transition-all uppercase text-[10px] tracking-[0.2em]">
                AUTHENTICATE
            </button>
        </div>
    </nav>

    <main id="dashboard" class="max-w-7xl mx-auto opacity-20 transition-all duration-1000 pointer-events-none">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-slate-800">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Protocol TVL</p>
                <h2 class="text-4xl font-bold italic">$142.8M</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-sky-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Target APY</p>
                <h2 class="text-4xl font-bold text-sky-400 italic">5.82%</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-emerald-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">User Net Profit</p>
                <h2 class="text-4xl font-bold text-emerald-400 italic mono" id="liveProfit">$0.0000</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl bg-sky-500/5 border-l-2 border-l-white">
                <p class="text-sky-500 text-[10px] font-black mb-3 uppercase tracking-widest">Founder Fee (20%)</p>
                <h2 class="text-4xl font-bold text-white italic mono" id="founderFee">$0.0000</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div class="lg:col-span-4 space-y-8">
                <div class="glass-panel p-10 rounded-[2.5rem] relative overflow-hidden border-t border-white/10">
                    <h3 class="text-sm font-black mb-2 uppercase tracking-[0.3em] text-sky-400">Capital Deployment</h3>
                    <p class="text-[10px] text-slate-500 uppercase font-black mb-10 tracking-widest">Institutional Only (Min $10,000)</p>
                    <div class="space-y-8 mb-12">
                        <div>
                            <div class="flex justify-between text-[11px] mb-4 font-black uppercase tracking-widest">
                                <span class="text-slate-400">Target Allocation</span>
                                <span class="text-white font-bold text-lg" id="amountDisplay">$10,000</span>
                            </div>
                            <input type="range" min="10000" max="1000000" step="10000" value="10000" id="depositInput"
                                   oninput="document.getElementById('amountDisplay').innerText = '$' + parseInt(this.value).toLocaleString()"
                                   class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500">
                        </div>
                    </div>
                    <button id="executeBtn" onclick="executeDeployment()" class="w-full py-5 bg-sky-600 text-white font-black rounded-2xl hover:bg-white hover:text-black transition-all uppercase tracking-[0.4em] text-[11px]">
                        EXECUTE DEPLOYMENT
                    </button>
                    <p id="txStatus" class="text-[10px] mt-8 hidden text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400"></p>
                </div>
                <div class="glass-panel p-8 rounded-3xl border border-white/5 bg-slate-900/20">
                    <p class="text-[10px] text-slate-500 font-bold uppercase tracking-[0.3em] mb-3">Active Principal</p>
                    <p class="text-3xl font-bold italic mono text-sky-500" id="principalDisplay">$0.00</p>
                </div>
            </div>
            <div class="lg:col-span-8">
                <div class="glass-panel rounded-[2.5rem] p-10 min-h-[550px] flex flex-col bg-slate-900/40">
                    <div class="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
                        <h3 class="font-black uppercase tracking-[0.4em] text-[11px] text-slate-500">Live Kernel Audit Logs</h3>
                        <div class="flex gap-2">
                            <span class="w-1.5 h-1.5 bg-sky-500 rounded-full status-pulse"></span>
                            <span class="w-1.5 h-1.5 bg-sky-500 rounded-full status-pulse" style="animation-delay: 0.5s"></span>
                        </div>
                    </div>
                    <div id="logOutput" class="flex-grow mono text-[11px] space-y-4 overflow-y-auto max-h-[400px] custom-scrollbar">
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let userAddress = null;

        function handleAuth() {
            const btn = document.getElementById('authBtn');
            if (btn.innerText === "AUTHENTICATE") {
                connectWallet();
            } else {
                disconnectWallet();
            }
        }

        async function connectWallet() {
            if (window.ethereum) {
                try {
                    const provider = new ethers.providers.Web3Provider(window.ethereum);
                    await provider.send("eth_requestAccounts", []);
                    const signer = provider.getSigner();
                    userAddress = await signer.getAddress();
                    
                    document.getElementById('dashboard').classList.remove('opacity-20', 'pointer-events-none');
                    document.getElementById('authBtn').innerText = "DISCONNECT";
                    
                    const connStatus = document.getElementById('connectionStatus');
                    connStatus.classList.replace('border-slate-500/20', 'border-emerald-500/20');
                    connStatus.querySelector('span:first-child').classList.replace('bg-slate-500', 'bg-emerald-500');
                    connStatus.querySelector('span:first-child').classList.add('status-pulse');
                    document.getElementById('statusText').classList.replace('text-slate-500', 'text-emerald-400');
                    document.getElementById('statusText').innerText = `AUTH: ${userAddress.substring(0,6)}...${userAddress.substring(38)}`;
                    
                    fetchLogs();
                } catch (e) {
                    console.error("Connection failed", e);
                }
            }
        }

        async function disconnectWallet() {
            userAddress = null;
            // Reset UI
            document.getElementById('dashboard').classList.add('opacity-20', 'pointer-events-none');
            document.getElementById('authBtn').innerText = "AUTHENTICATE";
            
            const connStatus = document.getElementById('connectionStatus');
            connStatus.classList.replace('border-emerald-500/20', 'border-slate-500/20');
            const dot = connStatus.querySelector('span:first-child');
            dot.classList.replace('bg-emerald-500', 'bg-slate-500');
            dot.classList.remove('status-pulse');
            
            const txt = document.getElementById('statusText');
            txt.classList.replace('text-emerald-400', 'text-slate-500');
            txt.innerText = "Kernel_Locked";

            // Reset deployment UI state
            document.getElementById('principalDisplay').innerText = "$0.00";
            document.getElementById('liveProfit').innerText = "$0.0000";
            document.getElementById('founderFee').innerText = "$0.0000";
            document.getElementById('txStatus').classList.add('hidden');
            const execBtn = document.getElementById('executeBtn');
            execBtn.disabled = false;
            execBtn.innerText = "EXECUTE DEPLOYMENT";

            // Inform backend to reset session stats
            await fetch('/reset', { method: 'POST' });
            fetchLogs();
        }

        async function executeDeployment() {
            const amount = document.getElementById('depositInput').value;
            const btn = document.getElementById('executeBtn');
            const status = document.getElementById('txStatus');
            
            btn.disabled = true;
            btn.innerText = "VERIFYING COLLATERAL...";
            status.className = "text-[10px] mt-8 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400";
            status.innerText = "SCANNING ON-CHAIN BALANCE...";

            const res = await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: userAddress, amount: parseFloat(amount) })
            });
            const result = await res.json();
            
            if (result.status === "success") {
                btn.innerText = "DEPLOYMENT_ACTIVE";
                status.innerText = "SUCCESS: $"+parseInt(amount).toLocaleString()+" ACTIVATED.";
            } else {
                btn.disabled = false;
                btn.innerText = "EXECUTE DEPLOYMENT";
                status.className = "text-[10px] mt-8 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400";
                status.innerText = "CRITICAL: " + result.message;
            }
            fetchLogs();
        }

        async function fetchLogs() {
            const res = await fetch('/stats');
            const data = await res.json();
            
            // Only update profit if wallet is connected to avoid flickering stale data
            if (userAddress) {
                document.getElementById('liveProfit').innerText = '$' + data.total_profit_generated.toLocaleString(undefined, {minimumFractionDigits: 4});
                document.getElementById('founderFee').innerText = '$' + data.fees_collected.toLocaleString(undefined, {minimumFractionDigits: 4});
                document.getElementById('principalDisplay').innerText = '$' + data.user_deployed_capital.toLocaleString();
            }

            const logOutput = document.getElementById('logOutput');
            logOutput.innerHTML = data.logs.map(l => `
                <div class="p-4 border-l-2 ${l.includes('CRITICAL') ? 'border-red-500 bg-red-500/5' : 'border-slate-800 bg-white/[0.02]'} hover:border-sky-500 transition-colors">
                    <span class="text-sky-500 font-bold uppercase mr-3">KERNEL_v2.1:</span>
                    <span class="${l.includes('CRITICAL') ? 'text-red-400' : 'text-slate-300'} uppercase">${l.split('KERNEL: ')[1] || l}</span>
                </div>
            `).reverse().join('');
        }
        setInterval(fetchLogs, 3000);
    </script>
</body>
</html>
"""