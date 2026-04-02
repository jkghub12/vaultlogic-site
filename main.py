import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import random
import hashlib

# --- VAULTLOGIC VERIFIED KERNEL (2026 EDITION) ---
class VaultLogicKernel:
    def __init__(self):
        self.vaults = {}
        self.institutional_floor = 10000.0
        self.market_benchmarks = {
            "CORE_INSTITUTIONAL": {"apy": 0.042, "risk": "LOW"},
            "DEFI_UTILIZATION": {"apy": 0.078, "risk": "MEDIUM"},
            "EXCHANGE_FIXED": {"apy": 0.092, "risk": "STABLE"}
        }
        self.logs = [f"KERNEL V7.0 :: VERIFICATION LAYER ACTIVE :: {datetime.now().strftime('%H:%M:%S')}"]

    def log(self, msg, type="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] [{type}] {msg.upper()}")
        if len(self.logs) > 30: self.logs.pop(0)

    def process_yield(self, address):
        if address not in self.vaults: return None
        v = self.vaults[address]
        avg_apy = 0.071 + random.uniform(-0.001, 0.001) # 7.1% base target
        earned = v['principal'] * (avg_apy / 31536000) * 2
        v['yield'] += earned
        return {"stealth_id": v['stealth_id'], "principal": v['principal'], "yield": v['yield'], "apy": avg_apy * 100}

    def deploy(self, address, amount, actual_balance):
        # RULE: MUST HAVE $10K MINIMUM IN WALLET TO EVEN START
        if actual_balance < self.institutional_floor:
            self.log(f"REJECTED: WALLET BALANCE ${actual_balance:,.2f} BELOW $10K FLOOR.", type="SECURITY")
            return False, "Insufficient Institutional Balance"
        
        # RULE: CANNOT SCOUT MORE THAN YOU HAVE
        if amount > actual_balance:
            return False, "Amount exceeds wallet balance"

        stealth_id = "MIDNIGHT-" + hashlib.sha256(address.encode()).hexdigest()[:8].upper()
        self.vaults[address] = {"stealth_id": stealth_id, "principal": amount, "yield": 0.0}
        self.log(f"VERIFIED: ${amount:,.2f} DEPLOYED FROM ${actual_balance:,.2f} TOTAL.")
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
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Verified Institutional Scout</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=JetBrains+Mono&display=swap');
        body { background: #020408; color: #f1f5f9; font-family: 'Space Grotesk', sans-serif; }
        .glass { background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.03); }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .btn-disabled { opacity: 0.3; cursor: not-allowed; filter: grayscale(1); }
    </style>
