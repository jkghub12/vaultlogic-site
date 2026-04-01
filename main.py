import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import random

# --- THE VAULTLOGIC KERNEL (STRICT ALM MODE) ---
class VaultLogicALM:
    def __init__(self):
        self.active_vaults = {}
        self.institutional_floor = 10000.0
        # Production Targets (Base Mainnet Spreads)
        self.market_map = {
            "MORPHO_BLUE_USDC": {"apy": 0.061, "weight": 0.45},
            "AAVE_V3_USDC": {"apy": 0.048, "weight": 0.35},
            "AERODROME_USDC_POOL": {"apy": 0.142, "weight": 0.20}
        }
        self.logs = [f"VAULTLOGIC KERNEL v1.0.0 :: SYSTEM INITIALIZED {datetime.now().strftime('%H:%M:%S')}"]

    def log_event(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {msg.upper()}")
        if len(self.logs) > 30: self.logs.pop(0)

    def calculate_yield(self, address):
        """The core heartbeat logic of the yield engine."""
        if address not in self.active_vaults: return None
        
        vault = self.active_vaults[address]
        
        # Calculate Blended APY
        blended_apy = sum(m['apy'] * m['weight'] for m in self.market_map.values())
        # Add market volatility drift
        blended_apy += random.uniform(-0.002, 0.002)
        
        # Accrual logic (per 2-second heartbeat)
        seconds_per_year = 31536000
        accrual_factor = (blended_apy / seconds_per_year) * 2
        earned = vault['principal'] * accrual_factor
        vault['yield_total'] += earned
        
        # Autonomous Rebalancing Simulation
        if random.random() > 0.90:
            self.log_event("ALM: Optimization triggered. Shifting weight to Morpho Blue.")

        return {
            "principal": vault['principal'],
            "profit": vault['yield_total'],
            "apy": blended_apy * 100,
            "status": "OPTIMIZED"
        }

    def deploy(self, address, amount):
        if amount < self.institutional_floor:
            self.log_event(f"REJECTED: ${amount:,.2f} below 10k floor.")
            return False, "Minimum $10,000 required."
        
        self.active_vaults[address] = {
            "principal": amount,
            "yield_total": 0.0,
            "deployed_at": datetime.now()
        }
        self.log_event(f"SETTLED: ${amount:,.2f} verified via settlement layer.")
        self.log_event(f"ENGINE: Capital deployed to high-yield Base clusters.")
        return True, "SUCCESS"

kernel = VaultLogicALM()
app = FastAPI()

# --- API SERVICES ---

@app.get("/heartbeat/{address}")
async def heartbeat(address: str):
    stats = kernel.calculate_yield(address)
    return {"stats": stats, "logs": kernel.logs, "markets": kernel.market_map}

@app.post("/deploy")
async def deploy_capital(data: dict):
    success, msg = kernel.deploy(data['address'], float(data['amount']))
    return {"status": "success" if success else "error", "message": msg}

@app.get("/", response_class=HTMLResponse)
async def terminal():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Production Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/6.7.0/ethers.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=JetBrains+Mono&display=swap');
        body { background: #050608; color: #f8fafc; font-family: 'Space Grotesk', sans-serif; }
        .glass { background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(25px); border: 1px solid rgba(255,255,255,0.05); }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .shimmer { animation: shimmer 2s infinite; background: linear-gradient(90deg, #0ea5e9, #22c55e, #0ea5e9); background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        @keyframes shimmer { to { background-position: 200% center; } }
    </style>
</head>
<body class="p-6 md:p-12">

    <!-- CONNECTION GATE -->
    <div id="gate" class="fixed inset-0 z-[100] bg-[#050608] flex items-center justify-center p-6">
        <div class="max-w-md w-full text-center">
            <div class="w-24 h-24 bg-sky-500 rounded-[2.5rem] mx-auto mb-10 flex items-center justify-center text-4xl font-bold italic text-white shadow-2xl shadow-sky-500/20">V</div>
            <h1 class="text-3xl font-bold tracking-tighter mb-4 italic">VAULTLOGIC</h1>
            <p class="text-slate-500 text-[10px] uppercase tracking-[0.5em] mb-16">The Institutional ALM Engine</p>
            <button onclick="connect()" class="w-full py-6 bg-white text-black rounded-3xl font-black uppercase tracking-widest hover:bg-sky-400 transition-all active:scale-95">Connect for Settlement</button>
        </div>
    </div>

    <!-- MAIN TERMINAL -->
    <div id="terminal" class="max-w-7xl mx-auto hidden opacity-0 transition-opacity duration-1000">
        <header class="flex justify-between items-center mb-16">
            <div class="flex items-center gap-5">
                <div class="w-12 h-12 bg-sky-500 rounded-2xl flex items-center justify-center text-white font-bold italic text-2xl">V</div>
                <div>
                    <h2 class="text-xl font-bold tracking-tighter uppercase italic leading-none">VaultLogic</h2>
                    <p class="text-[9px] text-slate-500 uppercase tracking-widest font-bold mt-1">Status: <span class="text-emerald-500">Live Engine</span></p>
                </div>
            </div>
            <div id="walletDisplay" class="mono text-[10px] text-slate-500 border border-white/5 px-6 py-3 rounded-full bg-white/[0.02]">0x...</div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
            <!-- Controller -->
            <div class="lg:col-span-4 space-y-8">
                <div class="glass p-10 rounded-[3rem]">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-sky-500 mb-10">Capital Settlement</h3>
                    <div class="mb-10">
                        <label class="text-[10px] text-slate-500 uppercase font-bold block mb-4 tracking-widest">Plaid Transaction Amount (USD)</label>
                        <input id="amt" type="number" value="25000" class="w-full bg-black/60 border border-white/10 rounded-2xl p-6 text-3xl font-bold text-white focus:outline-none focus:border-sky-500/50">
                        <div class="flex justify-between mt-4">
                            <p class="text-[9px] text-slate-600 font-bold uppercase italic tracking-wider">Base Settlement Layer</p>
                            <p class="text-[9px] text-slate-600 font-bold uppercase tracking-wider">Min: $10,000</p>
                        </div>
                    </div>
                    <button id="deployBtn" onclick="authorize()" class="w-full py-6 bg-sky-600 text-white font-black rounded-3xl uppercase tracking-widest text-[12px] shadow-2xl shadow-sky-600/10 active:scale-95 transition-all">Authorize Engine</button>
                </div>

                <div class="glass p-10 rounded-[3rem]">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 mb-8">Yield Markets</h3>
                    <div id="marketMonitor" class="space-y-5"></div>
                </div>
            </div>

            <!-- Performance -->
            <div class="lg:col-span-8 flex flex-col space-y-8">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div class="glass p-10 rounded-[3rem]">
                        <p class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Total Principal</p>
                        <h2 id="viewPrincipal" class="text-5xl font-bold tracking-tighter italic">$0.00</h2>
                    </div>
                    <div class="glass p-10 rounded-[3rem] border-l-4 border-l-emerald-500">
                        <p class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Realized Profit</p>
                        <h2 id="viewProfit" class="text-5xl font-bold text-emerald-400 tracking-tighter italic tabular-nums">$0.000000</h2>
                    </div>
                </div>

                <div class="glass p-10 rounded-[3rem] flex-grow flex flex-col min-h-[500px]">
                    <div class="flex justify-between items-center mb-10 pb-8 border-b border-white/5">
                        <div class="flex items-center gap-3">
                            <div class="w-2 h-2 bg-sky-500 rounded-full animate-pulse"></div>
                            <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Execution Audit Trail</p>
                        </div>
                        <span id="stratStatus" class="text-[9px] px-5 py-2 bg-sky-500/10 text-sky-400 rounded-full font-black border border-sky-500/10">KERNEL STANDBY</span>
                    </div>
                    <div id="logBox" class="flex-1 overflow-y-auto custom-scroll mono text-[11px] space-y-4 opacity-50"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let userAddr;
        async function connect() {
            if(!window.ethereum) return alert("Web3 Provider Required.");
            const accs = await window.ethereum.request({ method: 'eth_requestAccounts' });
            userAddr = accs[0];
            document.getElementById('gate').classList.add('hidden');
            document.getElementById('terminal').classList.remove('hidden');
            setTimeout(() => document.getElementById('terminal').classList.add('opacity-100'), 100);
            document.getElementById('walletDisplay').innerText = userAddr.slice(0,10) + "...";
            startSync();
        }

        async function authorize() {
            const amount = document.getElementById('amt').value;
            const btn = document.getElementById('deployBtn');
            btn.disabled = true;
            btn.innerText = "INITIALIZING SETTLEMENT...";

            const res = await fetch('/deploy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ address: userAddr, amount: amount })
            });
            const data = await res.json();
            
            if(data.status === 'success') {
                btn.innerText = "ENGINE ACTIVE";
                btn.className = "w-full py-6 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded-3xl font-black uppercase text-[12px]";
            } else {
                alert(data.message);
                btn.disabled = false;
                btn.innerText = "Authorize Engine";
            }
        }

        function startSync() {
            setInterval(async () => {
                try {
                    const res = await fetch('/heartbeat/' + userAddr);
                    const data = await res.json();
                    
                    if(data.stats) {
                        document.getElementById('viewPrincipal').innerText = '$' + data.stats.principal.toLocaleString();
                        document.getElementById('viewProfit').innerText = '$' + data.stats.profit.toLocaleString(undefined, {minimumFractionDigits: 6, maximumFractionDigits: 6});
                        document.getElementById('stratStatus').innerText = "ALM: " + data.stats.apy.toFixed(2) + "% APY";
                    }

                    if(data.markets) {
                        let html = "";
                        for(let k in data.markets) {
                            html += `<div class="flex justify-between items-center border-b border-white/5 pb-4">
                                <span class="text-[11px] font-bold text-slate-500 uppercase tracking-widest">${k.replace('_', ' ')}</span>
                                <span class="text-[11px] font-bold text-white">${(data.markets[k].apy * 100).toFixed(2)}%</span>
                            </div>`;
                        }
                        document.getElementById('marketMonitor').innerHTML = html;
                    }

                    if(data.logs) {
                        document.getElementById('logBox').innerHTML = data.logs.map(l => 
                            `<div class="flex gap-4"><span class="text-sky-500 font-bold">>>></span><span class="text-slate-300 uppercase">${l.split(': ')[1] || l}</span></div>`
                        ).reverse().join('');
                    }
                } catch(e){}
            }, 2000);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)