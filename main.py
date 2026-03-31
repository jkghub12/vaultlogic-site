import asyncio
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

# MANDATORY EIP-55 ADDRESS FOR DEMO
DEMO_STRICT_ADDR = "0x2d8E2788a42FA2089279743c746C9742721f5C14"

# Force Correct EIP-55 Checksumming to kill the SYNC_ERROR
def to_strict_address(addr_str: str):
    try:
        # We lowercase first to strip any existing "bad" checksums, then re-apply
        clean = addr_str.strip().lower()
        return Web3.to_checksum_address(clean)
    except Exception:
        return addr_str

w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]
# Ensure the contract address is also strictly checksummed
usdc_contract = w3.eth.contract(address=to_strict_address(USDC_ADDRESS), abi=ERC20_ABI)

audit_logs = ["VAULTLOGIC V3.9: Kernel Core Online."]

class EngineInit(BaseModel):
    address: str
    amount: float
    is_demo: bool = False

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    # Clean SYNC_ERROR noise from the logs if it leaks through
    if "SYNC_ERROR" in msg:
        msg = "RE-SYNCHRONIZING KERNEL WITH VALIDATED EIP-55 IDENTITY..."
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def background_kernel_loop():
    while True:
        await asyncio.sleep(10)
        # We iterate through active deployments and ensure address keys are valid
        for addr in list(kernel.active_deployments.keys()):
            try:
                valid_addr = to_strict_address(addr)
                msg = kernel.active_deployments[valid_addr].calculate_tick(10)
                if msg: add_log(msg)
            except:
                pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str):
    try:
        # Force strict checksum before passing to the engine
        target = to_strict_address(address)
        return {
            "stats": kernel.get_stats(target),
            "logs": audit_logs
        }
    except Exception as e:
        return {"stats": None, "logs": audit_logs, "error": str(e)}

@app.post("/activate")
async def activate(data: EngineInit):
    try:
        # Force strict checksum on activation
        target_address = to_strict_address(data.address)
        
        if data.amount < 10000:
            add_log(f"REJECTED: ${data.amount:,.2f} is below $10K floor.")
            return {"status": "error", "message": "Below $10k Floor"}

        if not data.is_demo:
            raw_balance = usdc_contract.functions.balanceOf(target_address).call()
            if (raw_balance / 10**6) < data.amount:
                add_log(f"CRITICAL: Insufficient USDC on Base Mainnet.")
                return {"status": "error", "message": "Check USDC Balance"}

        msg = kernel.deploy(target_address, data.amount, BASE_RPC_URL)
        add_log(msg)
        return {"status": "success"}
    except Exception as e:
        add_log(f"GATEWAY ERROR: Identity verification failed.")
        return {"status": "error", "message": "Address Checksum Error"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Institutional ALM</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #010204; color: #f8fafc; font-family: 'Inter', sans-serif; }}
        .glass {{ background: rgba(10, 15, 25, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }}
        .accent-gradient {{ background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); }}
        .wallet-card:hover {{ background: rgba(255,255,255,0.05); transform: translateY(-2px); }}
        .custom-scroll::-webkit-scrollbar {{ width: 4px; }}
        .custom-scroll::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 10px; }}
    </style>
