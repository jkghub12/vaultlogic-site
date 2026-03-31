import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3
from engine import kernel
import uvicorn

app = FastAPI()

BASE_RPC_URL = "https://mainnet.base.org"
audit_logs = ["VaultLogic v3.4-ALM: System Ready. Standing by for Kernel Initialization..."]

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def background_kernel_loop():
    while True:
        await asyncio.sleep(10)
        for addr in list(kernel.active_deployments.keys()):
            msg = kernel.active_deployments[addr].calculate_tick(10)
            if msg: add_log(msg)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str):
    return {"stats": kernel.get_stats(address), "logs": audit_logs}

@app.post("/activate")
async def activate_deployment(data: EngineInit):
    if data.amount < 10000: return {"status": "error", "message": "Floor is $10k"}
    msg = kernel.deploy(data.address, data.amount, BASE_RPC_URL)
    add_log(msg)
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VaultLogic | Industrial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        body { background: #020305; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .stat-card { background: #06080c; border: 1px solid rgba(255,255,255,0.03); border-radius: 24px; }
        .progress-bar { height: 4px; border-radius: 2px; background: #1a1f26; overflow: hidden; }
        .progress-fill { height: 100%; transition: width 1s ease-in-out; }
    </style>
</head>
<body class="p-8">
    <header class="max-w-6xl mx-auto flex justify-between items-center mb-12">
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center text-black font-black italic text-xl">V</div>
            <h1 class="text-xl font-black italic tracking-tighter uppercase">VaultLogic</h1>
        </div>
        <button id="authBtn" onclick="handleAuth()" class="bg-white text-black px-6 py-2 rounded-lg font-black text-[10px] tracking-widest uppercase">Connect Wallet</button>
    </header>

    <main id="dash" class="max-w-6xl mx-auto opacity-20 pointer-events-none transition-all duration-500">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="stat-card p-6 border-l-2 border-cyan-500">
                <p class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Deployed Capital</p>
                <h2 id="principal" class="text-4xl font-black italic">$0</h2>
            </div>
            <div class="stat-card p-6 border-l-2 border-emerald-500">
                <p class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Net Yield (80%)</p>
                <h2 id="profit" class="text-4xl font-black italic text-emerald-400">$0.0000</h2>
            </div>
            <div class="stat-card p-6 border-l-2 border-purple-500">
                <p class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Active Strategy</p>
                <h2 id="venue" class="text-3xl font-black italic text-white uppercase">Idle</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-4 stat-card p-8">
                <h3 class="text-[10px] font-black uppercase tracking-widest text-cyan-500 mb-8">System Control</h3>
                <div class="space-y-8">
                    <div>
                        <div class="flex justify-between text-[10px] font-bold uppercase text-gray-500 mb-4">
                            <span>Amount</span>
                            <span id="amtDisp" class="text-white">$10,000</span>
                        </div>
                        <input type="range" id="amtInput" min="10000" max="250000" step="5000" value="10000" class="w-full" oninput="document.getElementById('amtDisp').innerText = '$'+parseInt(this.value).toLocaleString()">
                    </div>
                    
                    <div class="space-y-4">
                        <div class="flex justify-between text-[10px] font-bold uppercase text-gray-500">
                            <span>Lending Allocation</span>
                            <span id="lendPerc" class="text-cyan-400">100%</span>
                        </div>
                        <div class="progress-bar"><div id="lendBar" class="progress-fill bg-cyan-500" style="width: 100%"></div></div>
                        
                        <div class="flex justify-between text-[10px] font-bold uppercase text-gray-500 pt-2">
                            <span>Liquidity Provision</span>
                            <span id="lpPerc" class="text-purple-400">0%</span>
                        </div>
                        <div class="progress-bar"><div id="lpBar" class="progress-fill bg-purple-500" style="width: 0%"></div></div>
                    </div>

                    <button id="execBtn" onclick="initKernel()" class="w-full py-4 bg-cyan-800 text-white font-black rounded-xl text-[10px] uppercase tracking-widest hover:bg-cyan-700">Initialize Kernel</button>
                </div>
            </div>

            <div class="lg:col-span-8 stat-card p-8 overflow-hidden flex flex-col">
                <p class="text-[10px] font-black uppercase text-gray-500 mb-6 border-b border-white/5 pb-4 tracking-widest">Audit Terminal</p>
                <div id="logs" class="font-mono text-[11px] space-y-4 overflow-y-auto max-h-[350px]"></div>
            </div>
        </div>
    </main>

    <script>
        let addr = null;
        async function handleAuth() {
            if (window.ethereum) {
                const provider = new ethers.providers.Web3Provider(window.ethereum);
                await provider.send("eth_requestAccounts", []);
                addr = await provider.getSigner().getAddress();
                document.getElementById('authBtn').innerText = addr.slice(0,6)+'...';
                document.getElementById('dash').classList.remove('opacity-20', 'pointer-events-none');
                setInterval(sync, 3000);
            }
        }

        async function initKernel() {
            const amount = document.getElementById('amtInput').value;
            await fetch('/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: addr, amount: parseFloat(amount) })
            });
            document.getElementById('execBtn').innerText = "Running";
            document.getElementById('execBtn').classList.replace('bg-cyan-800', 'bg-emerald-600');
        }

        async function sync() {
            const res = await fetch('/stats/' + addr);
            const data = await res.json();
            if (data.stats) {
                document.getElementById('principal').innerText = '$' + data.stats.principal.toLocaleString();
                document.getElementById('profit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {minimumFractionDigits: 4});
                document.getElementById('venue').innerText = data.stats.venue;
                document.getElementById('lendPerc').innerText = data.stats.allocation.Lending + '%';
                document.getElementById('lendBar').style.width = data.stats.allocation.Lending + '%';
                document.getElementById('lpPerc').innerText = data.stats.allocation.Liquidity + '%';
                document.getElementById('lpBar').style.width = data.stats.allocation.Liquidity + '%';
            }
            document.getElementById('logs').innerHTML = data.logs.map(l => `
                <div class="p-3 border-l-2 border-slate-800 bg-white/[0.01]">
                    <span class="text-cyan-500 font-bold uppercase mr-3">KERNEL:</span>
                    <span class="text-slate-400 uppercase">${l.split('KERNEL: ')[1] || l}</span>
                </div>
            `).reverse().join('');
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)