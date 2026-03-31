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

# HARDCODED CHECKSUMMED ADDRESS (EIP-55)
DEMO_ADDRESS_STR = "0x2d8E2788a42FA2089279743c746C9742721f5C14"

w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]
usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)

audit_logs = ["VAULTLOGIC V3.8-STABLE: Industrial Gateway Ready."]

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
        # Periodic sync and kernel ticking
        for addr in list(kernel.active_deployments.keys()):
            try:
                msg = kernel.active_deployments[addr].calculate_tick(10)
                if msg: add_log(msg)
            except:
                pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_kernel_loop())

@app.get("/stats/{address}")
async def get_stats(address: str):
    try:
        # Force checksum conversion immediately to solve the EIP-55 error
        safe_addr = Web3.to_checksum_address(address)
        return {
            "stats": kernel.get_stats(safe_addr),
            "logs": audit_logs
        }
    except Exception as e:
        # If we still get a checksum error, we report it cleanly
        return {"stats": None, "logs": audit_logs, "error": f"ADDR_ERR: {str(e)}"}

@app.post("/activate")
async def activate(data: EngineInit):
    try:
        target_address = Web3.to_checksum_address(data.address)
        
        # Floor check: $10,000 Minimum
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
        return {"status": "error", "message": "Address/Network Error"}

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
        
        .plaid-modal-enter {{ animation: slideUp 0.3s ease-out; }}
        @keyframes slideUp {{ from {{ transform: translateY(20px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
    </style>
</head>
<body class="p-6 md:p-10 min-h-screen flex flex-col">
    <!-- Updated Plaid Simulation UI -->
    <div id="plaidOverlay" class="fixed inset-0 z-[100] hidden items-center justify-center bg-black/80 backdrop-blur-sm p-4">
        <div id="plaidContainer" class="bg-white text-black max-w-sm w-full rounded-2xl overflow-hidden plaid-modal-enter shadow-2xl">
            <!-- Header -->
            <div class="p-6 border-b border-gray-100 flex justify-between items-center">
                <div class="flex items-center gap-2">
                    <div class="w-6 h-6 bg-black rounded flex items-center justify-center">
                        <div class="w-2 h-2 bg-white rounded-full"></div>
                    </div>
                    <span class="font-bold text-sm tracking-tight">Plaid</span>
                </div>
                <button onclick="closePlaid()" class="text-gray-400 hover:text-black">✕</button>
            </div>

            <!-- Content Area (Switchable) -->
            <div id="plaidContent" class="p-6">
                <!-- Select Bank View -->
                <div id="bankListView">
                    <h2 class="text-xl font-semibold mb-1">Select your bank</h2>
                    <p class="text-xs text-gray-500 mb-6">VaultLogic uses Plaid to link your account.</p>
                    <div class="space-y-2">
                        <div onclick="showLogin('Chase')" class="flex items-center justify-between p-3 border rounded-xl cursor-pointer hover:bg-gray-50 transition-colors">
                            <span class="font-medium text-sm">Chase</span>
                            <span class="text-gray-300">→</span>
                        </div>
                        <div onclick="showLogin('Bank of America')" class="flex items-center justify-between p-3 border rounded-xl cursor-pointer hover:bg-gray-50 transition-colors">
                            <span class="font-medium text-sm">Bank of America</span>
                            <span class="text-gray-300">→</span>
                        </div>
                        <div onclick="showLogin('Wells Fargo')" class="flex items-center justify-between p-3 border rounded-xl cursor-pointer hover:bg-gray-50 transition-colors">
                            <span class="font-medium text-sm">Wells Fargo</span>
                            <span class="text-gray-300">→</span>
                        </div>
                    </div>
                </div>

                <!-- Login View -->
                <div id="loginView" class="hidden">
                    <h2 id="loginTitle" class="text-xl font-semibold mb-1">Log in to Bank</h2>
                    <p class="text-xs text-gray-500 mb-6">Enter your credentials to link accounts.</p>
                    <div class="space-y-3">
                        <input type="text" placeholder="Username" class="w-full p-3 border rounded-lg text-sm bg-gray-50 outline-none focus:ring-2 focus:ring-blue-500">
                        <input type="password" placeholder="Password" class="w-full p-3 border rounded-lg text-sm bg-gray-50 outline-none focus:ring-2 focus:ring-blue-500">
                        <button onclick="submitPlaidLogin()" class="w-full py-3 bg-black text-white rounded-xl font-bold text-sm mt-4">Submit</button>
                    </div>
                </div>

                <!-- Loading View -->
                <div id="loadingView" class="hidden py-10 text-center">
                    <div class="inline-block w-8 h-8 border-4 border-gray-200 border-t-black rounded-full animate-spin mb-4"></div>
                    <p class="text-sm font-medium">Verifying with Institution...</p>
                </div>
            </div>
            
            <div class="bg-gray-50 p-4 text-center">
                <p class="text-[10px] text-gray-400 font-medium">PLAID • SECURE AND ENCRYPTED</p>
            </div>
        </div>
    </div>

    <nav class="max-w-7xl w-full mx-auto flex justify-between items-center mb-12">
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 accent-gradient rounded-xl flex items-center justify-center text-white font-black text-xl italic">V</div>
            <div>
                <h1 class="text-xl font-black italic tracking-tighter uppercase leading-none">VaultLogic</h1>
                <p class="text-[8px] text-slate-500 font-bold uppercase tracking-[0.3em] mt-1">Industrial Autopilot</p>
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
                    <p class="text-[9px] text-center text-slate-600 uppercase tracking-widest">Min. Institutional Deposit: $10,000 USD</p>
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
                    <p id="bankStatusText" class="text-[10px] font-bold text-white uppercase tracking-widest">Connect Bank (Plaid)</p>
                    <p id="bankSubtext" class="text-[9px] text-slate-500 mt-1 uppercase tracking-wider">Non-custodial bank settlements</p>
                </div>
                <div id="bankStatusIcon" class="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center text-xs group-hover:bg-white group-hover:text-black transition-all">→</div>
            </div>
        </div>
        <div id="demoContainer" class="text-right">
             <button id="demoBtn" onclick="toggleDemo()" class="text-slate-600 hover:text-sky-500 text-[10px] font-bold uppercase tracking-widest transition-colors">Access Demo Sandbox</button>
             <button id="stopDemoBtn" onclick="disconnect()" class="hidden bg-red-500/10 text-red-500 border border-red-500/20 px-6 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-red-500 hover:text-white transition-all">Stop Demo & Exit Sandbox</button>
             <p class="text-[9px] text-slate-700 mt-2 tracking-widest uppercase">VaultLogic V3.8 Core</p>
        </div>
    </footer>

    <script>
        let walletAddress = null;
        let syncTimer = null;
        let isDemoMode = false;
        let activeBank = null;
        
        // Exact checksummed address used in backend too
        const DEMO_ADDR = "0x2d8E2788a42FA2089279743c746C9742721f5C14";

        function openPlaid() {{
            document.getElementById('plaidOverlay').classList.remove('hidden');
            document.getElementById('plaidOverlay').classList.add('flex');
            document.getElementById('bankListView').classList.remove('hidden');
            document.getElementById('loginView').classList.add('hidden');
            document.getElementById('loadingView').classList.add('hidden');
        }}

        function closePlaid() {{
            document.getElementById('plaidOverlay').classList.add('hidden');
            document.getElementById('plaidOverlay').classList.remove('flex');
        }}

        function showLogin(bank) {{
            activeBank = bank;
            document.getElementById('bankListView').classList.add('hidden');
            document.getElementById('loginTitle').innerText = "Log in to " + bank;
            document.getElementById('loginView').classList.remove('hidden');
        }}

        function submitPlaidLogin() {{
            document.getElementById('loginView').classList.add('hidden');
            document.getElementById('loadingView').classList.remove('hidden');
            
            setTimeout(() => {{
                closePlaid();
                // Generate a temporary VaultLogic Deposit Wallet Address for this bank session
                const tempWallet = "0x" + Array.from({{length: 40}}, () => Math.floor(Math.random() * 16).toString(16)).join('');
                
                document.getElementById('bankStatusText').innerText = activeBank + " CONNECTED";
                document.getElementById('bankStatusText').classList.add('text-emerald-400');
                document.getElementById('bankSubtext').innerText = "Gateway Wallet: " + tempWallet.slice(0,10) + "...";
                document.getElementById('bankStatusIcon').innerHTML = "✓";
                document.getElementById('bankStatusIcon').classList.add('bg-emerald-500', 'text-white', 'border-none');
                
                addLocalLog("PLAID", `${{activeBank.toUpperCase()}} AUTHENTICATED. USD LIQUIDITY TUNNEL ACTIVE VIA ${{tempWallet.toUpperCase()}}.`);
            }}, 1800);
        }}

        function addLocalLog(type, msg) {{
            const logOutput = document.getElementById('logOutput');
            const time = new Date().toLocaleTimeString('en-GB', {{ hour12: false }});
            logOutput.innerHTML = `
                <div class="p-4 border-l-2 border-emerald-500 bg-emerald-500/5">
                    <span class="text-emerald-500 font-bold uppercase mr-3">PLAID:</span>
                    <span class="text-slate-300 uppercase">[${{time}}] ${{msg}}</span>
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
            
            // Reset Bank Status
            document.getElementById('bankStatusText').innerText = "Connect Bank (Plaid)";
            document.getElementById('bankSubtext').innerText = "Non-custodial bank settlements";
            document.getElementById('bankStatusText').classList.remove('text-emerald-400');
            document.getElementById('bankStatusIcon').innerHTML = "→";
            document.getElementById('bankStatusIcon').classList.remove('bg-emerald-500', 'text-white', 'border-none');

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
                    
                    if (data.error) {{
                        console.error("Backend Error:", data.error);
                    }}

                    if (data.stats) {{
                        document.getElementById('principalDisplay').innerText = '$' + data.stats.principal.toLocaleString();
                        document.getElementById('liveProfit').innerText = '$' + data.stats.net_profit.toLocaleString(undefined, {{minimumFractionDigits: 4}});
                    }}
                    
                    const logOutput = document.getElementById('logOutput');
                    logOutput.innerHTML = data.logs.map(l => {{
                        const isPlaid = l.includes('PLAID:');
                        return `
                            <div class="p-4 border-l-2 ${{isPlaid ? 'border-emerald-500 bg-emerald-500/5' : 'border-slate-800 bg-white/[0.02]'}}">
                                <span class="${{isPlaid ? 'text-emerald-500' : 'text-sky-500'}} font-bold uppercase mr-3">${{isPlaid ? 'PLAID' : 'KERNEL'}}:</span>
                                <span class="text-slate-300 uppercase">${{l.split('KERNEL: ')[1] || l.split('PLAID: ')[1] || l}}</span>
                            </div>
                        `;
                    }}).reverse().join('');
                }} catch (e) {{}}
            }}, 3000);
        }}
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)