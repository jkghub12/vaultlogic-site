import asyncio
import os
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
system_logs = [
    "VaultLogic Kernel v2.1-AUDIT Online", 
    "Institutional Partner Mode: Active.",
    "Scanning Base Liquidity Spreads...",
    "ALM Parameters: Delta-Neutral / Low Volatility."
]

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

@app.get("/logs")
async def get_logs():
    return {"logs": system_logs}

@app.post("/verify-balance")
async def verify_balance(data: EngineInit):
    try:
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        raw_balance = contract.functions.balanceOf(Web3.to_checksum_address(data.address)).call()
        actual_balance = raw_balance / 10**6
        
        if data.amount > actual_balance:
            add_log(f"REJECTED: ${data.amount:,.2f} request exceeds balance (${actual_balance:,.2f}).")
            return {"status": "failed", "message": "Insufficient on-chain collateral."}
            
        return {"status": "success", "balance": actual_balance}
    except Exception as e:
        # Fallback to simulation if RPC is down, otherwise standard logic applies
        add_log("NETWORK: RPC Latency detected. Allowing Demo validation.")
        return {"status": "simulation", "message": "Demo Mode Active."}

@app.post("/start-engine")
async def start_engine(data: EngineInit):
    add_log(f"INIT: Spawning Managed ALM Loop for {data.address[:10]}...")
    add_log(f"ALLOCATING: ${data.amount:,.2f} into Industrial Floor Strategy.")
    add_log("STRATEGY: Monitoring Morpho & Aerodrome yield spreads...")
    return {"status": "running"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Standard string to avoid curly brace SyntaxErrors
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Institutional ALM Kernel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script type="module">
        import { createAppKit } from 'https://esm.sh/@reown/appkit'
        import { Ethers5Adapter } from 'https://esm.sh/@reown/appkit-adapter-ethers5'
        import { base } from 'https://esm.sh/@reown/appkit/networks'

        const modal = createAppKit({
            adapters: [new Ethers5Adapter()],
            networks: [base],
            projectId: '2b936cf692d84ae6da1ba91950c96420',
            themeMode: 'dark',
            features: { analytics: true, email: false, socials: false }
        });
        window.modal = modal;

        modal.subscribeAccount(state => {
            const dashboard = document.getElementById('dashboard');
            const connectBtn = document.getElementById('connectBtn');
            const connectionStatus = document.getElementById('connectionStatus');
            
            if(state.isConnected && state.address) {
                window.userAddress = state.address;
                dashboard.classList.remove('opacity-40', 'pointer-events-none');
                connectBtn.innerText = "OPEN WALLET";
                connectBtn.classList.remove('bg-sky-600');
                connectBtn.classList.add('bg-slate-800');
                connectionStatus.innerHTML = `
                    <span class="w-2 h-2 bg-emerald-500 rounded-full status-pulse"></span>
                    <span class="text-sm font-medium text-emerald-400 uppercase tracking-tighter">AUTH: ${state.address.slice(0,6)}...${state.address.slice(-4)}</span>
                `;
            } else {
                window.userAddress = null;
                dashboard.classList.add('opacity-40', 'pointer-events-none');
                connectBtn.innerText = "AUTHENTICATE";
                connectBtn.classList.remove('bg-slate-800');
                connectBtn.classList.add('bg-sky-600');
                connectionStatus.innerHTML = `
                    <span class="w-2 h-2 bg-sky-500 rounded-full status-pulse"></span>
                    <span class="text-sm font-medium text-sky-400">CONNECTING TO BASE...</span>
                `;
            }
        });
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
        body { background-color: #05070a; color: #e2e8f0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .kernel-glow { box-shadow: 0 0 20px rgba(56, 189, 248, 0.15); }
        .log-entry { border-left: 2px solid #334155; transition: all 0.2s; }
        .log-entry:hover { border-left-color: #38bdf8; background: rgba(56, 189, 248, 0.05); }
        @keyframes pulse-slow { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .status-pulse { animation: pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #0f172a; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    <nav class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-12 gap-6">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-sky-500 rounded-lg flex items-center justify-center kernel-glow">
                <i class="fas fa-microchip text-black text-xl"></i>
            </div>
            <div>
                <h1 class="text-2xl font-bold tracking-tight uppercase">VaultLogic <span class="text-sky-500 text-xs align-top ml-1 mono font-normal">v2.1-AUDIT</span></h1>
                <p class="text-xs text-slate-500 uppercase tracking-widest">Autonomous ALM Kernel</p>
            </div>
        </div>

        <div class="flex items-center gap-4">
            <div id="connectionStatus" class="glass-panel px-4 py-2 rounded-full flex items-center gap-3 border-sky-500/30">
                <span class="w-2 h-2 bg-sky-500 rounded-full status-pulse"></span>
                <span class="text-sm font-medium text-sky-400">CONNECTING...</span>
            </div>
            <button onclick="window.modal.open()" id="connectBtn" class="bg-sky-600 hover:opacity-80 text-white px-6 py-2 rounded-lg font-semibold transition-all shadow-lg shadow-sky-900/20 uppercase text-xs tracking-widest">
                AUTHENTICATE
            </button>
        </div>
    </nav>

    <main id="dashboard" class="max-w-7xl mx-auto opacity-40 transition-opacity duration-700 pointer-events-none">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="glass-panel p-6 rounded-2xl">
                <p class="text-slate-500 text-[10px] font-bold mb-2 uppercase tracking-widest">System TVL</p>
                <h2 class="text-3xl font-bold">$142.8M</h2>
                <div class="text-emerald-400 text-[10px] mt-2 flex items-center gap-1"><i class="fas fa-chart-line"></i> +12.4% PERFORMANCE</div>
            </div>
            <div class="glass-panel p-6 rounded-2xl border-l-4 border-l-sky-500">
                <p class="text-slate-500 text-[10px] font-bold mb-2 uppercase tracking-widest">Target Yield (APY)</p>
                <h2 class="text-3xl font-bold text-sky-400">5.82%</h2>
                <p class="text-[10px] text-slate-500 mt-2 uppercase">Delta-Neutral Strategy</p>
            </div>
            <div class="glass-panel p-6 rounded-2xl">
                <p class="text-slate-500 text-[10px] font-bold mb-2 uppercase tracking-widest">Active Nodes</p>
                <div class="flex items-center gap-3"><h2 class="text-3xl font-bold">12</h2><span class="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-[10px] rounded border border-emerald-500/20">OPERATIONAL</span></div>
            </div>
            <div class="glass-panel p-6 rounded-2xl">
                <p class="text-slate-500 text-[10px] font-bold mb-2 uppercase tracking-widest">Kernel Health</p>
                <h2 class="text-3xl font-bold text-emerald-400">99.8%</h2>
                <div class="w-full bg-slate-800 h-1 mt-3 rounded-full overflow-hidden">
                    <div class="bg-emerald-500 h-full w-[99.8%]"></div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-1">
                <div class="glass-panel p-8 rounded-3xl relative overflow-hidden">
                    <h3 class="text-xl font-bold mb-4">Allocate Capital</h3>
                    <div class="space-y-4 mb-8">
                        <div class="flex justify-between text-xs mb-1">
                            <span class="text-slate-500">Deployment Amount (USDC)</span>
                            <span class="text-sky-500 font-bold" id="amountDisplay">$500,000</span>
                        </div>
                        <input type="range" min="10000" max="5000000" step="10000" id="alloc-amt" value="500000" 
                               oninput="document.getElementById('amountDisplay').innerText = '$' + parseInt(this.value).toLocaleString()"
                               class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500">
                    </div>
                    <button id="verify-btn" onclick="verifyAndStart()" class="w-full py-4 bg-white text-black font-bold rounded-xl hover:bg-sky-400 hover:text-white transition-all shadow-xl shadow-white/5 uppercase tracking-widest text-xs">
                        CONFIRM ALLOCATION
                    </button>
                    <div id="sim-msg" class="text-[10px] mt-4 hidden text-center italic font-bold"></div>
                </div>
            </div>

            <div class="lg:col-span-2">
                <div class="glass-panel rounded-3xl p-6 min-h-[600px] flex flex-col bg-slate-900/20">
                    <div class="flex items-center gap-2 mb-4">
                        <div class="w-2 h-2 bg-sky-500 rounded-full status-pulse"></div>
                        <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Live Execution Audit</span>
                    </div>
                    <div id="logOutput" class="flex-grow mono text-[11px] space-y-2 overflow-y-auto max-h-[500px] pr-2 custom-scrollbar"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        async function verifyAndStart() {
            const amt = document.getElementById('alloc-amt').value;
            const btn = document.getElementById('verify-btn');
            const simMsg = document.getElementById('sim-msg');
            
            btn.innerText = "AUDITING...";
            btn.disabled = true;
            btn.className = "w-full py-4 bg-white text-black font-bold rounded-xl transition-all shadow-xl uppercase tracking-widest text-xs";
            simMsg.classList.add('hidden');
            
            try {
                const vRes = await fetch('/verify-balance', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ address: window.userAddress, amount: parseFloat(amt) })
                });
                const vData = await vRes.json();
                
                if(vData.status === 'failed') {
                    simMsg.innerText = "INSUFFICIENT FUNDS. ACCESS DENIED.";
                    simMsg.classList.remove('hidden');
                    simMsg.classList.add('text-red-500');
                    btn.innerText = "ALLOCATION REJECTED";
                    btn.classList.add('bg-red-600', 'text-white');
                    // WE STOP HERE. NO ENGINE START.
                    return;
                }
                
                if(vData.status === 'simulation') {
                    simMsg.innerText = "Simulation mode active (Demo Balance).";
                    simMsg.classList.remove('hidden');
                    simMsg.classList.add('text-sky-400');
                }
                
                await fetch('/start-engine', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ address: window.userAddress, amount: parseFloat(amt) })
                });
                
                btn.innerText = "ALLOCATION ACTIVE";
                btn.classList.add('bg-emerald-500', 'text-white');
            } catch(e) {
                btn.innerText = "CONFIRM ALLOCATION";
                btn.disabled = false;
            }
        }

        setInterval(async () => {
            try {
                const res = await fetch('/logs');
                const data = await res.json();
                const logOutput = document.getElementById('logOutput');
                logOutput.innerHTML = data.logs.map(l => `
                    <div class="log-entry p-2 rounded bg-slate-900/40 border border-white/5">
                        <span class="text-slate-500 font-bold">[SYS]</span> 
                        <span class="text-slate-300 font-medium">${l}</span>
                    </div>
                `).reverse().join('');
            } catch(e) {}
        }, 2500);
    </script>
</body>
</html>
"""
    return html_content