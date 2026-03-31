import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3
from engine import kernel
import uvicorn
from datetime import datetime

app = FastAPI()

# --- CONFIG ---
BASE_RPC_URL = "https://mainnet.base.org"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
ERC20_ABI = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]

# --- DEBUG SETTINGS ---
DEBUG_BYPASS = True  # Set to False for Production On-Chain Verification
INSTITUTIONAL_FLOOR = 10000

audit_logs = ["VaultLogic v3.5-PROD: System Secure. Awaiting Authentication..."]

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def background_worker():
    while True:
        await asyncio.sleep(10)
        for addr in list(kernel.active_deployments.keys()):
            msg = kernel.active_deployments[addr].calculate_tick(10)
            if msg: add_log(msg)

@app.on_event("startup")
async def startup():
    asyncio.create_task(background_worker())

@app.get("/stats/{address}")
async def get_stats(address: str):
    return {"stats": kernel.get_stats(address), "logs": audit_logs}

@app.post("/activate")
async def activate(data: EngineInit):
    # 1. Floor Check (Bypassed if DEBUG_BYPASS is True)
    if not DEBUG_BYPASS and data.amount < INSTITUTIONAL_FLOOR:
        add_log(f"CRITICAL: REJECTED. ${data.amount:,.2f} is below $10k Floor.")
        return {"status": "error", "message": "Below Institutional Floor"}

    # 2. On-Chain Balance Verification
    if not DEBUG_BYPASS:
        try:
            w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
            usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
            balance = usdc.functions.balanceOf(Web3.to_checksum_address(data.address)).call() / 1e6
            
            if balance < data.amount:
                add_log(f"CRITICAL: REJECTED. Found ${balance:,.2f} USDC in wallet. Required: ${data.amount:,.2f}")
                return {"status": "error", "message": "Insufficient On-Chain Funds"}
        except Exception as e:
            add_log(f"ERROR: RPC Verification Failed.")
            return {"status": "error", "message": "Verification Failed"}
    else:
        add_log(f"DEBUG: Skipping balance check for {data.address[:8]}... (Simulated Deployment)")

    msg = kernel.deploy(data.address, data.amount, BASE_RPC_URL)
    add_log(msg)
    return {"status": "success"}

