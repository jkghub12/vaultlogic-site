import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import random
import hashlib

# --- VAULTLOGIC HYBRID KERNEL (V8.1) ---
class VaultLogicKernel:
    def __init__(self):
        self.vaults = {}
        self.institutional_floor = 10000.0
        self.market_benchmarks = {
            "CORE_INSTITUTIONAL": {"apy": 0.042},
            "DEFI_UTILIZATION": {"apy": 0.078},
            "EXCHANGE_FIXED": {"apy": 0.092}
        }
        self.logs = [f"KERNEL V8.1 // HYBRID VERIFICATION ACTIVE // {datetime.now().strftime('%H:%M:%S')}"]

    def log(self, msg, type="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] [{type}] {msg.upper()}")
        if len(self.logs) > 30: self.logs.pop(0)

    def process_yield(self, address):
        if address not in self.vaults: return None
        v = self.vaults[address]
        avg_apy = 0.071 + random.uniform(-0.0005, 0.0005)
        earned = v['principal'] * (avg_apy / 31536000) * 2
        v['yield'] += earned
        return {"stealth_id": v['stealth_id'], "principal": v['principal'], "yield": v['yield'], "apy": avg_apy * 100}

    def deploy(self, address, amount, actual_balance):
        if actual_balance < self.institutional_floor:
            self.log(f"REJECTED: ${actual_balance:,.2f} BELOW FLOOR.", type="SECURE")
            return False, "Insufficient Institutional Balance"
        
        if amount > actual_balance:
            return False, "Allocation exceeds verified balance"

        stealth_id = "MIDNIGHT-" + hashlib.sha256(address.encode()).hexdigest()[:8].upper()
        self.vaults[address] = {"stealth_id": stealth_id, "principal": amount, "yield": 0.0}
        self.log(f"SCOUT AUTHORIZED: ${amount:,.2f} // STEALTH: {stealth_id}")
        return True, "SUCCESS"

kernel = VaultLogicKernel()
app = FastAPI()

class DeployReq(BaseModel):
    address: str
    amount: float
    balance: float

@app.get("/heartbeat/{address}")
async def heartbeat(address: str):
    stats = kernel.process_yield(address)
    return {"stats": stats, "logs": kernel.logs, "markets": kernel.market_benchmarks}

@app.post("/deploy")
async def deploy(data: DeployReq):
    success, msg = kernel.deploy(data.address, data.amount, data.balance)
    return {"status": "success" if success else "error", "message": msg}

