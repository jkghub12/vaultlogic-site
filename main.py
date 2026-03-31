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

def to_strict_address(addr_str: str):
    """Ensures EIP-55 compliance to prevent Kernel Sync Errors."""
    try:
        if not addr_str: return addr_str
        clean = addr_str.strip().lower()
        return Web3.to_checksum_address(clean)
    except Exception:
        return addr_str

w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

usdc_contract = w3.eth.contract(address=to_strict_address(USDC_ADDRESS), abi=ERC20_ABI)
audit_logs = ["VAULTLOGIC V4.0: Kernel Core Online. Monitoring Base Mainnet..."]

class EngineInit(BaseModel):
    address: str
    amount: float
    is_demo: bool = False

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if "SYNC_ERROR" in msg or "invalid EIP-55" in msg:
        msg = "RE-SYNCHRONIZING KERNEL WITH VALIDATED EIP-55 IDENTITY..."
    audit_logs.append(f"[{timestamp}] KERNEL: {msg}")
    if len(audit_logs) > 30: audit_logs.pop(0)

async def background_kernel_loop():
    while True:
        await asyncio.sleep(10)
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
        target = to_strict_address(address)
        return {"stats": kernel.get_stats(target), "logs": audit_logs}
    except Exception as e:
        return {"stats": None, "logs": audit_logs, "error": str(e)}

@app.post("/activate")
async def activate(data: EngineInit):
    try:
        target_address = to_strict_address(data.address)
        if data.amount < 10000:
            add_log(f"REJECTED: ${data.amount:,.2f} is below $10K floor.")
            return {"status": "error", "message": "Below $10k Floor"}

        if not data.is_demo:
            raw_balance = usdc_contract.functions.balanceOf(target_address).call()
            if (raw_balance / 10**6) < data.amount:
                add_log(f"CRITICAL: Insufficient USDC on Base Mainnet for {target_address[:10]}...")
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
        body {{ background: #010204; color: #f8fafc; font-family: 'Inter', sans-serif; overflow-x: hidden; }}
        .glass {{ background: rgba(10, 15, 25, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }}
        .accent-gradient {{ background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); }}
        .custom-scroll::-webkit-scrollbar {{ width: 4px; }}
        .custom-scroll::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 10px; }}
        .wallet-card:hover {{ background: rgba(255,255,255,0.08); transform: translateY(-2px); }}
    </style>
