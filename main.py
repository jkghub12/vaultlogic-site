import asyncio
import random
from fastapi import FastAPI, Request
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
# Ensure the backend and frontend use the EXACT same checksummed string
DEMO_ADDRESS_STR = "0x2d8E2788a42FA2089279743c746C9742721f5C14"
DEMO_ADDRESS = Web3.to_checksum_address(DEMO_ADDRESS_STR)

w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]
usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)

audit_logs = ["VAULTLOGIC V3.6-STABLE: Industrial Gateway Ready."]

class EngineInit(BaseModel):
    address: str
    amount: float
    is_demo: bool = False

def add_log(msg):
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
    try:
        # Convert to checksum to avoid the SYNC_ERROR
        safe_addr = Web3.to_checksum_address(address)
        return {
            "stats": kernel.get_stats(safe_addr),
            "logs": audit_logs
        }
    except Exception as e:
        return {"stats": None, "logs": audit_logs, "error": str(e)}

@app.post("/activate")
async def activate(data: EngineInit):
    try:
        target_address = Web3.to_checksum_address(data.address)
        if data.amount < 10000:
            add_log(f"REJECTED: ${data.amount:,.2f} is below the Institutional Floor.")
            return {"status": "error", "message": "Below $10k Floor"}

        if not data.is_demo:
            raw_balance = usdc_contract.functions.balanceOf(target_address).call()
            actual_usdc = raw_balance / 10**6
            if actual_usdc < data.amount:
                add_log(f"CRITICAL: Insufficient Funds (${actual_usdc:,.2f} available).")
                return {"status": "error", "message": "Check USDC Balance"}

        msg = kernel.deploy(target_address, data.amount, BASE_RPC_URL)
        add_log(msg)
        return {"status": "success", "validated_address": target_address}
    except Exception as e:
        add_log(f"NETWORK ERROR: {str(e)}")
        return {"status": "error", "message": "Network/Validation Error"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Industrial ALM</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        body {{ background: #020408; color: #f8fafc; font-family: 'Inter', sans-serif; overflow-x: hidden; }}
        .glass {{ background: rgba(10, 15, 25, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }}
        .accent-gradient {{ background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); }}
        .btn-shadow {{ box-shadow: 0 4px 14px 0 rgba(14, 165, 233, 0.39); }}
        input[type=range] {{ accent-color: #0ea5e9; }}
        ::-webkit-scrollbar {{ width: 4px; }}
        ::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 10px; }}
        
        /* Modal Animation */
        .modal-enter {{ animation: modalFade 0.3s ease-out forwards; }}
        @keyframes modalFade {{ from {{ opacity: 0; transform: scale(0.95); }} to {{ opacity: 1; transform: scale(1); }} }}
    </style>
</head>
<body class="p-6 md:p-10 min-h-screen flex flex-col">
    <!-- Plaid Simulation Modal -->
    <div id="plaidModal" class="fixed inset-0 z-50 hidden items-center justify-center bg-black/80 backdrop-blur-sm p-4">
        <div class="glass max-w-md w-full p-8 rounded-3xl border border-white/10 modal-enter">
            <div class="w-12 h-12 bg-white rounded-xl mb-6 flex items-center justify-center">
                <svg class="w-6 h-6 text-black" fill="currentColor" viewBox="0 0 24 24"><path d="M2 12c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12zm11-4h-2v1h2V8zm0 2h-2v6h2v-6z"/></svg>
            </div>
            <h2 class="text-xl font-bold mb-2">Connect Bank Account</h2>
            <p class="text-slate-400 text-sm mb-8 leading-relaxed">VaultLogic uses Plaid to securely verify and link your traditional bank assets for direct USD-USDC settlements.</p>
            
            <div class="space-y-3 mb-8">
                <div class="p-4 bg-white/5 border border-white/5 rounded-xl flex items-center gap-4 cursor-pointer hover:bg-white/10 transition-colors">
                    <div class="w-8 h-8 bg-blue-600 rounded-lg"></div>
                    <span class="text-sm font-bold">Chase Manhattan</span>
                </div>
                <div class="p-4 bg-white/5 border border-white/5 rounded-xl flex items-center gap-4 cursor-pointer hover:bg-white/10 transition-colors opacity-50">
                    <div class="w-8 h-8 bg-red-600 rounded-lg"></div>
                    <span class="text-sm font-bold">Bank of America</span>
                </div>
            </div>
            
            <button onclick="simulatePlaidSuccess()" class="w-full py-4 bg-white text-black font-black rounded-xl text-xs uppercase tracking-widest hover:bg-slate-200 transition-all">Link Selected Account</button>
            <button onclick="closePlaid()" class="w-full mt-4 text-slate-500 text-[10px] font-bold uppercase tracking-widest hover:text-white transition-colors">Cancel Connection</button>
        </div>
    </div>

    <nav class="max-w-7xl w-full mx-auto flex justify-between items-center mb-12">
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 accent-gradient rounded-xl flex items-center justify-center text-white font-black text-xl italic">V</div>
            <div>
                <h1 class="text-xl font-black italic tracking-tighter uppercase leading-none">VaultLogic</h1>
                <p class="text-[8px] text-slate-500 font-bold uppercase tracking-[0.3em] mt-1">Institutional Autopilot</p>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <button id="authBtn" onclick="toggleAuth()" class="bg-white text-black px-6 py-2.5 rounded-lg font-black text-[10px] tracking-widest uppercase hover:bg-slate-200 transition-all shadow-xl">Connect Wallet</button>
            <button id="disconnectBtn" onclick="disconnect()" class="hidden text-slate-500 hover:text-red-500 text-[10px] font-bold uppercase tracking-widest transition-all">Disconnect</button>
        </div>
    </nav>

    <main id="mainDash" class="max-w-7xl w-full mx-auto opacity-20 pointer-events-none transition-all duration-700 flex-grow">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-center">
            <div class="glass p-8 rounded-3xl border-l-4 border-sky-500">
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Capital Managed</p>
                <h2 id="principalDisplay" class="text-5xl font-black italic tracking-tighter">$0</h2>
            </div>
            <div class="glass p-8 rounded-3xl border-l-4 border-emerald-500">
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Net Yield</p>
                <h2 id="liveProfit" class="text-5xl font-black text-emerald-400 italic tracking-tighter">$0.0000</h2>
            </div>
            <div class="glass p-8 rounded-3xl border-l-4 border-indigo-500">
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Kernel Status</p>
                <h2 id="statusLabel" class="text-4xl font-black text-white italic uppercase tracking-tighter">STANDBY</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-4 glass p-10 rounded-3xl">
                <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-sky-500 mb-8 text-center">Deployment Controls</h3>
                <div class="space-y-10">
                    <div>
                        <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-4">
                            <span>Allocation Range</span>
                            <span id="amtVal" class="text-white">$10,000</span>
                        </div>
                        <input type="range" id="amtRange" min="10000" max="1000000" step="5000" value="10000" 
                               class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                               oninput="document.getElementById('amtVal').innerText = '$'+parseInt(this.value).toLocaleString()">
                    </div>
                    <button id="deployBtn" onclick="initKernel()" class="w-full py-5 accent-gradient text-white font-black rounded-2xl text-[11px] uppercase tracking-[0.2em] btn-shadow hover:scale-[1.02] active:scale-95 transition-all">
                        Initialize ALM Kernel
                    </button>
                </div>
            </div>

            <div class="lg:col-span-8 glass p-10 rounded-3xl">
                <div class="flex justify-between items-center mb-6 border-b border-white/5 pb-6 font-mono">
                    <p id="activeWallet" class="text-[10px] text-slate-500 uppercase tracking-widest">Awaiting Identity...</p>
                    <div class="flex items-center gap-2">
                        <div id="statusDot" class="w-2 h-2 rounded-full bg-slate-700"></div>
                        <span id="auditText" class="text-[9px] font-bold text-slate-500 uppercase">Audit Standby</span>
                    </div>
                </div>
                <div id="logOutput" class="font-mono text-[11px] space-y-4 max-h-[350px] overflow-y-auto pr-4"></div>
            </div>
        </div>
    </main>

    <footer class="max-w-7xl w-full mx-auto mt-20 pt-12 border-t border-white/5 flex flex-col md:flex-row justify-between gap-12 opacity-60 hover:opacity-100 transition-opacity">
        <div class="flex-1">
            <h4 class="text-xs font-black text-slate-400 uppercase tracking-[0.3em] mb-6">Traditional Banking Gateways</h4>
            <div onclick="openPlaid()" class="glass p-6 rounded-2xl flex items-center justify-between group cursor-pointer hover:bg-white/5 max-w-sm">
                <div>
                    <p class="text-[10px] font-bold text-white uppercase tracking-widest">Connect Bank (Plaid)</p>
                    <p class="text-[9px] text-slate-500 mt-1">Non-custodial bank settlements</p>
                </div>
                <div class="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center text-xs group-hover:bg-white group-hover:text-black transition-all">→</div>
            </div>
        </div>
        <div id="demoContainer" class="text-right">
             <button id="demoBtn" onclick="toggleDemo()" class="text-slate-600 hover:text-sky-500 text-[10px] font-bold uppercase tracking-widest transition-colors">Access Demo Sandbox</button>
             <button id="stopDemoBtn" onclick="disconnect()" class="hidden bg-red-500/10 text-red-500 border border-red-500/20 px-6 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-red-500 hover:text-white transition-all">Stop Demo & Exit Sandbox</button>
             <p class="text-[9px] text-slate-700 mt-2 tracking-widest">VAULTLOGIC V3.6 CORE</p>
        </div>
    </footer>

    <script>
        let walletAddress = null;
        let syncTimer = null;
        let isDemoMode = false;
        // Fix for Checksum Error: Direct string reference
        const DEMO_ADDR = "{DEMO_ADDRESS_STR}";

        function openPlaid() {{
            document.getElementById('plaidModal').classList.remove('hidden');
            document.getElementById('plaidModal').classList.add('flex');
        }}

        function closePlaid() {{
            document.getElementById('plaidModal').classList.add('hidden');
            document.getElementById('plaidModal').classList.remove('flex');
        }}

        function simulatePlaidSuccess() {{
            closePlaid();
            const logOutput = document.getElementById('logOutput');
            logOutput.innerHTML = `
                <div class="p-4 border-l-2 border-emerald-500 bg-emerald-500/5">
                    <span class="text-emerald-500 font-bold uppercase mr-3">PLAID:</span>
                    <span class="text-slate-300 uppercase">CHASE BANK LINKED SUCCESSFULLY. READY FOR FIAT SETTLEMENT.</span>
                </div>
            ` + logOutput.innerHTML;
        }}

        function disconnect() {{
            walletAddress = null;
            isDemoMode = false;
            if (syncTimer) clearInterval(syncTimer);
            
            document.getElementById('mainDash').classList.add('opacity-20', 'pointer-events-none');
            const authBtn = document.getElementById('authBtn');
            authBtn.innerText = "Connect Wallet";
            authBtn.classList.remove('bg-sky-600', 'text-white');
            authBtn.classList.add('bg-white', 'text-black');
            authBtn.disabled = false;
            
            document.getElementById('demoBtn').classList.remove('hidden');
            document.getElementById('stopDemoBtn').classList.add('hidden');
            document.getElementById('disconnectBtn').classList.add('hidden');
            
            document.getElementById('activeWallet').innerText = "Awaiting Identity...";
            document.getElementById('statusDot').classList.replace('bg-emerald-500', 'bg-slate-700');
            document.getElementById('auditText').classList.replace('text-emerald-500', 'text-slate-500');
            document.getElementById('auditText').innerText = "Audit Standby";
            document.getElementById('principalDisplay').innerText = "$0";
            document.getElementById('liveProfit').innerText = "$0.0000";
            document.getElementById('logOutput').innerHTML = "";
            
            const dBtn = document.getElementById('deployBtn');
            dBtn.innerText = "Initialize ALM Kernel";
            dBtn.classList.add('accent-gradient');
            dBtn.classList.remove('bg-emerald-600', 'bg-red-900');
            dBtn.disabled = false;
        }}

        function toggleDemo() {{
            isDemoMode = true;
            walletAddress = DEMO_ADDR;
            document.getElementById('demoBtn').classList.add('hidden');
            document.getElementById('stopDemoBtn').classList.remove('hidden');
            updateUIForIdentity("DEMO SESSION");
        }}

        async function toggleAuth() {{
            if (isDemoMode) return;
            if (typeof window.ethereum === 'undefined') {{
                alert("Metamask/Wallet required for production access.");
                return;
            }}
            try {{
                const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                if (accounts.length > 0) {{
                    isDemoMode = false;
                    walletAddress = accounts[0];
                    updateUIForIdentity("PRODUCTION");
                }}
            }} catch (e) {{ console.error(e); }}
        }}

        function updateUIForIdentity(statusText) {{
            const btn = document.getElementById('authBtn');
            const disBtn = document.getElementById('disconnectBtn');
            const displayAddr = walletAddress.slice(0,6).toUpperCase() + "..." + walletAddress.slice(-4).toUpperCase();
            
            if(isDemoMode) {{
                btn.innerText = "DEMO ACTIVE";
                btn.classList.remove('bg-white', 'text-black');
                btn.classList.add('bg-sky-600', 'text-white');
                btn.disabled = true;
            }} else {{
                btn.innerText = displayAddr;
                btn.classList.remove('bg-sky-600');
                btn.classList.add('bg-white');
                btn.disabled = false;
                disBtn.classList.remove('hidden');
            }}
            
            document.getElementById('activeWallet').innerText = "IDENT: " + walletAddress.toUpperCase();
            document.getElementById('statusLabel').innerText = statusText;
            document.getElementById('mainDash').classList.remove('opacity-20', 'pointer-events-none');
            
            document.getElementById('statusDot').classList.replace('bg-slate-700', 'bg-emerald-500');
            document.getElementById('auditText').classList.replace('text-slate-500', 'text-emerald-500');
            document.getElementById('auditText').innerText = "Live Audit";

            startSync();
        }}

        async function initKernel() {{
            const amount = document.getElementById('amtRange').value;
            const btn = document.getElementById('deployBtn');
            btn.innerText = "VERIFYING COLLATERAL...";
            btn.disabled = true;

            try {{
                const res = await fetch('/activate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ 
                        address: walletAddress, 
                        amount: parseFloat(amount),
                        is_demo: isDemoMode
                    }})
                }});
                const data = await res.json();
                if (data.status === "success") {{
                    btn.innerText = "KERNEL ACTIVE";
                    btn.classList.replace('accent-gradient', 'bg-emerald-600');
                    document.getElementById('statusLabel').innerText = "DEPLOYED";
                }} else {{
                    btn.innerText = data.message.toUpperCase();
                    btn.classList.replace('accent-gradient', 'bg-red-900');
                    setTimeout(() => {{ 
                        btn.innerText = "Initialize ALM Kernel"; 
                        btn.disabled = false; 
                        btn.classList.add('accent-gradient');
                        btn.classList.remove('bg-red-900');
                    }}, 4000);
                }}
            }} catch (e) {{ btn.innerText = "SERVER ERROR"; btn.disabled = false; }}
        }}

        function startSync() {{
            if (syncTimer) clearInterval(syncTimer);
            syncTimer = setInterval(async () => {{
                if (!walletAddress) return;
                try {{
                    const res = await fetch('/stats/' + walletAddress);
                    const data = await res.json();
                    if (data.stats) {{
                        document.getElementById('principalDisplay').innerText = '$' + data.stats.principal.toLocaleString();
                        document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {{minimumFractionDigits: 4}});
                    }}
                    const logOutput = document.getElementById('logOutput');
                    logOutput.innerHTML = data.logs.map(l => `
                        <div class="p-4 border-l-2 border-slate-800 bg-white/[0.02]">
                            <span class="text-sky-500 font-bold uppercase mr-3">KERNEL:</span>
                            <span class="text-slate-300 uppercase">${{l.split('KERNEL: ')[1] || l}}</span>
                        </div>
                    `).reverse().join('');
                }} catch (e) {{}}
            }}, 3000);
        }}
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)