@app.get("/", response_class=HTMLResponse)
async def terminal():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Institutional Gate</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=JetBrains+Mono&display=swap');
        body { background: #010204; color: #f1f5f9; font-family: 'Space Grotesk', sans-serif; }
        .glass { background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(25px); border: 1px solid rgba(255,255,255,0.03); }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .status-pill { border-left: 4px solid #0ea5e9; }
        .yield-pill { border-left: 4px solid #10b981; }
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    </style>
</head>
<body class="p-4 md:p-12 min-h-screen flex flex-col">
    <div id="gate" class="fixed inset-0 z-[100] bg-[#010204] flex flex-col items-center justify-center p-6 text-center">
        <div class="w-20 h-20 bg-sky-500 rounded-[2.2rem] mb-8 flex items-center justify-center text-3xl font-bold italic text-white shadow-2xl">V</div>
        <h1 class="text-3xl font-bold tracking-tighter mb-2 italic uppercase">VaultLogic</h1>
        <p class="text-slate-500 text-[10px] uppercase tracking-[0.5em] mb-12">Institutional Verification Protocol</p>
        <button onclick="initConnection()" class="w-full max-w-xs py-5 bg-white text-black rounded-2xl font-black uppercase tracking-widest hover:bg-sky-400 transition-all">Identify Wallet</button>
    </div>

    <div id="main" class="max-w-7xl mx-auto hidden opacity-0 transition-opacity duration-700 w-full flex-grow">
        <header class="flex justify-between items-center mb-12">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 bg-sky-500 rounded-xl flex items-center justify-center text-white font-bold italic">V</div>
                <h2 class="text-xl font-bold uppercase italic tracking-tighter">VaultLogic <span class="text-slate-600 font-light tracking-widest">GATE</span></h2>
            </div>
            <button onclick="location.reload()" class="mono text-[10px] text-slate-500 border border-white/5 px-6 py-3 rounded-full bg-white/[0.02] hover:text-red-400">DISCONNECT</button>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-4 space-y-6">
                <div class="glass p-8 rounded-[2.5rem] status-pill">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-sky-500 mb-8">Asset Verification</h3>
                    <div class="mb-10 p-6 bg-white/[0.02] rounded-2xl border border-white/5">
                        <p class="text-[9px] text-slate-500 uppercase font-bold mb-2 tracking-widest">Base Network USDC</p>
                        <h4 id="displayBal" class="text-3xl font-bold text-white tabular-nums">$0.00</h4>
                        <div id="gateStatus" class="mt-3 text-[8px] font-black uppercase px-2 py-1 bg-red-500/10 text-red-400 w-fit rounded">LOCKED: BELOW FLOOR</div>
                    </div>
                    <div class="space-y-6">
                        <div>
                            <label class="text-[9px] text-slate-500 uppercase font-bold block mb-3">Scout Allocation</label>
                            <input id="scoutInput" type="number" placeholder="Min. $10,000" class="w-full bg-black/60 border border-white/10 rounded-2xl p-5 text-2xl font-bold focus:outline-none focus:border-sky-500/50">
                        </div>
                        <button id="authBtn" onclick="authorize()" class="w-full py-5 bg-sky-600 text-white font-black rounded-2xl uppercase tracking-widest text-[11px] transition-all">Authorize Scout</button>
                    </div>
                </div>
                <div class="glass p-8 rounded-[2.5rem]">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 mb-6">Market Drivers (2026)</h3>
                    <div id="mktList" class="space-y-4"></div>
                </div>
            </div>

            <div class="lg:col-span-8 space-y-8">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="glass p-10 rounded-[2.5rem]">
                        <p class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Stealth Identity</p>
                        <h2 id="stealthText" class="mono text-xl font-bold text-sky-400 uppercase">Awaiting Auth</h2>
                    </div>
                    <div class="glass p-10 rounded-[2.5rem] yield-pill">
                        <p class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Yield Accrued</p>
                        <h2 id="yieldText" class="text-4xl font-bold text-emerald-400 italic tabular-nums tracking-tighter">$0.000000</h2>
                    </div>
                </div>
                <div class="glass p-10 rounded-[2.5rem] flex-grow flex flex-col min-h-[480px]">
                    <div class="flex justify-between items-center mb-8 pb-6 border-b border-white/5">
                        <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Institutional Verification Log</p>
                        <span id="apyText" class="text-[9px] px-4 py-1.5 bg-sky-500/10 text-sky-400 rounded-full font-black">SCANNING</span>
                    </div>
                    <div id="logBox" class="flex-1 overflow-y-auto custom-scroll mono text-[11px] space-y-3 opacity-60"></div>
                </div>
            </div>
        </div>
    </div>

    <footer class="mt-12 text-center">
        <p class="text-[9px] text-slate-700 uppercase tracking-widest">VaultLogic 2026 // Distributed Settlement Engine</p>
        <button onclick="devOverride()" class="text-[8px] text-slate-800 mt-4 uppercase hover:text-sky-900 transition-colors">Developer Override (Demo Mode)</button>
    </footer>

    <script>
        let wallet;
        let verifiedBalance = 0;
        const USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";

        async function initConnection() {
            if (!window.ethereum) return alert("MetaMask or Coinbase Wallet required.");
            try {
                const provider = new ethers.providers.Web3Provider(window.ethereum);
                const accounts = await provider.send("eth_requestAccounts", []);
                wallet = accounts[0];

                document.getElementById('gate').classList.add('hidden');
                document.getElementById('main').classList.remove('hidden');
                setTimeout(() => document.getElementById('main').classList.add('opacity-100'), 50);

                const abi = ["function balanceOf(address) view returns (uint256)"];
                const contract = new ethers.Contract(USDC_BASE, abi, provider);
                const rawBal = await contract.balanceOf(wallet);
                verifiedBalance = parseFloat(ethers.utils.formatUnits(rawBal, 6));
                
                updateUI();
                startHeartbeat();
            } catch (e) {
                console.error(e);
            }
        }

        function devOverride() {
            verifiedBalance = 100000.00;
            updateUI();
        }

        function updateUI() {
            document.getElementById('displayBal').innerText = "$" + verifiedBalance.toLocaleString(undefined, {minimumFractionDigits: 2});
            const status = document.getElementById('gateStatus');
            const btn = document.getElementById('authBtn');
            
            if (verifiedBalance < 10000) {
                status.innerText = "LOCKED: BELOW FLOOR";
                status.className = "mt-3 text-[8px] font-black uppercase px-2 py-1 bg-red-500/10 text-red-400 w-fit rounded";
                btn.disabled = true;
                btn.innerText = "GATE LOCKED";
                btn.classList.add('opacity-30', 'cursor-not-allowed');
            } else {
                status.innerText = "VERIFIED: INSTITUTIONAL";
                status.className = "mt-3 text-[8px] font-black uppercase px-2 py-1 bg-emerald-500/10 text-emerald-400 w-fit rounded";
                btn.disabled = false;
                btn.innerText = "AUTHORIZE SCOUT";
                btn.classList.remove('opacity-30', 'cursor-not-allowed');
            }
        }

        async function authorize() {
            const val = parseFloat(document.getElementById('scoutInput').value);
            if (val < 10000) return alert("Min. $10,000 Institutional Floor Required.");
            const res = await fetch('/deploy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: wallet, amount: val, balance: verifiedBalance })
            });
            const data = await res.json();
            if(data.status === 'success') {
                const btn = document.getElementById('authBtn');
                btn.innerText = "SCOUT ACTIVE";
                btn.disabled = true;
                btn.classList.add('opacity-50');
            } else {
                alert(data.message);
            }
        }

        function startHeartbeat() {
            setInterval(async () => {
                try {
                    const res = await fetch('/heartbeat/' + wallet);
                    const d = await res.json();
                    if(d.stats) {
                        document.getElementById('stealthText').innerText = d.stats.stealth_id;
                        document.getElementById('yieldText').innerText = '$' + d.stats.yield.toLocaleString(undefined, {minimumFractionDigits: 6});
                        document.getElementById('apyText').innerText = d.stats.apy.toFixed(2) + "% APY";
                    }
                    if(d.markets) {
                        document.getElementById('mktList').innerHTML = Object.entries(d.markets).map(([k,v]) => 
                            `<div class="flex justify-between border-b border-white/5 pb-3">
                                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">${k.replace('_', ' ')}</span>
                                <span class="text-[10px] font-bold text-white">${(v.apy*100).toFixed(2)}%</span>
                            </div>`
                        ).join('');
                    }
                    if(d.logs) {
                        document.getElementById('logBox').innerHTML = d.logs.map(l => `
                            <div class="flex gap-4">
                                <span class="text-sky-500 font-bold">>>></span>
                                <span class="uppercase text-slate-400 font-medium">${l.split('] ')[1] || l}</span>
                            </div>`).reverse().join('');
                    }
                } catch(e) {}
            }, 2000);
        }
    </script>
</body>
</html>
"""
    return html_content

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)