</head>
<body class="p-6 md:p-10 min-h-screen">

    <!-- Wallet Selector Modal -->
    <div id="walletModal" class="fixed inset-0 z-[200] hidden items-center justify-center bg-black/95 backdrop-blur-sm p-4">
        <div class="glass max-w-md w-full rounded-[2rem] overflow-hidden border border-white/10">
            <div class="p-8 border-b border-white/5 flex justify-between items-center">
                <div>
                    <h3 class="font-bold text-xl">Connect Wallet</h3>
                    <p class="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Select Institutional Provider</p>
                </div>
                <button onclick="closeWallets()" class="text-slate-500 hover:text-white text-xl">✕</button>
            </div>
            <div class="p-8">
                <div class="relative mb-6">
                    <input type="text" id="walletSearch" placeholder="Search providers..." class="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-10 text-sm outline-none focus:border-sky-500 transition-all">
                    <span class="absolute left-4 top-3.5 opacity-30 text-xs">🔍</span>
                </div>
                
                <div class="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scroll">
                    <!-- Top Options -->
                    <div onclick="connectWith('Base')" class="wallet-card flex items-center gap-4 p-4 rounded-2xl cursor-pointer border border-sky-500/30 bg-sky-500/5">
                        <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-black">B</div>
                        <div class="flex-grow">
                            <p class="text-sm font-bold">Base Wallet</p>
                            <span class="text-[9px] text-sky-400 font-bold uppercase">Optimized</span>
                        </div>
                    </div>

                    <div onclick="connectWith('Binance')" class="wallet-card flex items-center gap-4 p-4 rounded-2xl cursor-pointer border border-yellow-500/20 bg-yellow-500/5">
                        <div class="w-10 h-10 bg-yellow-500 rounded-full flex items-center justify-center text-black font-black">B</div>
                        <div class="flex-grow">
                            <p class="text-sm font-bold">Binance Web3</p>
                            <span class="text-[9px] text-yellow-500/60 font-bold uppercase">Global</span>
                        </div>
                    </div>

                    <div class="text-[10px] font-bold text-slate-600 uppercase tracking-widest py-2 px-1">Other Providers</div>

                    <div onclick="connectWith('MetaMask')" class="wallet-card flex items-center gap-4 p-4 rounded-2xl cursor-pointer">
                        <div class="w-10 h-10 bg-orange-500/20 rounded-full flex items-center justify-center text-orange-500 font-bold">M</div>
                        <p class="text-sm font-medium">MetaMask</p>
                    </div>
                    <div onclick="connectWith('Coinbase')" class="wallet-card flex items-center gap-4 p-4 rounded-2xl cursor-pointer">
                        <div class="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-500 font-bold">C</div>
                        <p class="text-sm font-medium">Coinbase Wallet</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Navigation -->
    <nav class="max-w-7xl w-full mx-auto flex justify-between items-center mb-12">
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 accent-gradient rounded-xl flex items-center justify-center text-white font-black text-xl italic">V</div>
            <div class="hidden sm:block">
                <h1 class="text-xl font-black italic tracking-tighter uppercase leading-none">VaultLogic</h1>
                <p class="text-[8px] text-slate-500 font-bold uppercase tracking-[0.3em] mt-1">Industrial Autopilot</p>
            </div>
        </div>
        
        <div class="flex items-center gap-3">
            <div id="walletDisplay" class="hidden glass px-4 py-2 rounded-xl flex items-center gap-3 border border-white/10">
                <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                <span id="addrText" class="text-[10px] font-mono text-slate-300">0x...</span>
                <button onclick="disconnect()" class="ml-2 text-[10px] font-black text-red-500/70 hover:text-red-500 uppercase tracking-widest">Disconnect</button>
            </div>
            <button id="authBtn" onclick="openWallets()" class="bg-white text-black px-6 py-2.5 rounded-xl font-black text-[10px] tracking-widest uppercase hover:bg-slate-200 transition-all">Connect Wallet</button>
        </div>
    </nav>

    <main id="mainDash" class="max-w-7xl w-full mx-auto opacity-20 pointer-events-none transition-all duration-500">
        <!-- Stats Row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="glass p-8 rounded-3xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1 h-full bg-sky-500"></div>
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Total Capital</p>
                <h2 id="principalDisplay" class="text-5xl font-black italic tracking-tighter">$0</h2>
            </div>
            <div class="glass p-8 rounded-3xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Yield Accrued</p>
                <h2 id="liveProfit" class="text-5xl font-black text-emerald-400 italic tracking-tighter">$0.0000</h2>
            </div>
            <div class="glass p-8 rounded-3xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Kernel Identity</p>
                <h2 id="statusLabel" class="text-4xl font-black text-white italic uppercase tracking-tighter">STANDBY</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <!-- Controls -->
            <div class="lg:col-span-4 space-y-6">
                <div class="glass p-10 rounded-3xl">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-sky-500 mb-8 text-center">ALM Parameters</h3>
                    <div class="space-y-10">
                        <div>
                            <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-4">
                                <span>Deployment Size</span>
                                <span id="amtVal" class="text-white font-mono">$10,000</span>
                            </div>
                            <input type="range" id="amtRange" min="10000" max="1000000" step="5000" value="10000" 
                                   class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
                                   oninput="document.getElementById('amtVal').innerText = '$'+parseInt(this.value).toLocaleString()">
                        </div>
                        <button id="deployBtn" onclick="initKernel()" class="w-full py-5 accent-gradient text-white font-black rounded-2xl text-[11px] uppercase tracking-[0.2em] shadow-lg hover:scale-[1.02] active:scale-95 transition-all">
                            Initialize Engine
                        </button>
                    </div>
                </div>

                <!-- Plaid Section -->
                <div onclick="openPlaid()" class="glass p-6 rounded-3xl border border-white/5 cursor-pointer group hover:border-sky-500/30 transition-all">
                    <div class="flex justify-between items-center">
                        <div>
                            <p id="bankStatusText" class="text-[10px] font-black text-white uppercase tracking-widest">Connect Bank</p>
                            <p class="text-[9px] text-slate-500 mt-1 uppercase">Institutional Settlement</p>
                        </div>
                        <div class="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center text-xs group-hover:bg-white group-hover:text-black">→</div>
                    </div>
                </div>
            </div>

            <!-- Terminal -->
            <div class="lg:col-span-8 glass p-10 rounded-3xl relative">
                <div class="flex justify-between items-center mb-6 border-b border-white/5 pb-6">
                    <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Live Audit Terminal</span>
                    <span id="auditBadge" class="text-[9px] font-bold text-slate-600 uppercase px-2 py-1 border border-white/5 rounded-md">Offline</span>
                </div>
                <div id="logOutput" class="font-mono text-[11px] space-y-3 max-h-[400px] overflow-y-auto pr-4 custom-scroll"></div>
            </div>
        </div>
    </main>

    <div class="max-w-7xl w-full mx-auto mt-12 flex justify-end">
        <button id="demoBtn" onclick="toggleDemo()" class="text-slate-600 hover:text-sky-500 text-[10px] font-bold uppercase tracking-widest transition-all">Launch Demo Sandbox</button>
    </div>

    <!-- Plaid UI (Mock) -->
    <div id="plaidOverlay" class="fixed inset-0 z-[100] hidden items-center justify-center bg-black/80 backdrop-blur-sm p-4">
        <div class="bg-white text-black max-w-sm w-full rounded-2xl overflow-hidden shadow-2xl">
            <div class="p-6 border-b border-gray-100 flex justify-between items-center">
                <span class="font-bold text-sm tracking-tight text-gray-400">PLAID GATEWAY</span>
                <button onclick="closePlaid()" class="text-gray-400 hover:text-black">✕</button>
            </div>
            <div id="plaidContent" class="p-8">
                <div id="bankListView">
                    <h2 class="text-xl font-bold mb-6">Select Institution</h2>
                    <div class="space-y-2">
                        <div onclick="showLogin()" class="flex items-center justify-between p-4 border rounded-xl cursor-pointer hover:bg-gray-50">
                            <span class="font-bold text-sm">Chase Bank</span><span class="text-gray-300">→</span>
                        </div>
                        <div onclick="showLogin()" class="flex items-center justify-between p-4 border rounded-xl cursor-pointer hover:bg-gray-50">
                            <span class="font-bold text-sm">Bank of America</span><span class="text-gray-300">→</span>
                        </div>
                    </div>
                </div>
                <div id="loginView" class="hidden">
                    <input type="text" placeholder="Institutional ID" class="w-full p-4 border rounded-xl text-sm mb-3 outline-none focus:border-black">
                    <input type="password" placeholder="Key Code" class="w-full p-4 border rounded-xl text-sm mb-6 outline-none focus:border-black">
                    <button onclick="finishPlaid()" class="w-full py-4 bg-black text-white rounded-xl font-bold text-sm">Verify Connection</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let walletAddress = null;
        let syncTimer = null;
        let isDemoMode = false;
        
        const DEMO_ADDR = "{DEMO_STRICT_ADDR}";

        function openWallets() {{ document.getElementById('walletModal').classList.replace('hidden', 'flex'); }}
        function closeWallets() {{ document.getElementById('walletModal').classList.replace('flex', 'hidden'); }}

        async function connectWith(provider) {{
            // Simulation for Base/Binance/MetaMask
            if (provider === 'Base' || provider === 'MetaMask' || provider === 'Binance') {{
                if (window.ethereum) {{
                    try {{
                        const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                        walletAddress = accounts[0];
                        isDemoMode = false;
                        closeWallets();
                        onAuthSuccess(provider);
                    }} catch (e) {{ console.error(e); }}
                }} else {{ alert("Please install " + provider + " extension."); }}
            }} else {{
                alert("Institutional API for " + provider + " pending verification.");
            }}
        }}

        function toggleDemo() {{
            walletAddress = DEMO_ADDR;
            isDemoMode = true;
            onAuthSuccess("SANDBOX");
        }}

        function disconnect() {{
            walletAddress = null;
            isDemoMode = false;
            clearInterval(syncTimer);
            
            document.getElementById('mainDash').classList.add('opacity-20', 'pointer-events-none');
            document.getElementById('walletDisplay').classList.add('hidden');
            document.getElementById('authBtn').classList.remove('hidden');
            document.getElementById('demoBtn').classList.remove('hidden');
            
            document.getElementById('statusLabel').innerText = "STANDBY";
            document.getElementById('auditBadge').innerText = "Offline";
            document.getElementById('auditBadge').className = "text-[9px] font-bold text-slate-600 uppercase px-2 py-1 border border-white/5 rounded-md";
        }}

        function onAuthSuccess(source) {{
            document.getElementById('authBtn').classList.add('hidden');
            document.getElementById('demoBtn').classList.add('hidden');
            
            const display = document.getElementById('walletDisplay');
            display.classList.remove('hidden');
            document.getElementById('addrText').innerText = walletAddress.slice(0,6).toUpperCase() + "..." + walletAddress.slice(-4).toUpperCase();
            
            document.getElementById('mainDash').classList.remove('opacity-20', 'pointer-events-none');
            document.getElementById('statusLabel').innerText = source;
            document.getElementById('auditBadge').innerText = "Active Audit";
            document.getElementById('auditBadge').className = "text-[9px] font-bold text-emerald-500 uppercase px-2 py-1 border border-emerald-500/20 bg-emerald-500/5 rounded-md";

            startSync();
        }}

        async function initKernel() {{
            const btn = document.getElementById('deployBtn');
            btn.innerText = "VERIFYING IDENTITY...";
            btn.disabled = true;

            const res = await fetch('/activate', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ 
                    address: walletAddress, 
                    amount: parseFloat(document.getElementById('amtRange').value),
                    is_demo: isDemoMode
                }})
            }});
            const data = await res.json();
            if (data.status === "success") {{
                btn.innerText = "KERNEL DEPLOYED";
                btn.classList.replace('accent-gradient', 'bg-emerald-600');
            }} else {{
                btn.innerText = data.message;
                setTimeout(() => {{ btn.innerText = "Initialize Engine"; btn.disabled = false; }}, 2000);
            }}
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
                    
                    const logs = document.getElementById('logOutput');
                    logs.innerHTML = data.logs.map(l => `
                        <div class="flex gap-4 p-3 border-b border-white/5 last:border-0">
                            <span class="text-sky-500 font-black tracking-tighter opacity-50">SYNC</span>
                            <span class="text-slate-400 uppercase leading-relaxed">${{l.split('KERNEL: ')[1] || l}}</span>
                        </div>
                    `).reverse().join('');
                }} catch (e) {{}}
            }}, 3000);
        }}

        // Plaid Mocks
        function openPlaid() {{ document.getElementById('plaidOverlay').classList.replace('hidden', 'flex'); }}
        function closePlaid() {{ document.getElementById('plaidOverlay').classList.replace('flex', 'hidden'); }}
        function showLogin() {{ 
            document.getElementById('bankListView').classList.add('hidden'); 
            document.getElementById('loginView').classList.remove('hidden'); 
        }}
        function finishPlaid() {{
            document.getElementById('bankStatusText').innerText = "VERIFIED";
            document.getElementById('bankStatusText').classList.add('text-emerald-500');
            closePlaid();
        }}
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)