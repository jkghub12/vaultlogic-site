import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3
from engine import kernel # Importing our Kernel logic

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
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def background_kernel_loop():
    """Ticking the engine every 10 seconds for all active users."""
    while True:
        await asyncio.sleep(10)
        for addr in list(kernel.active_deployments.keys()):
            update_msg = kernel.active_deployments[addr].calculate_tick(10)
            if update_msg:
                add_log(update_msg)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str):
    stats = kernel.get_stats(address)
    return {
        "stats": stats,
        "logs": audit_logs
    }

@app.post("/activate")
async def activate_deployment(data: EngineInit):
    # 1. INSTITUTIONAL FLOOR CHECK
    if data.amount < 10000:
        add_log(f"REJECTED: ${data.amount:,.2f} is below $10k Floor.")
        return {"status": "error", "message": "Below Institutional Floor"}
    
    # 2. ON-CHAIN COLLATERAL CHECK
    try:
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(data.address)).call() / 1e6
        
        if balance < data.amount:
            add_log(f"CRITICAL: Insufficient Collateral for {data.address[:8]}. Required: ${data.amount:,.2f} | Found: ${balance:,.2f}")
            return {"status": "error", "message": "Insufficient On-Chain Collateral"}
            
    except Exception as e:
        return {"status": "error", "message": "RPC_VERIFICATION_FAILED"}

    # 3. INITIALIZE ENGINE
    msg = kernel.deploy(data.address, data.amount)
    add_log(msg)
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def home():
    # Note: Frontend now dynamically fetches stats based on connected wallet
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
        body { background-color: #05070a; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .status-pulse { animation: pulse 2s infinite; }
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
                <p class="text-[10px] text-slate-500 uppercase tracking-[0.4em] font-black">Industrial Yield Engine</p>
            </div>
        </div>
        <div class="flex items-center gap-6">
            <div id="connectionStatus" class="flex items-center gap-3 glass-panel px-5 py-2.5 rounded-full border-slate-500/20">
                <span class="w-2 h-2 bg-slate-500 rounded-full"></span>
                <span id="statusText" class="text-[10px] font-black text-slate-500 tracking-widest uppercase">Kernel_Locked</span>
            </div>
            <button onclick="connectWallet()" id="authBtn" class="bg-white text-black hover:bg-sky-500 hover:text-white px-10 py-3 rounded-lg font-black transition-all uppercase text-[10px] tracking-[0.2em]">
                AUTHENTICATE
            </button>
        </div>
    </nav>

    <main id="dashboard" class="max-w-7xl mx-auto opacity-20 transition-all duration-1000 pointer-events-none">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-sky-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Active Principal</p>
                <h2 class="text-4xl font-bold italic mono" id="principalDisplay">$0.00</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-emerald-500">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Net Profit (User 80%)</p>
                <h2 class="text-4xl font-bold text-emerald-400 italic mono" id="liveProfit">$0.0000</h2>
            </div>
            <div class="glass-panel p-8 rounded-3xl border-l-2 border-l-white/20">
                <p class="text-slate-500 text-[10px] font-black mb-3 uppercase tracking-widest">Global APY</p>
                <h2 class="text-4xl font-bold text-white italic mono">5.82%</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div class="lg:col-span-4 space-y-8">
                <div class="glass-panel p-10 rounded-[2.5rem] relative overflow-hidden border-t border-white/10">
                    <h3 class="text-[11px] font-black mb-8 uppercase tracking-[0.3em] text-sky-400 text-center">Capital Controller</h3>
                    <div class="space-y-8 mb-12">
                        <div>
                            <div class="flex justify-between text-[10px] mb-4 font-black uppercase tracking-widest">
                                <span class="text-slate-400">Target Allocation</span>
                                <span class="text-white font-bold" id="amountDisplay">$10,000</span>
                            </div>
                            <input type="range" min="10000" max="1000000" step="10000" value="10000" id="depositInput"
                                   oninput="document.getElementById('amountDisplay').innerText = '$' + parseInt(this.value).toLocaleString()"
                                   class="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-white">
                        </div>
                    </div>
                    <button id="executeBtn" onclick="executeDeployment()" class="w-full py-5 bg-sky-600 text-white font-black rounded-xl hover:bg-white hover:text-black transition-all uppercase tracking-[0.4em] text-[10px]">
                        EXECUTE DEPLOYMENT
                    </button>
                    <p id="txStatus" class="text-[10px] mt-8 hidden text-center italic font-black uppercase tracking-widest p-4 rounded-xl"></p>
                </div>
                
                <div class="glass-panel p-8 rounded-3xl border border-white/5">
                    <p class="text-[10px] text-slate-500 font-bold uppercase tracking-[0.3em] mb-6">Current Risk Allocation</p>
                    <div class="space-y-4">
                        <div>
                            <div class="flex justify-between text-[10px] mb-2 uppercase font-black">
                                <span class="text-slate-400">Lending (Low Risk)</span>
                                <span id="lendingPerc">70%</span>
                            </div>
                            <div class="w-full bg-slate-800 h-1 rounded-full"><div id="lendingBar" class="bg-sky-500 h-1 rounded-full transition-all duration-1000" style="width: 70%"></div></div>
                        </div>
                        <div>
                            <div class="flex justify-between text-[10px] mb-2 uppercase font-black">
                                <span class="text-slate-400">Liquidity (Active LP)</span>
                                <span id="lpPerc">30%</span>
                            </div>
                            <div class="w-full bg-slate-800 h-1 rounded-full"><div id="lpBar" class="bg-emerald-500 h-1 rounded-full transition-all duration-1000" style="width: 30%"></div></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel rounded-[2.5rem] p-10 min-h-[550px] flex flex-col bg-slate-900/20">
                    <div class="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
                        <h3 class="font-black uppercase tracking-[0.4em] text-[10px] text-slate-500">Live Infrastructure Audit</h3>
                        <div class="flex gap-2">
                            <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full status-pulse"></span>
                        </div>
                    </div>
                    <div id="logOutput" class="flex-grow mono text-[11px] space-y-4 overflow-y-auto max-h-[400px] custom-scrollbar"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let userAddress = null;

        async function connectWallet() {
            if (window.ethereum) {
                const provider = new ethers.providers.Web3Provider(window.ethereum);
                await provider.send("eth_requestAccounts", []);
                userAddress = await provider.getSigner().getAddress();
                
                document.getElementById('dashboard').classList.remove('opacity-20', 'pointer-events-none');
                document.getElementById('authBtn').innerText = "DISCONNECT";
                document.getElementById('connectionStatus').querySelector('span:first-child').classList.replace('bg-slate-500', 'bg-emerald-500');
                document.getElementById('statusText').innerText = `AUTH: ${userAddress.substring(0,6)}...`;
                
                startSync();
            }
        }

        async function executeDeployment() {
            const amount = document.getElementById('depositInput').value;
            const btn = document.getElementById('executeBtn');
            const status = document.getElementById('txStatus');
            
            btn.disabled = true;
            status.classList.remove('hidden');
            status.className = "text-[10px] mt-8 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-sky-500/10 text-sky-400";
            status.innerText = "VERIFYING ON-CHAIN COLLATERAL...";

            const res = await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: userAddress, amount: parseFloat(amount) })
            });
            const result = await res.json();
            
            if (result.status === "success") {
                btn.innerText = "DEPLOYMENT_ACTIVE";
                status.innerText = "SUCCESS: INDUSTRIAL KERNEL ENGAGED.";
            } else {
                btn.disabled = false;
                status.className = "text-[10px] mt-8 text-center italic font-black uppercase tracking-widest p-4 rounded-xl bg-red-500/10 text-red-400";
                status.innerText = "CRITICAL: " + result.message;
            }
        }

        function startSync() {
            setInterval(async () => {
                if (!userAddress) return;
                const res = await fetch('/stats/' + userAddress);
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
                    <div class="p-4 border-l-2 ${l.includes('CRITICAL') ? 'border-red-500 bg-red-500/5' : 'border-slate-800 bg-white/[0.02]'}">
                        <span class="text-sky-500 font-bold uppercase mr-3">KERNEL:</span>
                        <span class="${l.includes('CRITICAL') ? 'text-red-400' : 'text-slate-300'} uppercase">${l.split('KERNEL: ')[1] || l}</span>
                    </div>
                `).reverse().join('');
            }, 3000);
        }
    </script>
</body>
</html>
"""