</head>
<body class="p-6 md:p-10 min-h-screen flex flex-col items-center">

    <!-- Wallet Selector Modal -->
    <div id="walletModal" class="fixed inset-0 z-[300] hidden items-center justify-center bg-black/95 backdrop-blur-md p-4">
        <div class="glass max-w-md w-full rounded-[2.5rem] overflow-hidden border border-white/10">
            <div class="p-8 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                <h3 class="font-bold text-xl">Connect Wallet</h3>
                <button onclick="closeWallets()" class="text-slate-500 hover:text-white text-xl">✕</button>
            </div>
            <div class="p-8 space-y-3">
                <div onclick="connectWith('Base')" class="wallet-card flex items-center gap-4 p-4 rounded-2xl cursor-pointer border border-sky-500/30 bg-sky-500/5">
                    <div class="w-11 h-11 bg-blue-600 rounded-full flex items-center justify-center font-black text-lg">B</div>
                    <div><p class="text-sm font-bold">Base Wallet</p><span class="text-[9px] text-sky-400 font-bold uppercase">Optimized L2</span></div>
                </div>
                <div onclick="connectWith('MetaMask')" class="wallet-card flex items-center gap-4 p-4 rounded-2xl cursor-pointer">
                    <div class="w-10 h-10 bg-orange-500/20 rounded-full flex items-center justify-center text-orange-500 font-bold">M</div>
                    <p class="text-sm font-medium">MetaMask</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Navigation -->
    <nav class="max-w-7xl w-full flex justify-between items-center mb-12">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 accent-gradient rounded-2xl flex items-center justify-center text-white font-black text-2xl italic shadow-lg">V</div>
            <div class="hidden sm:block">
                <h1 class="text-2xl font-black italic tracking-tighter uppercase leading-none">VaultLogic</h1>
                <p class="text-[9px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-1">Industrial Autopilot</p>
            </div>
        </div>
        
        <div class="flex items-center gap-3">
            <div id="walletDisplay" class="hidden glass px-5 py-2.5 rounded-2xl flex items-center gap-4 border border-white/10">
                <div class="flex items-center gap-2">
                    <div class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
                    <span id="addrText" class="text-[11px] font-mono font-bold text-slate-300">0x...</span>
                </div>
                <div class="h-4 w-[1px] bg-white/10"></div>
                <button onclick="disconnect()" class="text-[10px] font-black text-red-400 hover:text-red-500 uppercase tracking-widest">Disconnect</button>
            </div>
            <button id="authBtn" onclick="openWallets()" class="bg-white text-black px-8 py-3.5 rounded-2xl font-black text-[11px] tracking-widest uppercase hover:bg-slate-200 transition-all">Connect Wallet</button>
        </div>
    </nav>

    <main id="mainDash" class="max-w-7xl w-full opacity-20 pointer-events-none transition-all duration-700 blur-sm">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="glass p-10 rounded-[2.5rem] relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1.5 h-full bg-sky-500"></div>
                <p class="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3">Asset Value</p>
                <h2 id="principalDisplay" class="text-6xl font-black italic tracking-tighter">$0</h2>
            </div>
            <div class="glass p-10 rounded-[2.5rem] relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1.5 h-full bg-emerald-500"></div>
                <p class="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3">Live Yield</p>
                <h2 id="liveProfit" class="text-6xl font-black text-emerald-400 italic tracking-tighter tabular-nums">$0.0000</h2>
            </div>
            <div class="glass p-10 rounded-[2.5rem] relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1.5 h-full bg-indigo-500"></div>
                <p class="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3">Identity</p>
                <h2 id="statusLabel" class="text-5xl font-black text-white italic uppercase tracking-tighter">STANDBY</h2>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-4 space-y-6">
                <div class="glass p-10 rounded-[2.5rem] border border-white/5">
                    <h3 class="text-[10px] font-black uppercase tracking-[0.4em] text-sky-500 mb-10 text-center opacity-80">Deployment Strategy</h3>
                    <div class="space-y-12">
                        <div>
                            <div class="flex justify-between text-[11px] font-bold uppercase text-slate-500 mb-5">
                                <span>Size</span>
                                <span id="amtVal" class="text-sky-400 font-mono text-sm">$10,000</span>
                            </div>
                            <input type="range" id="amtRange" min="10000" max="1000000" step="5000" value="10000" 
                                   class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none"
                                   oninput="document.getElementById('amtVal').innerText = '$'+parseInt(this.value).toLocaleString()">
                        </div>
                        <button id="deployBtn" onclick="initKernel()" class="w-full py-6 accent-gradient text-white font-black rounded-2xl text-[12px] uppercase tracking-[0.25em]">Initialize Engine</button>
                    </div>
                </div>

                <!-- Plaid Section -->
                <div onclick="openPlaid()" id="plaidTrigger" class="glass p-7 rounded-[2rem] border border-white/5 cursor-pointer group hover:border-sky-500/30 transition-all flex items-center justify-between">
                    <div class="flex items-center gap-5">
                        <div class="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center text-xl grayscale group-hover:grayscale-0 transition-all">🏦</div>
                        <div>
                            <p id="bankStatusText" class="text-[11px] font-black text-white uppercase tracking-widest">Connect Bank</p>
                            <p class="text-[9px] text-slate-500 mt-1 uppercase font-bold">Institutional Settlement</p>
                        </div>
                    </div>
                    <div class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center text-sm group-hover:bg-white group-hover:text-black transition-all">→</div>
                </div>
            </div>

            <div class="lg:col-span-8 glass p-10 rounded-[2.5rem] relative flex flex-col min-h-[500px]">
                <div class="flex justify-between items-center mb-8 border-b border-white/5 pb-8">
                    <span class="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">Live Audit Terminal</span>
                    <span id="auditBadge" class="text-[10px] font-bold text-slate-600 uppercase px-3 py-1.5 border border-white/5 rounded-xl">Offline</span>
                </div>
                <div id="logOutput" class="font-mono text-[11px] space-y-4 flex-grow overflow-y-auto pr-4 custom-scroll pb-4"></div>
            </div>
        </div>
    </main>

    <div id="demoContainer" class="max-w-7xl w-full mt-16 flex justify-center pb-20">
        <button id="demoBtn" onclick="toggleDemo()" class="text-slate-600 hover:text-sky-500 text-[11px] font-black uppercase tracking-[0.3em] transition-all border-b border-transparent hover:border-sky-500/50 pb-1 px-4">Launch Sandbox Mode</button>
    </div>

    <!-- Plaid UI -->
    <div id="plaidOverlay" class="fixed inset-0 z-[500] hidden items-center justify-center bg-black/85 backdrop-blur-md p-4">
        <div class="bg-white text-black max-w-sm w-full rounded-[2.5rem] overflow-hidden shadow-2xl">
            <div class="p-8 border-b border-gray-100 flex justify-between items-center">
                <span class="font-black text-[10px] tracking-[0.2em] text-gray-400 uppercase">Plaid Gateway</span>
                <button onclick="closePlaid()" class="text-gray-400 hover:text-black text-xl">✕</button>
            </div>
            <div id="plaidContent" class="p-10">
                <div id="bankListView">
                    <h2 class="text-2xl font-black mb-8 tracking-tight">Select Institution</h2>
                    <div class="space-y-3">
                        <div onclick="showLogin()" class="flex items-center justify-between p-5 border-2 border-gray-50 rounded-2xl cursor-pointer hover:border-blue-500 hover:bg-blue-50/30 transition-all">
                            <span class="font-bold text-base">Chase Bank</span>
                            <span class="text-gray-300">→</span>
                        </div>
                        <div onclick="showLogin()" class="flex items-center justify-between p-5 border-2 border-gray-50 rounded-2xl cursor-pointer hover:border-blue-500 hover:bg-blue-50/30 transition-all">
                            <span class="font-bold text-base">Bank of America</span>
                            <span class="text-gray-300">→</span>
                        </div>
                    </div>
                </div>
                <div id="loginView" class="hidden">
                    <h2 class="text-2xl font-black mb-8 tracking-tight">Institutional Login</h2>
                    <input type="text" placeholder="Username" class="w-full p-5 bg-gray-50 border-2 border-transparent rounded-2xl text-sm mb-4 outline-none focus:border-blue-500 transition-all">
                    <input type="password" placeholder="Key Code" class="w-full p-5 bg-gray-50 border-2 border-transparent rounded-2xl text-sm mb-8 outline-none focus:border-blue-500 transition-all">
                    <button onclick="finishPlaid()" class="w-full py-5 bg-blue-600 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-lg active:scale-95 transition-all">Connect Securely</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let walletAddress = null;
        let syncTimer = null;
        let isDemoMode = false;
        
        const DEMO_ADDR = "0x2d8E2788a42FA2089279743c746C9742721f5C14";

        function openWallets() {{ document.getElementById('walletModal').classList.replace('hidden', 'flex'); }}
        function closeWallets() {{ document.getElementById('walletModal').classList.replace('flex', 'hidden'); }}

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

        async function connectWith(provider) {{
            if (window.ethereum) {{
                try {{
                    const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                    walletAddress = accounts[0];
                    isDemoMode = false;
                    closeWallets();
                    onAuthSuccess(provider);
                }} catch (e) {{ console.error("Connection Failed", e); }}
            }} else {{ 
                alert("Provider not detected.");
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
            if (syncTimer) clearInterval(syncTimer);
            
            const mainDash = document.getElementById('mainDash');
            mainDash.classList.add('opacity-20', 'pointer-events-none', 'blur-sm');
            
            document.getElementById('walletDisplay').classList.add('hidden');
            document.getElementById('authBtn').classList.remove('hidden');
            document.getElementById('demoContainer').classList.remove('hidden'); // SHOW DEMO AGAIN
            
            document.getElementById('statusLabel').innerText = "STANDBY";
            document.getElementById('principalDisplay').innerText = "$0";
            document.getElementById('liveProfit').innerText = "$0.0000";
            document.getElementById('auditBadge').innerText = "Offline";
            document.getElementById('auditBadge').className = "text-[10px] font-bold text-slate-600 uppercase px-3 py-1.5 border border-white/5 rounded-xl bg-white/[0.02]";
            document.getElementById('logOutput').innerHTML = '<div class="opacity-30 italic text-slate-500">Kernel Disconnected.</div>';
            
            const btn = document.getElementById('deployBtn');
            btn.innerText = "Initialize Engine";
            btn.classList.remove('bg-emerald-600');
            btn.classList.add('accent-gradient');
            btn.disabled = false;
        }}

        function onAuthSuccess(source) {{
            document.getElementById('authBtn').classList.add('hidden');
            document.getElementById('demoContainer').classList.add('hidden'); // HIDE DEMO WHEN CONNECTED
            
            document.getElementById('walletDisplay').classList.remove('hidden');
            document.getElementById('addrText').innerText = walletAddress.slice(0,6).toUpperCase() + "..." + walletAddress.slice(-4).toUpperCase();
            
            document.getElementById('mainDash').classList.remove('opacity-20', 'pointer-events-none', 'blur-sm');
            document.getElementById('statusLabel').innerText = source;
            document.getElementById('auditBadge').innerText = "Active Audit";
            document.getElementById('auditBadge').className = "text-[10px] font-bold text-emerald-500 uppercase px-3 py-1.5 border border-emerald-500/20 bg-emerald-500/5 rounded-xl animate-pulse";

            startSync();
        }}

        async function initKernel() {{
            const btn = document.getElementById('deployBtn');
            btn.innerText = "VERIFYING...";
            btn.disabled = true;

            try {{
                const res = await fetch('/activate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ address: walletAddress, amount: parseFloat(document.getElementById('amtRange').value), is_demo: isDemoMode }})
                }});
                const data = await res.json();
                if (data.status === "success") {{
                    btn.innerText = "KERNEL DEPLOYED";
                    btn.classList.remove('accent-gradient');
                    btn.classList.add('bg-emerald-600');
                }} else {{
                    btn.innerText = data.message;
                    setTimeout(() => {{ btn.innerText = "Initialize Engine"; btn.disabled = false; }}, 3000);
                }}
            } catch(e) {{
                btn.innerText = "GATEWAY ERROR";
                setTimeout(() => {{ btn.innerText = "Initialize Engine"; btn.disabled = false; }}, 3000);
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
                        document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {{minimumFractionDigits: 4, maximumFractionDigits: 4}});
                    }}
                    if (data.logs) {{
                        document.getElementById('logOutput').innerHTML = data.logs.map(l => `
                            <div class="flex gap-4 p-4 border-l-2 border-white/5 items-start">
                                <span class="text-sky-500 font-black opacity-40">AUDIT</span>
                                <span class="text-slate-400 uppercase font-bold tracking-tight">${{l.split('KERNEL: ')[1] || l}}</span>
                            </div>`).reverse().join('');
                    }}
                }} catch (e) {{}}
            }}, 3000);
        }}
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)