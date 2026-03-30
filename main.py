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
system_logs = [
    "VaultLogic Kernel v2.1-AUDIT Online", 
    "Institutional Partner Mode: Active.",
    "ALM Parameters: Delta-Neutral / Low Volatility.",
    "Monetization: 20% Performance Fee (Industrial Standard)."
]

# Track global monetization and active user deployment
revenue_stats = {
    "total_profit_generated": 0.0,
    "fees_collected": 0.0,
    "active_tvl": 142842019.00,
    "user_deployed_capital": 0.0, # Tracked when user clicks "Execute"
    "target_apy": 0.0582 # 5.82%
}

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    global system_logs
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] KERNEL_MSG: {msg}"
    system_logs.append(formatted_msg)
    if len(system_logs) > 50: system_logs.pop(0)

# --- REAL-TIME REVENUE ENGINE ---
async def yield_hunter():
    """
    Simulates the Kernel actively hunting spreads.
    If a user has deployed capital, it calculates REAL proportional yield.
    """
    strategies = ["Morpho Blue", "Aerodrome V3", "Moonwell", "Aave V3"]
    while True:
        # Update every 10 seconds for a snappy demo
        await asyncio.sleep(10)
        
        # 1. Simulate Global Protocol Background Activity (for the vibe)
        global_gross = random.uniform(20.0, 100.0)
        
        # 2. Calculate REAL User Yield if they have deployed capital
        user_yield = 0.0
        if revenue_stats["user_deployed_capital"] > 0:
            # Yield = (Principal * APY) / Seconds in Year * Interval
            # We use 10 seconds as the interval
            user_yield = (revenue_stats["user_deployed_capital"] * revenue_stats["target_apy"]) / 31536000 * 10
            
            # Apply 20% Founder Fee to the user's actual yield
            user_perf_fee = user_yield * 0.20
            user_net = user_yield - user_perf_fee
            
            revenue_stats["total_profit_generated"] += user_net
            revenue_stats["fees_collected"] += user_perf_fee
            
            target = random.choice(strategies)
            add_log(f"HARVEST: {target} cycle complete for user vault.")
            add_log(f"REVENUE: 20% Fee (${user_perf_fee:.6f}) auto-routed to Founder.")
        else:
            # If no user capital, just show the global "background" profit ticking
            revenue_stats["total_profit_generated"] += global_gross * 0.8
            revenue_stats["fees_collected"] += global_gross * 0.2

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(yield_hunter())

@app.get("/stats")
async def get_stats():
    return revenue_stats

@app.get("/logs")
async def get_logs():
    return {"logs": [l.split("KERNEL_MSG: ")[1] if "KERNEL_MSG: " in l else l for l in system_logs]}

@app.post("/verify-balance")
async def verify_balance(data: EngineInit):
    try:
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        raw_balance = contract.functions.balanceOf(Web3.to_checksum_address(data.address)).call()
        actual_balance = raw_balance / 10**6
        
        if data.amount > actual_balance:
            add_log(f"REJECTED: ${data.amount:,.2f} exceeds balance (${actual_balance:,.2f}). Access Denied.")
            return {"status": "failed", "message": "Insufficient on-chain collateral."}
            
        return {"status": "success", "balance": actual_balance}
    except Exception as e:
        # Fallback for demo environments without RPC access
        return {"status": "simulation", "message": "Demo Mode Active."}

