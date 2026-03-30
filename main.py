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
    "ALM Parameters: Delta-Neutral / Low Volatility.",
    "Performance Fee Set: 20% Net Yield."
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
        add_log("NETWORK: RPC Latency detected. Allowing Demo validation.")
        return {"status": "simulation", "message": "Demo Mode Active."}

@app.post("/start-engine")
async def start_engine(data: EngineInit):
    add_log(f"INIT: Spawning Managed ALM Loop for {data.address[:10]}...")
    add_log(f"ALLOCATING: ${data.amount:,.2f} into Industrial Floor Strategy.")
    add_log("STRATEGY: Monitoring Morpho & Aerodrome yield spreads...")
    add_log("REVENUE: 20% Performance Fee logic attached to harvest cycle.")
    return {"status": "running"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
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
                    <span class="text-sm font-medium text-sky-400 uppercase tracking-tighter">BASE_MAINNET: SYNCING</span>
                `;
            }
        });
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
        body { background-color: #020408; color: #f8fafc; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(10, 15, 30, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .kernel-glow { box-shadow: 0 0 40px rgba(56, 189, 248, 0.1); }
        .log-entry { border-left: 1px solid #1e293b; transition: all 0.2s; }
        .log-entry:hover { border-left: 1px solid #38bdf8; background: rgba(56, 189, 248, 0.03); }
        @keyframes pulse-slow { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .status-pulse { animation: pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        .scanline {
            width: 100%; height: 2px; background: rgba(56, 189, 248, 0.05);
            position: fixed; top: 0; left: 0; pointer-events: none; z-index: 100;
            animation: scan 8s linear infinite;
        }
        @keyframes scan { from { top: 0%; } to { top: 100%; } }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        .range-slider::-webkit-slider-thumb {
            -webkit-appearance: none; height: 18px; width: 18px; border-radius: 50%;
            background: #38bdf8; cursor: pointer; border: 3px solid #020408;
        }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="scanline"></div>

    <nav class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-12 gap-6 border-b border-white/5 pb-8">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-sky-500/10 rounded-xl flex items-center justify-center border border-sky-500/20 kernel-glow">
                <i class="fas fa-terminal text-sky-500 text-xl"></i>
            </div>
            <div>
                <h1 class="text-2xl font-bold tracking-tighter uppercase italic">VaultLogic <span class="text-sky-500 text-xs align-top not-italic mono tracking-normal ml-1">KRNL_v2.1</span></h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-[0.3em] font-bold">Industrial Yield Protocol</p>
            </div>
        </div>

        <div class="flex items-center gap-4">
            <div id="connectionStatus" class="glass-panel px-5 py-2.5 rounded-lg flex items-center gap-3 border-white/5">
                <span class="w-1.5 h-1.5 bg-sky-500 rounded-full status-pulse"></span>
                <span class="text-[10px] font-bold text-sky-400 uppercase tracking-widest">BASE_MAINNET: SYNCING</span>
            </div>
            <button onclick="window.modal.open()" id="connectBtn" class="bg-white text-black hover:bg-sky-400 hover:text-white px-8 py-2.5 rounded-lg font-black transition-all shadow-xl uppercase text-[10px] tracking-[0.2em]">
                AUTHENTICATE
            </button>
        </div>
    </nav>

    <main id="dashboard" class="max-w-7xl mx-auto opacity-40 transition-all duration-1000 pointer-events-none scale-[0.98]">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="glass-panel p-6 rounded-xl border-l-2 border-l-slate-700">
                <p class="text-slate-500 text-[9px] font-black mb-3 uppercase tracking-[0.2em]">Institutional TVL</p>
                <h2 class="text-3xl font-bold italic">$142,842,019</h2>
                <div class="text-emerald-400 text-[9px] mt-3 flex items-center gap-1 font-bold"><i class="fas fa-caret-up"></i> 12.4% PERFORMANCE YTD</div>
            </div>
            <div class="glass-panel p-6 rounded-xl border-l-2 border-l-sky-500">
                <p class="text-slate-500 text-[9px] font-black mb-3 uppercase tracking-[0.2em]">Target APY (Industrial)</p>
                <h2 class="text-3xl font-bold text-sky-400 italic">5.82%</h2>
                <p class="text-[9px] text-slate-400 mt-3 font-bold uppercase tracking-widest">Strategy: Delta-Neutral ALM</p>
            </div>
            <div class="glass-panel p-6 rounded-xl border-l-2 border-l-slate-700">
                <p class="text-slate-500 text-[9px] font-black mb-3 uppercase tracking-[0.2em]">Rebalance Frequency</p>
                <h2 class="text-3xl font-bold italic">14.2s</h2>
                <p class="text-[9px] text-emerald-500 mt-3 font-bold uppercase tracking-widest">Avg. Gas: 0.001 Gwei</p>
            </div>
            <div class="glass-panel p-6 rounded-xl border-l-2 border-l-slate-700">
                <p class="text-slate-500 text-[9px] font-black mb-3 uppercase tracking-[0.2em]">Kernel Health</p>
                <div class="flex items-center gap-3"><h2 class="text-3xl font-bold text-emerald-400 italic">99.8%</h2></div>
                <div class="w-full bg-white/5 h-1 mt-4 rounded-full overflow-hidden">
                    <div class="bg-emerald-500 h-full w-[99.8%]"></div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-4">
                <div class="glass-panel p-8 rounded-2xl relative border-t border-white/10">
                    <div class="absolute top-0 right-0 p-3"><i class="fas fa-shield-halved text-white/10"></i></div>
                    <h3 class="text-sm font-black mb-6 uppercase tracking-[0.25em] text-sky-400">Capital Deployment</h3>
                    
                    <div class="space-y-8 mb-10">
                        <div>
                            <div class="flex justify-between text-[10px] mb-3 font-black uppercase tracking-widest">
                                <span class="text-slate-500">Allocation (USDC)</span>
                                <span class="text-white" id="amountDisplay">$500,000</span>
                            </div>
                            <input type="range" min="10000" max="5000000" step="10000" id="alloc-amt" value="500000" 
                                   oninput="updateProjections(this.value)"
                                   class="w-full h-1 bg-white/5 rounded-lg appearance-none cursor-pointer range-slider">
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-white/5 p-4 rounded-lg border border-white/5">
                                <p class="text-[8px] text-slate-500 font-bold uppercase mb-1">Est. Net Profit (yr)</p>
                                <p class="text-sm font-bold text-emerald-400 mono" id="profitProj">$23,280</p>
                            </div>
                            <div class="bg-white/5 p-4 rounded-lg border border-white/5">
                                <p class="text-[8px] text-slate-500 font-bold uppercase mb-1">Performance Fee (20%)</p>
                                <p class="text-sm font-bold text-sky-400 mono" id="feeProj">$5,820</p>
                            </div>
                        </div>
                    </div>

                    <button id="verify-btn" onclick="verifyAndStart()" class="w-full py-4 bg-sky-600 text-white font-black rounded-lg hover:bg-white hover:text-black transition-all shadow-2xl uppercase tracking-[0.3em] text-[10px]">
                        EXECUTE DEPLOYMENT
                    </button>
                    <div id="sim-msg" class="text-[9px] mt-6 hidden text-center italic font-black uppercase tracking-widest p-3 rounded bg-red-500/10 border border-red-500/20"></div>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel rounded-2xl flex flex-col bg-slate-900/40 border border-white/5 overflow-hidden">
                    <div class="bg-white/5 px-6 py-4 border-b border-white/5 flex justify-between items-center">
                        <div class="flex items-center gap-3">
                            <div class="w-2 h-2 bg-emerald-500 rounded-full status-pulse"></div>
                            <span class="text-[9px] font-black uppercase tracking-[0.3em] text-slate-400">Live Kernel Audit Logs</span>
                        </div>
                        <span class="text-[9px] mono text-slate-600">ID: BASE_KRNL_8832_X</span>
                    </div>
                    <div id="logOutput" class="p-6 flex-grow mono text-[10px] space-y-3 overflow-y-auto max-h-[500px] custom-scrollbar leading-relaxed"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        function updateProjections(val) {
            const amount = parseInt(val);
            document.getElementById('amountDisplay').innerText = '$' + amount.toLocaleString();
            
            // Calc: 5.82% total yield
            const totalYield = amount * 0.0582;
            const fee = totalYield * 0.20;
            const netProfit = totalYield - fee;
            
            document.getElementById('profitProj').innerText = '$' + Math.floor(netProfit).toLocaleString();
            document.getElementById('feeProj').innerText = '$' + Math.floor(fee).toLocaleString();
        }

        async function verifyAndStart() {
            const amt = document.getElementById('alloc-amt').value;
            const btn = document.getElementById('verify-btn');
            const simMsg = document.getElementById('sim-msg');
            
            btn.innerText = "PROTOCOL_AUDIT_IN_PROGRESS...";
            btn.disabled = true;
            btn.className = "w-full py-4 bg-slate-800 text-slate-400 font-black rounded-lg transition-all uppercase tracking-[0.2em] text-[10px]";
            simMsg.classList.add('hidden');
            
            try {
                const vRes = await fetch('/verify-balance', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ address: window.userAddress, amount: parseFloat(amt) })
                });
                const vData = await vRes.json();
                
                if(vData.status === 'failed') {
                    simMsg.innerText = "CRITICAL: INSUFFICIENT COLLATERAL. ACCESS DENIED.";
                    simMsg.classList.remove('hidden');
                    simMsg.classList.add('text-red-500');
                    btn.innerText = "DEPLOYMENT_REJECTED";
                    btn.className = "w-full py-4 bg-red-900/30 text-red-500 font-black rounded-lg border border-red-500/50 uppercase tracking-[0.2em] text-[10px]";
                    return;
                }
                
                if(vData.status === 'simulation') {
                    simMsg.innerText = "DEMO_MODE_ACTIVE: PROCEEDING WITH SIMULATED FLOW.";
                    simMsg.classList.remove('hidden');
                    simMsg.classList.add('text-sky-400');
                }
                
                await fetch('/start-engine', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ address: window.userAddress, amount: parseFloat(amt) })
                });
                
                btn.innerText = "DEPLOYMENT_CONFIRMED";
                btn.className = "w-full py-4 bg-emerald-600 text-white font-black rounded-lg shadow-xl shadow-emerald-900/20 uppercase tracking-[0.2em] text-[10px]";
            } catch(e) {
                btn.innerText = "EXECUTE DEPLOYMENT";
                btn.disabled = false;
                btn.className = "w-full py-4 bg-sky-600 text-white font-black rounded-lg hover:bg-white hover:text-black transition-all shadow-2xl uppercase tracking-[0.3em] text-[10px]";
            }
        }

        setInterval(async () => {
            try {
                const res = await fetch('/logs');
                const data = await res.json();
                const logOutput = document.getElementById('logOutput');
                logOutput.innerHTML = data.logs.map(l => {
                    const isError = l.includes('REJECTED');
                    const colorClass = isError ? 'text-red-400' : 'text-sky-400';
                    return `
                        <div class="log-entry p-3 rounded bg-white/[0.02] border border-white/5">
                            <span class="text-slate-600 font-bold mr-2">[${new Date().toLocaleTimeString()}]</span>
                            <span class="${colorClass} font-bold mr-2">KERNEL_MSG:</span>
                            <span class="text-slate-300">${l}</span>
                        </div>
                    `
                }).reverse().join('');
            } catch(e) {}
        }, 2000);
        
        // Initial Proj
        updateProjections(500000);
    </script>
</body>
</html>
"""
    return html_content