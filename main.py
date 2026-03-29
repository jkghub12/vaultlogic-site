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
vault_cache = {
    "metrics": {
        "tvl": "$142.8M",
        "health": "99.8%",
        "reserve": "104.2%",
        "active_nodes": 12
    },
    "strategies": [
        {"id": "morpho", "protocol": "MORPHO BLUE", "apy": 3.62, "predicted": 3.85, "asset": "USDC", "risk": "LOW", "util": "82%"},
        {"id": "aave", "protocol": "AAVE V3", "apy": 4.12, "predicted": 4.25, "asset": "EURC", "risk": "MINIMAL", "util": "74%"},
        {"id": "aero", "protocol": "AERODROME", "apy": 12.41, "predicted": 11.15, "asset": "PYUSD/USDC", "risk": "MED", "util": "91%"},
        {"id": "uni", "protocol": "UNISWAP V3", "apy": 3.55, "predicted": 4.10, "asset": "USDC/EURC", "risk": "LOW", "util": "65%"}
    ]
}

system_logs = ["VaultLogic Kernel v2.6.8 Online", "Institutional Pitch Mode: Active."]

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
    from engine import run_alm_engine
    add_log(f"INIT: Spawning ALM Kernel for {data.address[:10]}... with ${data.amount:,.2f}")
    asyncio.create_task(run_alm_engine(data.address, log_callback=add_log))
    return {"status": "running"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logo_url = "https://raw.githubusercontent.com/VaultLogic/vaultlogic-site/main/VLlogo.png"
    
    cards_html = "".join([f"""
        <div class="card">
            <div class="card-top">
                <div>
                    <div class="protocol">{s['protocol']}</div>
                    <div class="asset">{s['asset']}</div>
                </div>
                <div class="badge">{s['risk']} RISK</div>
            </div>
            <div class="yield-grid">
                <div class="y-box"><label>NET APY</label><div class="val">{s['apy']}%</div></div>
                <div class="y-box active"><label>FORECAST</label><div class="val">{s['predicted']}%</div></div>
            </div>
            <button class="btn-select" onclick="openAllocation('{s['id']}')">SELECT STRATEGY</button>
        </div>
    """ for s in vault_cache['strategies']])

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>VaultLogic | Coinbase Institutional ALM</title>
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
                const dashboard = document.getElementById('dashboard');
                
                if(state.isConnected) {{
                    window.userAddress = state.address;
                    userZone.style.display = 'flex';
                    connectNav.style.display = 'none';
                    document.getElementById('addr-display').innerText = state.address.slice(0,6) + '...' + state.address.slice(-4);
                    // If they connect while on the login page, move them to dashboard
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
            
            body {{ margin:0; background: var(--bg); color: var(--text); font-family: 'Public Sans', sans-serif; height: 100vh; }}
            
            nav {{ background: rgba(15,23,42,0.9); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); height: 70px; display: flex; align-items: center; justify-content: space-between; padding: 0 40px; position: sticky; top: 0; z-index: 1000; }}
            .logo {{ display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 20px; text-decoration: none; color: var(--text); }}
            .logo img {{ height: 32px; filter: brightness(0) invert(1); }}
            
            .nav-links {{ display: flex; gap: 25px; align-items: center; }}
            .nav-links a {{ color: var(--sub); text-decoration: none; font-size: 12px; font-weight: 700; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }}
            .nav-links a:hover, .nav-links a.active {{ color: var(--text); }}

            .stats-bar {{ background: #1e293b; border-bottom: 1px solid var(--border); display: flex; gap: 50px; padding: 15px 40px; overflow-x: auto; }}
            .stat-unit label {{ display: block; font-size: 10px; font-weight: 800; color: var(--sub); text-transform: uppercase; }}
            .stat-unit span {{ font-size: 16px; font-weight: 800; color: var(--text); }}

            .container {{ max-width: 1200px; margin: 0 auto; padding: 40px; }}
            
            /* TAB SYSTEM */
            .tab-content {{ display: none; }}
            .tab-content.active-tab {{ display: block; }}

            /* LOGIN PAGE (Coinbase Pitch) */
            #login-page {{ height: 70vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }}
            .pitch-badge {{ background: rgba(59,130,246,0.1); color: var(--accent); padding: 8px 16px; border-radius: 50px; font-size: 12px; font-weight: 800; margin-bottom: 20px; border: 1px solid rgba(59,130,246,0.3); }}
            .pitch-title {{ font-size: 56px; font-weight: 800; letter-spacing: -2px; margin-bottom: 20px; }}
            .pitch-sub {{ color: var(--sub); font-size: 18px; max-width: 600px; margin-bottom: 40px; line-height: 1.6; }}

            /* DASHBOARD COMPONENTS */
            #hero-panel {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid var(--border); border-radius: 20px; padding: 40px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }}
            .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 24px; transition: 0.3s; }}
            .card:hover {{ border-color: var(--accent); transform: translateY(-5px); }}
            .protocol {{ font-size: 11px; font-weight: 800; color: var(--sub); }}
            .asset {{ font-size: 22px; font-weight: 800; margin: 5px 0 20px 0; }}
            
            .yield-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 25px; }}
            .y-box {{ background: rgba(15,23,42,0.5); padding: 15px; border-radius: 12px; border: 1px solid transparent; }}
            .y-box.active {{ border-color: var(--accent); background: rgba(59,130,246,0.1); }}
            .y-box label {{ font-size: 9px; font-weight: 800; color: var(--sub); display: block; }}
            .y-box .val {{ font-size: 18px; font-weight: 800; }}
            
            .btn-action {{ background: var(--green); color: white; border: none; padding: 14px 28px; border-radius: 10px; font-weight: 800; cursor: pointer; font-size: 14px; }}
            .btn-select {{ width:100%; background: transparent; border: 1px solid var(--border); color: var(--text); padding: 12px; border-radius: 10px; font-weight: 700; cursor: pointer; }}
            .btn-select:hover {{ background: white; color: black; }}

            #log-container {{ background: #020617; border-radius: 16px; margin-top: 50px; border: 1px solid var(--border); }}
            .log-header {{ padding: 15px 25px; background: #0f172a; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 11px; font-weight: 800; color: var(--sub); }}
            #log-stream {{ height: 250px; overflow-y: auto; padding: 25px; font-family: 'JetBrains Mono'; font-size: 12px; color: #10b981; line-height: 1.8; }}

            .modal {{ display:none; position:fixed; inset:0; background:rgba(2,6,23,0.9); z-index:2000; justify-content:center; align-items:center; backdrop-filter: blur(10px); }}
            .modal-box {{ background:var(--panel); padding:40px; border-radius:24px; width:100%; max-width:420px; border: 1px solid var(--border); }}
        </style>
    </head>
    <body>
        <nav>
            <a onclick="showSection('login-page')" class="logo" style="cursor:pointer">
                <img src="{logo_url}" alt="VL" onerror="this.style.display='none'">
                <span>VAULTLOGIC</span>
            </a>
            <div class="nav-links">
                <a onclick="showSection('dashboard')" id="nav-dashboard">DASHBOARD</a>
                <a onclick="showSection('strategies')" id="nav-strategies">STRATEGIES</a>
                <a onclick="showSection('performance')" id="nav-performance">PERFORMANCE</a>
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
            <div class="stat-unit"><label>Kernel Health</label><span style="color:var(--green)">{vault_cache['metrics']['health']}</span></div>
            <div class="stat-unit"><label>Nodes</label><span>{vault_cache['metrics']['active_nodes']} Online</span></div>
        </div>

        <div class="container">
            <!-- Institutional Login Page (Home) -->
            <div id="login-page" class="tab-content active-tab">
                <div class="pitch-badge">COINBASE ASSET MANAGEMENT PARTNER PORTAL</div>
                <h1 class="pitch-title">The Industrial Floor<br>for On-Chain Yield</h1>
                <p class="pitch-sub">Automated Asset-Liability Management (ALM) kernel for institutional treasuries. High-performance liquidity provision on Base mainnet.</p>
                <button class="btn-action" style="padding: 20px 50px; font-size:18px;" onclick="window.modal.open()">INITIALIZE KERNEL</button>
            </div>

            <!-- Dashboard -->
            <div id="dashboard" class="tab-content">
                <div id="hero-panel">
                    <div>
                        <div style="font-size:24px; font-weight:800; margin-bottom:5px;">Institutional Dashboard</div>
                        <div style="color:var(--sub); font-size:14px;">Real-time management of active yield strategies.</div>
                    </div>
                    <button class="btn-action" onclick="openAllocation('global')">DEPLOY CAPITAL</button>
                </div>
                <div class="grid">{cards_html}</div>
            </div>

            <!-- Strategies -->
            <div id="strategies" class="tab-content">
                <h1 style="font-size:32px; font-weight:800;">Risk Frameworks</h1>
                <p style="color:var(--sub); max-width:600px; margin-bottom:40px;">VaultLogic utilizes a proprietary Multi-Pool Delta strategy to manage volatility and liquidity gaps across the Base ecosystem.</p>
                <div class="grid">{cards_html}</div>
            </div>

            <!-- Performance -->
            <div id="performance" class="tab-content">
                <h1 style="font-size:32px; font-weight:800;">Historical Performance</h1>
                <div style="background:var(--panel); border:1px solid var(--border); padding:80px; border-radius:24px; text-align:center; color:var(--sub);">
                    <div style="font-size:40px; margin-bottom:10px;">📊</div>
                    Performance metrics are being indexed for the current epoch.<br>Institutional historical logs are available via CSV export once connected.
                </div>
            </div>

            <!-- About -->
            <div id="about" class="tab-content">
                <h1 style="font-size:32px; font-weight:800;">About VaultLogic</h1>
                <div style="line-height:1.8; color:var(--sub); max-width:800px; font-size:16px;">
                    VaultLogic is built specifically for institutional capital. Unlike retail aggregators, our engine focuses on **Asset-Liability Management (ALM)**. 
                    <br><br>
                    We manage the liquidity risks associated with large-scale on-chain positions, ensuring that capital stays "in-range" and productive 24/7 without manual intervention. Our kernel is optimized for the Base L2, providing the security of Ethereum with institutional speed.
                </div>
            </div>

            <div id="log-container">
                <div class="log-header"><span>INDUSTRIAL LOG_STREAM</span><span id="sys-time">KERNEL_ACTIVE</span></div>
                <div id="log-stream"></div>
            </div>
        </div>

        <!-- Allocation Modal -->
        <div id="allocationModal" class="modal">
            <div class="modal-box">
                <h2 style="margin:0 0 10px 0;">Capital Allocation</h2>
                <p style="font-size:14px; color:var(--sub); margin-bottom:30px;">Input USDC amount. The kernel will perform an on-chain audit of your address before deployment.</p>
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
                
                document.getElementById(id).classList.add('active-tab');
                const navItem = document.getElementById('nav-' + id);
                if(navItem) navItem.classList.add('active');
                
                window.scrollTo(0,0);
            }}

            function toggleModal(id, show) {{ document.getElementById(id).style.display = show ? 'flex' : 'none'; }}
            function openAllocation(stratId) {{ 
                if(!window.userAddress) {{ window.modal.open(); return; }}
                toggleModal('allocationModal', true); 
            }}

            async function verifyAndStart() {{
                const amt = document.getElementById('alloc-amt').value;
                const btn = document.getElementById('verify-btn');
                const err = document.getElementById('err-box');
                if(!amt || amt <= 0) return;
                
                err.style.display = 'none';
                btn.innerText = "AUDITING BALANCE...";
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