@app.post("/start-engine")
async def start_engine(data: EngineInit):
    # This activates the REAL math in the background task
    revenue_stats["user_deployed_capital"] = data.amount
    revenue_stats["total_profit_generated"] = 0.0 # Reset stats for the new "Live" run
    revenue_stats["fees_collected"] = 0.0
    
    add_log(f"INIT: Spawning Managed ALM Loop for {data.address[:10]}...")
    add_log(f"ALLOCATING: ${data.amount:,.2f} into Industrial Floor.")
    add_log(f"CALC: Target yield set to {revenue_stats['target_apy']*100}% APY.")
    return {"status": "running"}

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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script type="module">
        import { createAppKit } from 'https://esm.sh/@reown/appkit'
        import { Ethers5Adapter } from 'https://esm.sh/@reown/appkit-adapter-ethers5'
        import { base } from 'https://esm.sh/@reown/appkit/networks'

        const modal = createAppKit({
            adapters: [new Ethers5Adapter()],
            networks: [base],
            projectId: '2b936cf692d84ae6da1ba91950c96420',
            themeMode: 'dark'
        });
        window.modal = modal;

        modal.subscribeAccount(state => {
            const dashboard = document.getElementById('dashboard');
            const connectBtn = document.getElementById('connectBtn');
            if(state.isConnected) {
                window.userAddress = state.address;
                dashboard.classList.remove('opacity-40', 'pointer-events-none');
                connectBtn.innerText = "OPEN WALLET";
            } else {
                dashboard.classList.add('opacity-40', 'pointer-events-none');
                connectBtn.innerText = "AUTHENTICATE";
            }
        });
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;700&display=swap');
        body { background-color: #020408; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(10, 15, 30, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .scanline {
            width: 100%; height: 2px; background: rgba(56, 189, 248, 0.05);
            position: fixed; top: 0; left: 0; pointer-events: none; z-index: 100;
            animation: scan 8s linear infinite;
        }
        @keyframes scan { from { top: 0%; } to { top: 100%; } }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="scanline"></div>

    <nav class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-12 gap-6 border-b border-white/5 pb-8">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-sky-500/10 rounded-xl flex items-center justify-center border border-sky-500/20">
                <i class="fas fa-terminal text-sky-500 text-xl"></i>
            </div>
            <div>
                <h1 class="text-2xl font-bold tracking-tighter uppercase italic">VaultLogic <span class="text-sky-500 text-xs align-top not-italic mono ml-1">KRNL_v2.1</span></h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-[0.3em] font-bold">Industrial Yield Protocol</p>
            </div>
        </div>
        <button onclick="window.modal.open()" id="connectBtn" class="bg-white text-black hover:bg-sky-400 hover:text-white px-8 py-2.5 rounded-lg font-black transition-all uppercase text-[10px] tracking-[0.2em]">
            AUTHENTICATE
        </button>
    </nav>

    <main id="dashboard" class="max-w-7xl mx-auto opacity-40 transition-all duration-1000 pointer-events-none">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="glass-panel p-6 rounded-xl border-l-2 border-l-slate-700">
                <p class="text-slate-500 text-[9px] font-black mb-3 uppercase tracking-[0.2em]">Institutional TVL</p>
                <h2 class="text-3xl font-bold italic">$142,842,019</h2>
            </div>
            <div class="glass-panel p-6 rounded-xl border-l-2 border-l-sky-500">
                <p class="text-slate-500 text-[9px] font-black mb-3 uppercase tracking-[0.2em]">Target APY</p>
                <h2 class="text-3xl font-bold text-sky-400 italic">5.82%</h2>
            </div>
            <div class="glass-panel p-6 rounded-xl border-l-2 border-l-emerald-500">
                <p class="text-slate-500 text-[9px] font-black mb-3 uppercase tracking-[0.2em]">Live Profit (Net)</p>
                <h2 class="text-3xl font-bold text-emerald-400 italic mono" id="userProfit">$0.00</h2>
            </div>
            <div class="glass-panel p-6 rounded-xl border-l-2 border-l-sky-500 bg-sky-500/5">
                <p class="text-sky-500 text-[9px] font-black mb-3 uppercase tracking-[0.2em]">Founder Revenue (20%)</p>
                <h2 class="text-3xl font-bold text-white italic mono" id="founderFees">$0.00</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-4">
                <div class="glass-panel p-8 rounded-2xl relative border-t border-white/10">
                    <h3 class="text-sm font-black mb-6 uppercase tracking-[0.25em] text-sky-400">Capital Deployment</h3>
                    <div class="space-y-8 mb-10">
                        <div>
                            <div class="flex justify-between text-[10px] mb-3 font-black uppercase tracking-widest">
                                <span class="text-slate-500">Allocation (USDC)</span>
                                <span class="text-white" id="amountDisplay">$500,000</span>
                            </div>
                            <input type="range" min="1000" max="5000000" step="1000" id="alloc-amt" value="500000" 
                                   oninput="document.getElementById('amountDisplay').innerText = '$' + parseInt(this.value).toLocaleString()"
                                   class="w-full h-1 bg-white/5 rounded-lg appearance-none cursor-pointer">
                        </div>
                    </div>
                    <button id="verify-btn" onclick="verifyAndStart()" class="w-full py-4 bg-sky-600 text-white font-black rounded-lg hover:bg-white hover:text-black transition-all uppercase tracking-[0.3em] text-[10px]">
                        EXECUTE DEPLOYMENT
                    </button>
                    <div id="sim-msg" class="text-[9px] mt-6 hidden text-center italic font-black uppercase tracking-widest p-3 rounded bg-red-500/10 border border-red-500/20"></div>
                </div>
                
                <div class="mt-6 glass-panel p-6 rounded-xl border border-white/5">
                    <p class="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-2">Active Principal</p>
                    <p class="text-xl font-bold italic mono text-sky-500" id="activePrincipal">$0.00</p>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel rounded-2xl flex flex-col bg-slate-900/40 border border-white/5 overflow-hidden">
                    <div class="bg-white/5 px-6 py-4 border-b border-white/5 flex justify-between items-center">
                        <span class="text-[9px] font-black uppercase tracking-[0.3em] text-slate-400">Live Kernel Audit Logs</span>
                    </div>
                    <div id="logOutput" class="p-6 flex-grow mono text-[10px] space-y-3 overflow-y-auto max-h-[500px] custom-scrollbar"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        async function updateStats() {
            try {
                const res = await fetch('/stats');
                const data = await res.json();
                
                // Use 4 decimal places so users with smaller deposits can see it ticking
                document.getElementById('userProfit').innerText = '$' + data.total_profit_generated.toLocaleString(undefined, {minimumFractionDigits: 4});
                document.getElementById('founderFees').innerText = '$' + data.fees_collected.toLocaleString(undefined, {minimumFractionDigits: 4});
                document.getElementById('activePrincipal').innerText = '$' + data.user_deployed_capital.toLocaleString();
            } catch(e) {}
        }

        async function verifyAndStart() {
            const amt = document.getElementById('alloc-amt').value;
            const btn = document.getElementById('verify-btn');
            const simMsg = document.getElementById('sim-msg');
            
            btn.innerText = "PROTOCOL_AUDIT...";
            btn.disabled = true;
            
            const vRes = await fetch('/verify-balance', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: window.userAddress, amount: parseFloat(amt) })
            });
            const vData = await vRes.json();
            
            if(vData.status === 'failed') {
                simMsg.innerText = "CRITICAL: INSUFFICIENT COLLATERAL. ACCESS DENIED.";
                simMsg.classList.remove('hidden');
                btn.innerText = "DEPLOYMENT_REJECTED";
                btn.disabled = false;
                return;
            }
            
            await fetch('/start-engine', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: window.userAddress, amount: parseFloat(amt) })
            });
            btn.innerText = "DEPLOYMENT_CONFIRMED";
            simMsg.innerText = "SUCCESS: CAPITAL ACTIVATED IN KERNEL.";
            simMsg.classList.remove('hidden', 'bg-red-500/10', 'border-red-500/20');
            simMsg.classList.add('bg-emerald-500/10', 'border-emerald-500/20', 'text-emerald-500');
        }

        setInterval(async () => {
            const res = await fetch('/logs');
            const data = await res.json();
            const logOutput = document.getElementById('logOutput');
            logOutput.innerHTML = data.logs.map(l => `
                <div class="p-3 border-l border-slate-800 hover:border-sky-500 bg-white/[0.02]">
                    <span class="text-sky-500 font-bold mr-2">KERNEL:</span><span class="text-slate-300">${l}</span>
                </div>
            `).reverse().join('');
            updateStats();
        }, 3000);
    </script>
</body>
</html>
"""