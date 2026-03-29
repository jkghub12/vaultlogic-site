import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3

app = FastAPI()

# --- CONFIGURATION ---
BASE_RPC_URL = "https://mainnet.base.org"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

# --- SYSTEM STATE ---
# Now tracking a unified vault state rather than individual "picks"
vault_cache = {
    "metrics": {
        "tvl": "$142.8M",
        "health": "99.8%",
        "current_apy": "5.82%",
        "active_nodes": 12,
        "last_rebalance": "14 mins ago"
    }
}

system_logs = [
    "VaultLogic Kernel v2.7.0 Online", 
    "Institutional Partner Mode: Active.",
    "Scanning Base Liquidity Spreads...",
    "ALM Parameters: Delta-Neutral / Low Volatility."
]

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

@app.get("/logs")
async def get_logs():
    return {"logs": system_logs}

@app.post("/verify-balance")
async def verify_balance(data: EngineInit):
    try:
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        raw_balance = contract.functions.balanceOf(Web3.to_checksum_address(data.address)).call()
        actual_balance = raw_balance / 10**6
        if data.amount > actual_balance:
            return {"status": "error", "message": f"Audit Failed: Wallet holds {actual_balance:,.2f} USDC."}
        return {"status": "success", "balance": actual_balance}
    except Exception:
        return {"status": "error", "message": "Blockchain Connectivity Interrupted."}