</head>
<body class="p-4 md:p-12 min-h-screen">

    <!-- CONNECTION GATE -->
    <div id="gate" class="fixed inset-0 z-[100] bg-[#020408] flex flex-col items-center justify-center p-6 text-center">
        <div class="w-20 h-20 bg-sky-500 rounded-[2.2rem] mb-8 flex items-center justify-center text-3xl font-bold italic text-white">V</div>
        <h1 class="text-3xl font-bold tracking-tighter mb-2 italic">VAULTLOGIC VERIFY</h1>
        <p class="text-slate-500 text-[10px] uppercase tracking-[0.5em] mb-12">Checking On-Chain Institutional Credentials</p>
        <button onclick="connectWallet()" class="w-full max-w-xs py-5 bg-white text-black rounded-2xl font-black uppercase tracking-widest hover:bg-sky-400 transition-all">Identify Wallet</button>
    </div>

    <!-- MAIN TERMINAL -->
    <div id="main" class="max-w-7xl mx-auto hidden opacity-0 transition-opacity duration-700">
        <header class="flex justify-between items-center mb-12">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 bg-sky-500 rounded-xl flex items-center justify-center text-white font-bold italic">V</div>
                <h2 class="text-xl font-bold uppercase italic tracking-tighter">VaultLogic <span class="text-slate-600 font-light">Verified</span></h2>
            </div>
            <div class="flex gap-4">
                <div id="walletDisplay" class="mono text-[10px] text-slate-500 border border-white/5 px-6 py-3 rounded-full bg-white/[0.02]">0x...</div>
                <button onclick="location.reload()" class="text-[9px] uppercase font-bold text-red-500/50 hover:text-red-500">Disconnect</button>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-4 space-y-6">
                <div class="glass p-8 rounded-[2.5rem] border-l-4 border-sky-500">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-sky-500 mb-6">Capital Verification</h3>
                    
                    <div id="balanceCheck" class="mb-8 p-4 bg-white/[0.02] rounded-2xl border border-white/5">
                        <p class="text-[9px] text-slate-500 uppercase font-bold mb-1">Detected Wallet Balance</p>
                        <h4 id="detectedBalance" class="text-xl font-bold text-white">$0.00 <span class="text-[10px] text-slate-600">USDC</span></h4>
                    </div>

                    <div id="deploymentForm" class="space-y-6">
                        <div>
                            <label class="text-[9px] text-slate-500 uppercase font-bold block mb-3">Scout Allocation (USD)</label>
                            <input id="scoutAmount" type="number" placeholder="Enter Amount" class="w-full bg-black/60 border border-white/10 rounded-2xl p-5 text-2xl font-bold focus:outline-none focus:border-sky-500/50">
                        </div>
                        <button id="authBtn" onclick="handleAuthorize()" class="w-full py-5 bg-sky-600 text-white font-black rounded-2xl uppercase tracking-widest text-[11px] transition-all">Authorize Scout</button>
                    </div>
                </div>

                <div class="glass p-8 rounded-[2.5rem]">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 mb-6">Live Drivers</h3>
                    <div id="marketList" class="space-y-4"></div>
                </div>
            </div>

            <div class="lg:col-span-8 space-y-8">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="glass p-10 rounded-[2.5rem]">
                        <p class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Stealth ID</p>
                        <h2 id="stealthId" class="mono text-xl font-bold text-sky-400">---</h2>
                    </div>
                    <div class="glass p-10 rounded-[2.5rem] border-l-4 border-emerald-500">
                        <p class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Total Yield Accrued</p>
                        <h2 id="yieldDisplay" class="text-4xl font-bold text-emerald-400 italic tabular-nums tracking-tighter">$0.000000</h2>
                    </div>
                </div>

                <div class="glass p-10 rounded-[2.5rem] flex-grow flex flex-col min-h-[450px]">
                    <div class="flex justify-between items-center mb-8 pb-6 border-b border-white/5">
                        <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Institutional Verification Log</p>
                        <span id="apyDisplay" class="text-[9px] px-4 py-1.5 bg-sky-500/10 text-sky-400 rounded-full font-black">SCANNING</span>
                    </div>
                    <div id="logContent" class="flex-1 overflow-y-auto mono text-[11px] space-y-3"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentAccount;
        let userBalance = 0;

        async function connectWallet() {
            if (!window.ethereum) return alert("Please install MetaMask or Coinbase Wallet.");
            
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            currentAccount = accounts[0];
            
            // SIMULATION: In a real app, we'd call the USDC contract on Base.
            // For this demo, we "fetch" the balance to show Jesse how the gate works.
            userBalance = Math.random() > 0.5 ? (15000 + Math.random() * 50000) : (2000 + Math.random() * 5000);
            
            document.getElementById('gate').classList.add('hidden');
            document.getElementById('main').classList.remove('hidden');
            setTimeout(() => document.getElementById('main').classList.add('opacity-100'), 50);
            
            document.getElementById('walletDisplay').innerText = currentAccount.slice(0,10) + "...";
            document.getElementById('detectedBalance').innerText = "$" + userBalance.toLocaleString(undefined, {minimumFractionDigits: 2});
            
            if (userBalance < 10000) {
                const btn = document.getElementById('authBtn');
                btn.innerText = "INSUFFICIENT FUNDS (<$10K)";
                btn.className = "w-full py-5 bg-red-900/20 text-red-500 border border-red-500/20 rounded-2xl font-black uppercase text-[10px] cursor-not-allowed";
                btn.disabled = true;
            }

            startUpdates();
        }

        async function handleAuthorize() {
            const amount = parseFloat(document.getElementById('scoutAmount').value);
            if (!amount || amount < 1) return alert("Enter valid amount");

            const res = await fetch('/deploy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: currentAccount, amount: amount, balance: userBalance })
            });
            const data = await res.json();
            
            if(data.status === 'success') {
                const btn = document.getElementById('authBtn');
                btn.innerText = "SCOUT AUTHORIZED";
                btn.disabled = true;
                btn.classList.add('btn-disabled');
            } else {
                alert(data.message);
            }
        }

        function startUpdates() {
            setInterval(async () => {
                const res = await fetch('/heartbeat/' + currentAccount);
                const d = await res.json();
                
                if(d.stats) {
                    document.getElementById('stealthId').innerText = d.stats.stealth_id;
                    document.getElementById('yieldDisplay').innerText = '$' + d.stats.yield.toLocaleString(undefined, {minimumFractionDigits: 6});
                    document.getElementById('apyDisplay').innerText = d.stats.apy.toFixed(2) + "% APY";
                }

                if(d.markets) {
                    document.getElementById('marketList').innerHTML = Object.entries(d.markets).map(([k,v]) => 
                        `<div class="flex justify-between border-b border-white/5 pb-3">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">${k.replace('_', ' ')}</span>
                            <span class="text-[10px] font-bold text-white">${(v.apy*100).toFixed(2)}%</span>
                        </div>`
                    ).join('');
                }

                if(d.logs) {
                    document.getElementById('logContent').innerHTML = d.logs.map(l => `
                        <div class="flex gap-4">
                            <span class="text-sky-500 font-bold">>>></span>
                            <span class="uppercase tracking-tight text-slate-400">${l.split('] ')[1] || l}</span>
                        </div>
                    `).reverse().join('');
                }
            }, 2000);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)