@app.post("/reset/{address}")
async def reset(address: str):
    if address in kernel.active_deployments:
        del kernel.active_deployments[address]
        add_log(f"SESSION_CLOSED: {address[:8]}... resources released.")
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>VaultLogic | Industrial ALM</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        body { background: #020305; color: #e2e8f0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .stat-card { background: #06080c; border: 1px solid rgba(255,255,255,0.03); border-radius: 24px; }
        input[type=range] { accent-color: #0891b2; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
    </style>
</head>
<body class="p-6 md:p-12">
    <header class="max-w-7xl mx-auto flex justify-between items-center mb-16">
        <div class="flex items-center gap-5">
            <div class="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-black font-black italic text-2xl shadow-[0_0_20px_rgba(255,255,255,0.1)]">V</div>
            <div>
                <h1 class="text-2xl font-black italic tracking-tighter uppercase leading-none">VaultLogic</h1>
                <p class="text-[9px] text-gray-600 font-bold uppercase tracking-[0.4em] mt-1">Autonomous Yield Engine</p>
            </div>
        </div>
        <button id="authBtn" onclick="toggleAuth()" class="bg-white text-black px-8 py-3 rounded-lg font-black text-[11px] tracking-widest uppercase hover:scale-105 transition-all">AUTHENTICATE</button>
    </header>

    <main id="dash" class="max-w-7xl mx-auto opacity-20 pointer-events-none transition-all duration-700">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div class="stat-card p-8 border-l-2 border-cyan-500">
                <p class="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4">Capital Deployed</p>
                <h2 id="principalDisp" class="text-5xl font-black italic tracking-tighter">$0</h2>
            </div>
            <div class="stat-card p-8 border-l-2 border-emerald-500">
                <p class="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4">Net Profit (80%)</p>
                <h2 id="profitDisp" class="text-5xl font-black text-emerald-400 italic tracking-tighter">$0.0000</h2>
            </div>
            <div class="stat-card p-8 border-l-2 border-purple-500">
                <p class="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4">Active Venue</p>
                <h2 id="venueDisp" class="text-4xl font-black text-white italic uppercase tracking-tighter">IDLE</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div class="lg:col-span-4 stat-card p-10">
                <h3 class="text-[11px] font-black uppercase tracking-[0.3em] text-cyan-500 mb-10">Deployment Settings</h3>
                <div class="space-y-10">
                    <div>
                        <div class="flex justify-between text-[11px] font-bold uppercase text-gray-500 mb-5">
                            <span>Target Amount</span>
                            <span id="amtVal" class="text-white">$10,000</span>
                        </div>
                        <input type="range" id="amtRange" min="1000" max="500000" step="1000" value="10000" class="w-full h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer" oninput="document.getElementById('amtVal').innerText = '$'+parseInt(this.value).toLocaleString()">
                    </div>
                    
                    <div class="space-y-6">
                        <div class="flex justify-between text-[10px] font-bold uppercase text-gray-600">
                            <span>Lending Allocation</span>
                            <span id="lPerc" class="text-cyan-400">100%</span>
                        </div>
                        <div class="h-1 bg-gray-900 overflow-hidden rounded-full"><div id="lBar" class="h-full bg-cyan-500 transition-all duration-1000" style="width:100%"></div></div>
                        
                        <div class="flex justify-between text-[10px] font-bold uppercase text-gray-600">
                            <span>Liquidity Allocation</span>
                            <span id="pPerc" class="text-purple-400">0%</span>
                        </div>
                        <div class="h-1 bg-gray-900 overflow-hidden rounded-full"><div id="pBar" class="h-full bg-purple-500 transition-all duration-1000" style="width:0%"></div></div>
                    </div>

                    <button id="execBtn" onclick="runKernel()" class="w-full py-5 bg-cyan-800 text-white font-black rounded-xl text-[11px] uppercase tracking-widest hover:bg-cyan-700 transition-all active:scale-95">Initialize Kernel</button>
                </div>
            </div>

            <div class="lg:col-span-8 stat-card p-10">
                <p class="text-[10px] font-black uppercase text-gray-600 mb-8 border-b border-white/5 pb-5 tracking-widest">Audit Terminal Output</p>
                <div id="logs" class="font-mono text-[11px] space-y-4 max-h-[400px] overflow-y-auto pr-4"></div>
            </div>
        </div>
    </main>

    <script>
        let wallet = null;
        let syncRef = null;

        async function toggleAuth() {
            if (!wallet) {
                if (!window.ethereum) {
                    alert("Please install MetaMask or a compatible Web3 wallet.");
                    return;
                }
                try {
                    // Force a fresh request to trigger wallet selection if needed
                    const accounts = await window.ethereum.request({ 
                        method: 'eth_requestAccounts' 
                    });
                    wallet = accounts[0];
                    document.getElementById('authBtn').innerText = "DISCONNECT [" + wallet.slice(0,6).toUpperCase() + "]";
                    document.getElementById('dash').classList.remove('opacity-20', 'pointer-events-none');
                    startSync();
                } catch (e) {
                    console.error("Auth failed", e);
                }
            } else {
                // Clear state
                await fetch('/reset/' + wallet, { method: 'POST' });
                wallet = null;
                clearInterval(syncRef);
                document.getElementById('authBtn').innerText = "AUTHENTICATE";
                document.getElementById('dash').classList.add('opacity-20', 'pointer-events-none');
                location.reload(); // Refresh to ensure wallet hooks reset
            }
        }

        async function runKernel() {
            const amount = document.getElementById('amtRange').value;
            const btn = document.getElementById('execBtn');
            
            btn.innerText = "VERIFYING...";
            btn.disabled = true;

            const res = await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: wallet, amount: parseFloat(amount) })
            });
            const data = await res.json();
            
            if (data.status === "success") {
                btn.innerText = "KERNEL ACTIVE";
                btn.classList.replace('bg-cyan-800', 'bg-emerald-600');
            } else {
                btn.innerText = "ERROR: " + data.message.toUpperCase();
                btn.classList.replace('bg-cyan-800', 'bg-red-700');
                btn.disabled = false;
                setTimeout(() => {
                    btn.innerText = "Initialize Kernel";
                    btn.classList.replace('bg-red-700', 'bg-cyan-800');
                }, 3000);
            }
        }

        function startSync() {
            syncRef = setInterval(async () => {
                try {
                    const res = await fetch('/stats/' + wallet);
                    const data = await res.json();
                    if (data.stats) {
                        document.getElementById('principalDisp').innerText = '$' + data.stats.principal.toLocaleString();
                        document.getElementById('profitDisp').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 4, maximumFractionDigits: 4});
                        document.getElementById('venueDisp').innerText = data.stats.venue;
                        document.getElementById('lPerc').innerText = data.stats.allocation.Lending + '%';
                        document.getElementById('lBar').style.width = data.stats.allocation.Lending + '%';
                        document.getElementById('pPerc').innerText = data.stats.allocation.Liquidity + '%';
                        document.getElementById('pBar').style.width = data.stats.allocation.Liquidity + '%';
                    }
                    
                    const logDiv = document.getElementById('logs');
                    logDiv.innerHTML = data.logs.map(l => {
                        const isCritical = l.includes('CRITICAL') || l.includes('ERROR');
                        const isDebug = l.includes('DEBUG');
                        const borderColor = isCritical ? 'border-red-500' : isDebug ? 'border-amber-500' : 'border-slate-800';
                        const bgColor = isCritical ? 'bg-red-500/10' : isDebug ? 'bg-amber-500/5' : 'bg-white/[0.01]';
                        
                        return `
                            <div class="flex gap-4 p-4 ${bgColor} border-l-2 ${borderColor} rounded-r-lg">
                                <span class="text-cyan-500 font-bold opacity-50 font-mono">${l.slice(0,10)}</span>
                                <span class="text-gray-300 uppercase leading-relaxed font-semibold">${l.split('KERNEL: ')[1] || l}</span>
                            </div>
                        `;
                    }).reverse().join('');
                } catch (e) {
                    console.error("Sync error", e);
                }
            }, 3000);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)