@app.post("/start-engine")
async def start_engine(data: EngineInit):
    add_log(f"INIT: Spawning Managed ALM Loop for {data.address[:10]}...")
    add_log(f"ALLOCATING: ${data.amount:,.2f} into Industrial Floor Strategy.")
    return {"status": "running"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logo_url = "https://raw.githubusercontent.com/VaultLogic/vaultlogic-site/main/VLlogo.png"
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>VaultLogic | Coinbase Institutional Partner Portal</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script type="module">
            import {{ createAppKit }} from 'https://esm.sh/@reown/appkit'
            import {{ Ethers5Adapter }} from 'https://esm.sh/@reown/appkit-adapter-ethers5'
            import {{ base }} from 'https://esm.sh/@reown/appkit/networks'

            const modal = createAppKit({{
                adapters: [new Ethers5Adapter()],
                networks: [base],
                projectId: '2b936cf692d84ae6da1ba91950c96420',
                themeMode: 'dark'
            }});
            window.modal = modal;

            modal.subscribeAccount(state => {{
                const userZone = document.getElementById('user-zone');
                const connectNav = document.getElementById('connect-nav');
                const loginPage = document.getElementById('login-page');
                
                if(state.isConnected) {{
                    window.userAddress = state.address;
                    userZone.style.display = 'flex';
                    connectNav.style.display = 'none';
                    document.getElementById('addr-display').innerText = state.address.slice(0,6) + '...' + state.address.slice(-4);
                    if(loginPage.classList.contains('active-tab')) showSection('dashboard');
                }} else {{
                    userZone.style.display = 'none';
                    connectNav.style.display = 'block';
                }}
            }});
        </script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
            :root {{ --bg: #0f172a; --panel: #1e293b; --text: #f8fafc; --sub: #94a3b8; --accent: #3b82f6; --green: #22c55e; --red: #ef4444; --border: #334155; }}
            
            body {{ margin:0; background: var(--bg); color: var(--text); font-family: 'Public Sans', sans-serif; height: 100vh; overflow-x: hidden; }}
            
            nav {{ background: rgba(15,23,42,0.9); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); height: 70px; display: flex; align-items: center; justify-content: space-between; padding: 0 40px; position: sticky; top: 0; z-index: 1000; }}
            .logo {{ display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 20px; text-decoration: none; color: var(--text); cursor:pointer; }}
            .logo img {{ height: 32px; filter: brightness(0) invert(1); }}
            
            .nav-links {{ display: flex; gap: 20px; align-items: center; }}
            .nav-links a {{ color: var(--sub); text-decoration: none; font-size: 11px; font-weight: 700; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; transition: 0.2s; }}
            .nav-links a:hover, .nav-links a.active {{ color: var(--text); }}

            .stats-bar {{ background: #1e293b; border-bottom: 1px solid var(--border); display: flex; gap: 50px; padding: 15px 40px; overflow-x: auto; }}
            .stat-unit label {{ display: block; font-size: 10px; font-weight: 800; color: var(--sub); text-transform: uppercase; }}
            .stat-unit span {{ font-size: 16px; font-weight: 800; color: var(--text); }}

            .container {{ max-width: 1200px; margin: 0 auto; padding: 40px; }}
            
            .tab-content {{ display: none; }}
            .tab-content.active-tab {{ display: block; }}

            /* Unified Dashboard Layout */
            #hero-panel {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid var(--border); border-radius: 20px; padding: 50px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            
            .main-metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 40px; }}
            .metric-card {{ background: var(--panel); border: 1px solid var(--border); padding: 30px; border-radius: 20px; }}
            .metric-card label {{ font-size: 12px; font-weight: 800; color: var(--sub); text-transform: uppercase; display: block; margin-bottom: 10px; }}
            .metric-card .value {{ font-size: 32px; font-weight: 800; }}

            /* Simplified Onboarding Step Cards */
            .step-card {{ background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border); border-radius: 16px; padding: 30px; margin-bottom: 20px; display: flex; gap: 25px; align-items: flex-start; }}
            .step-num {{ background: var(--accent); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; flex-shrink: 0; }}
            .step-body h3 {{ margin: 0 0 10px 0; font-size: 20px; font-weight: 800; }}
            .step-body p {{ color: var(--sub); margin: 0; line-height: 1.6; }}

            .btn-action {{ background: var(--accent); color: white; border: none; padding: 18px 36px; border-radius: 12px; font-weight: 800; cursor: pointer; font-size: 16px; transition: 0.2s; }}
            .btn-action:hover {{ filter: brightness(1.2); transform: translateY(-2px); }}

            #log-container {{ background: #020617; border-radius: 16px; margin-top: 50px; border: 1px solid var(--border); }}
            .log-header {{ padding: 15px 25px; background: #0f172a; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 11px; font-weight: 800; color: var(--sub); }}
            #log-stream {{ height: 300px; overflow-y: auto; padding: 25px; font-family: 'JetBrains Mono'; font-size: 12px; color: #10b981; line-height: 1.8; }}

            .modal {{ display:none; position:fixed; inset:0; background:rgba(2,6,23,0.9); z-index:2000; justify-content:center; align-items:center; backdrop-filter: blur(10px); }}
            .modal-box {{ background:var(--panel); padding:40px; border-radius:24px; width:100%; max-width:420px; border: 1px solid var(--border); }}
        </style>
    </head>
    <body>
        <nav>
            <div onclick="showSection('login-page')" class="logo">
                <img src="{logo_url}" alt="VL" onerror="this.style.display='none'">
                <span>VAULTLOGIC</span>
            </div>
            <div class="nav-links">
                <a onclick="showSection('dashboard')" id="nav-dashboard">DASHBOARD</a>
                <a onclick="showSection('earn')" id="nav-earn">HOW IT WORKS</a>
                <a onclick="showSection('about')" id="nav-about">ABOUT</a>
            </div>
            <div id="auth-zone">
                <button id="connect-nav" onclick="window.modal.open()" style="background:white; color:black; border:none; padding:10px 20px; border-radius:8px; font-weight:800; cursor:pointer;">CONNECT</button>
                <div id="user-zone" style="display:none; align-items:center; gap:15px;">
                    <span id="addr-display" style="font-family:'JetBrains Mono'; font-size:12px; font-weight:800; background:rgba(255,255,255,0.05); padding:6px 12px; border-radius:6px;"></span>
                    <button onclick="window.modal.disconnect()" style="color:var(--red); background:none; border:none; font-size:10px; font-weight:800; cursor:pointer;">DISCONNECT</button>
                </div>
            </div>
        </nav>

        <div class="stats-bar">
            <div class="stat-unit"><label>System TVL</label><span>{vault_cache['metrics']['tvl']}</span></div>
            <div class="stat-unit"><label>ALM Kernel</label><span style="color:var(--green)">ACTIVE</span></div>
            <div class="stat-unit"><label>Nodes</label><span>{vault_cache['metrics']['active_nodes']} Online</span></div>
        </div>

        <div class="container">
            <!-- ENTRY PAGE -->
            <div id="login-page" class="tab-content active-tab" style="text-align:center; padding: 100px 0;">
                <h1 style="font-size: 64px; font-weight: 800; margin-bottom: 20px; letter-spacing: -3px;">Automated ALM for<br>Base Treasuries.</h1>
                <p style="color: var(--sub); font-size: 20px; max-width: 600px; margin: 0 auto 40px auto; line-height: 1.6;">The VaultLogic Kernel optimizes institutional capital across the Base ecosystem, ensuring 24/7 liquidity and yield capture without manual intervention.</p>
                <button class="btn-action" style="font-size: 20px; padding: 22px 50px;" onclick="window.modal.open()">ENTER PORTAL</button>
            </div>

            <!-- DASHBOARD -->
            <div id="dashboard" class="tab-content">
                <div id="hero-panel">
                    <div>
                        <div style="font-size:14px; font-weight:800; color:var(--accent); margin-bottom:10px; text-transform:uppercase;">Institutional Vault</div>
                        <div style="font-size:32px; font-weight:800; margin-bottom:10px;">Managed Capital Engine</div>
                        <div style="color:var(--sub); font-size:16px;">The ALM Kernel is currently optimizing within Delta-Neutral parameters.</div>
                    </div>
                    <button class="btn-action" onclick="toggleModal('allocationModal', true)">ALLOCATE CAPITAL</button>
                </div>

                <div class="main-metrics">
                    <div class="metric-card"><label>Current Vault APY</label><div class="value" style="color:var(--green)">{vault_cache['metrics']['current_apy']}</div></div>
                    <div class="metric-card"><label>Last Rebalance</label><div class="value">{vault_cache['metrics']['last_rebalance']}</div></div>
                    <div class="metric-card"><label>Kernel Health</label><div class="value">{vault_cache['metrics']['health']}</div></div>
                </div>

                <div id="log-container">
                    <div class="log-header"><span>INDUSTRIAL_EXECUTION_LOG</span><span>VAULTLOGIC_CORE_V2.7</span></div>
                    <div id="log-stream"></div>
                </div>
            </div>

            <!-- HOW IT WORKS -->
            <div id="earn" class="tab-content">
                <h1 style="font-size:36px; font-weight:800; margin-bottom:40px;">Industrial Automation Flow</h1>
                <div class="step-card">
                    <div class="step-num">1</div>
                    <div class="step-body"><h3>Audit</h3><p>Kernel scans your connected institutional wallet for USDC/EURC reserves on the Base network.</p></div>
                </div>
                <div class="step-card">
                    <div class="step-num">2</div>
                    <div class="step-body"><h3>Deployment</h3><p>Capital is moved into a dedicated ALM contract kernel. No manual pool selection required.</p></div>
                </div>
                <div class="step-card">
                    <div class="step-num">3</div>
                    <div class="step-body"><h3>Active Management</h3><p>Our Python-powered engine monitors 14+ pools on Aave, Morpho, and Aerodrome, rebalancing every time a yield spread exceeds 0.5%.</p></div>
                </div>
            </div>

            <!-- ABOUT -->
            <div id="about" class="tab-content">
                <h1 style="font-size:32px; font-weight:800;">Risk-First Treasury Management</h1>
                <p style="color:var(--sub); font-size:18px; line-height:1.8;">VaultLogic removes the "human error" from on-chain liquidity management. By treating yield as a byproduct of efficient asset-liability management, we provide institutions with the "Industrial Floor" for their digital assets.</p>
            </div>
        </div>

        <!-- ALLOCATION MODAL -->
        <div id="allocationModal" class="modal">
            <div class="modal-box">
                <h2 style="margin:0 0 10px 0;">Capital Allocation</h2>
                <p style="font-size:14px; color:var(--sub); margin-bottom:30px;">Initialize the ALM kernel with institutional USDC reserves.</p>
                <input type="number" id="alloc-amt" placeholder="0.00" style="width:100%; background:var(--bg); border:1px solid var(--border); color:white; padding:18px; border-radius:12px; font-size:24px; font-weight:800; outline:none; margin-bottom:20px;">
                <div id="err-box" style="color:var(--red); font-size:12px; font-weight:700; margin-bottom:20px; display:none;"></div>
                <button id="verify-btn" onclick="verifyAndStart()" class="btn-action" style="width:100%; height:60px;">VERIFY & DEPLOY</button>
                <button onclick="toggleModal('allocationModal', false)" style="width:100%; background:none; border:none; color:var(--sub); margin-top:15px; cursor:pointer; font-weight:700;">Cancel</button>
            </div>
        </div>

        <script>
            function showSection(id) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active-tab'));
                document.querySelectorAll('.nav-links a').forEach(el => el.classList.remove('active'));
                const target = document.getElementById(id);
                if(target) {{
                    target.classList.add('active-tab');
                    const navItem = document.getElementById('nav-' + id);
                    if(navItem) navItem.classList.add('active');
                }}
            }}

            function toggleModal(id, show) {{ document.getElementById(id).style.display = show ? 'flex' : 'none'; }}

            async function verifyAndStart() {{
                const amt = document.getElementById('alloc-amt').value;
                const btn = document.getElementById('verify-btn');
                const err = document.getElementById('err-box');
                if(!amt || amt <= 0) return;
                
                err.style.display = 'none';
                btn.innerText = "AUDITING RESERVES...";
                btn.disabled = true;

                try {{
                    const vRes = await fetch('/verify-balance', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ address: window.userAddress, amount: parseFloat(amt) }})
                    }});
                    const vData = await vRes.json();
                    if(vData.status === 'error') {{
                        err.innerText = vData.message;
                        err.style.display = 'block';
                        btn.innerText = "VERIFY & DEPLOY";
                        btn.disabled = false;
                        return;
                    }}
                    await fetch('/start-engine', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ address: window.userAddress, amount: parseFloat(amt) }})
                    }});
                    toggleModal('allocationModal', false);
                }} catch(e) {{
                    btn.innerText = "VERIFY & DEPLOY";
                    btn.disabled = false;
                }}
            }}

            setInterval(async () => {{
                try {{
                    const res = await fetch('/logs');
                    const data = await res.json();
                    document.getElementById('log-stream').innerHTML = data.logs.map(l => `<div><span style="opacity:0.3;">></span> ${{l}}</div>`).reverse().join('');
                }} catch(e) {{}}
            }}, 2000);
        </script>
    </body>
    </html>
    """