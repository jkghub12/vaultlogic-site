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

system_logs = ["VaultLogic Kernel v2.6.5 Online", "Auth Mode: Institutional Gate Enabled."]

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

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

@app.get("/logs")
async def get_logs():
    return {"logs": system_logs}

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
        <title>VaultLogic | Institutional ALM</title>
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
                const landing = document.getElementById('landing-gate');
                const dashboard = document.getElementById('main-dashboard');
                const stats = document.getElementById('stats-ribbon');
                const userZone = document.getElementById('user-zone');
                const connectBtn = document.getElementById('connect-trigger');
                
                if(state.isConnected) {{
                    window.userAddress = state.address;
                    landing.style.display = 'none';
                    dashboard.style.display = 'block';
                    stats.style.display = 'flex';
                    userZone.style.display = 'flex';
                    connectBtn.style.display = 'none';
                    document.getElementById('addr-display').innerText = state.address.slice(0,6) + '...' + state.address.slice(-4);
                }} else {{
                    landing.style.display = 'flex';
                    dashboard.style.display = 'none';
                    stats.style.display = 'none';
                    userZone.style.display = 'none';
                    connectBtn.style.display = 'block';
                }}
            }});
        </script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
            :root {{ --bg: #0f172a; --panel: #1e293b; --text: #f8fafc; --sub: #94a3b8; --accent: #3b82f6; --green: #22c55e; --red: #ef4444; --border: #334155; }}
            
            body {{ margin:0; background: var(--bg); color: var(--text); font-family: 'Public Sans', sans-serif; height: 100vh; overflow-x: hidden; }}
            
            nav {{ background: rgba(15,23,42,0.8); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); height: 70px; display: flex; align-items: center; justify-content: space-between; padding: 0 40px; position: sticky; top: 0; z-index: 1000; }}
            .logo {{ display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 20px; text-decoration: none; color: var(--text); }}
            .logo img {{ height: 32px; filter: brightness(0) invert(1); }}
            
            .nav-links {{ display: flex; gap: 25px; align-items: center; }}
            .nav-links a {{ color: var(--sub); text-decoration: none; font-size: 12px; font-weight: 700; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }}
            .nav-links a:hover {{ color: var(--text); }}

            .stats-bar {{ background: #1e293b; border-bottom: 1px solid var(--border); display: none; gap: 50px; padding: 15px 40px; overflow-x: auto; }}
            .stat-unit label {{ display: block; font-size: 10px; font-weight: 800; color: var(--sub); text-transform: uppercase; margin-bottom: 2px; }}
            .stat-unit span {{ font-size: 16px; font-weight: 800; color: var(--text); }}

            /* Landing Gate Style */
            #landing-gate {{ height: calc(100vh - 70px); display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 20px; background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%); }}
            .gate-card {{ max-width: 500px; }}
            .gate-title {{ font-size: 48px; font-weight: 800; letter-spacing: -1.5px; margin-bottom: 15px; }}
            .gate-sub {{ color: var(--sub); font-size: 18px; margin-bottom: 40px; line-height: 1.5; }}
            .btn-large {{ background: white; color: black; border: none; padding: 18px 40px; border-radius: 12px; font-weight: 800; font-size: 16px; cursor: pointer; transition: 0.2s; }}
            .btn-large:hover {{ transform: scale(1.02); box-shadow: 0 0 30px rgba(255,255,255,0.1); }}

            .container {{ max-width: 1200px; margin: 0 auto; padding: 40px; }}
            
            #main-dashboard {{ display: none; }}
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
            
            .btn-select {{ width:100%; background: transparent; border: 1px solid var(--border); color: var(--text); padding: 12px; border-radius: 10px; font-weight: 700; cursor: pointer; }}
            .btn-select:hover {{ background: white; color: black; }}

            #log-container {{ background: #020617; border-radius: 16px; margin-top: 50px; border: 1px solid var(--border); }}
            .log-header {{ padding: 15px 25px; background: #0f172a; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 11px; font-weight: 800; color: var(--sub); }}
            #log-stream {{ height: 250px; overflow-y: auto; padding: 25px; font-family: 'JetBrains Mono'; font-size: 12px; color: #10b981; line-height: 1.8; }}

            .modal {{ display:none; position:fixed; inset:0; background:rgba(2,6,23,0.9); z-index:2000; justify-content:center; align-items:center; backdrop-filter: blur(10px); }}
            .modal-box {{ background:var(--panel); padding:40px; border-radius:24px; width:100%; max-width:420px; border: 1px solid var(--border); }}
            
            .tab-content {{ display: none; }}
            .active-tab {{ display: block; }}
            
            .btn-action {{ background: var(--green); color: white; border: none; padding: 14px 28px; border-radius: 10px; font-weight: 800; cursor: pointer; }}
        </style>
    </head>
    <body>
        <nav>
            <a href="/" class="logo">
                <img src="{logo_url}" alt="VL" onerror="this.style.display='none'">
                <span>VAULTLOGIC</span>
            </a>
            <div class="nav-links">
                <a onclick="showSection('dashboard')">DASHBOARD</a>
                <a onclick="showSection('strategies')">STRATEGIES</a>
                <a onclick="showSection('performance')">PERFORMANCE</a>
                <a onclick="showSection('about')">ABOUT</a>
            </div>
            <div id="auth-zone">
                <button id="connect-trigger" onclick="window.modal.open()" style="background:white; color:black; border:none; padding:10px 20px; border-radius:8px; font-weight:800; cursor:pointer;">CONNECT</button>
                <div id="user-zone" style="display:none; align-items:center; gap:15px;">
                    <span id="addr-display" style="font-family:'JetBrains Mono'; font-size:12px; font-weight:800; background:rgba(255,255,255,0.05); padding:6px 12px; border-radius:6px;"></span>
                    <button onclick="window.modal.disconnect()" style="color:var(--red); background:none; border:none; font-size:10px; font-weight:800; cursor:pointer;">DISCONNECT</button>
                </div>
            </div>
        </nav>

        <div id="stats-ribbon" class="stats-bar">
            <div class="stat-unit"><label>System TVL</label><span>{vault_cache['metrics']['tvl']}</span></div>
            <div class="stat-unit"><label>Kernel Health</label><span style="color:var(--green)">{vault_cache['metrics']['health']}</span></div>
            <div class="stat-unit"><label>Nodes</label><span>{vault_cache['metrics']['active_nodes']} Online</span></div>
        </div>

        <!-- Landing State -->
        <div id="landing-gate">
            <div class="gate-card">
                <div class="gate-title">Institutional Yield<br>Autopilot</div>
                <p class="gate-sub">Advanced Asset-Liability Management for the Base Ecosystem. Connect your institutional wallet to initialize the kernel.</p>
                <button class="btn-large" onclick="window.modal.open()">ENTER KERNEL</button>
            </div>
        </div>

        <!-- Authenticated State -->
        <div id="main-dashboard" class="container">
            <div id="dashboard" class="tab-content active-tab">
                <div id="hero-panel">
                    <div>
                        <div style="font-size:24px; font-weight:800; margin-bottom:5px;">Kernel Authenticated</div>
                        <div style="color:var(--sub); font-size:14px;">Select an allocation strategy to begin automated execution.</div>
                    </div>
                    <button class="btn-action" onclick="openAllocation('default')">ACTIVATE ENGINE</button>
                </div>
                <div class="grid">{cards_html}</div>
            </div>

            <div id="strategies" class="tab-content">
                <h1 style="font-size:32px; font-weight:800;">Risk Framework</h1>
                <p style="color:var(--sub); max-width:600px;">VaultLogic uses a Multi-Pool Delta strategy to manage volatility risk.</p>
                <div class="grid">{cards_html}</div>
            </div>

            <div id="performance" class="tab-content">
                <h1 style="font-size:32px; font-weight:800;">Performance</h1>
                <div style="background:var(--panel); border:1px solid var(--border); padding:60px; border-radius:20px; text-align:center; color:var(--sub);">
                    Historical yield curves are being indexed for the current epoch.
                </div>
            </div>

            <div id="about" class="tab-content">
                <h1 style="font-size:32px; font-weight:800;">About VaultLogic</h1>
                <div style="line-height:1.7; color:var(--sub); max-width:800px; font-size:15px;">
                    VaultLogic is built for institutions. Unlike retail yield aggregators, our engine focuses on **Asset-Liability Management (ALM)**. We don't just find yield; we manage the liquidity risks associated with large capital movements on-chain.
                    <br><br>
                    Our kernel runs natively on Base, ensuring low-latency execution and high-security oversight.
                </div>
            </div>

            <div id="log-container">
                <div class="log-header"><span>INDUSTRIAL LOG_STREAM</span><span>VAULTLOGIC_V2.6.5</span></div>
                <div id="log-stream"></div>
            </div>
        </div>

        <div id="allocationModal" class="modal">
            <div class="modal-box">
                <h2 style="margin:0 0 10px 0;">Capital Allocation</h2>
                <p style="font-size:14px; color:var(--sub); margin-bottom:30px;">Input USDC amount. The kernel will audit your balance before deployment.</p>
                <input type="number" id="alloc-amt" placeholder="0.00" style="width:100%; background:var(--bg); border:1px solid var(--border); color:white; padding:18px; border-radius:12px; font-size:24px; font-weight:800; outline:none; margin-bottom:20px;">
                <div id="err-box" style="color:var(--red); font-size:12px; font-weight:700; margin-bottom:20px; display:none;"></div>
                <button id="verify-btn" onclick="verifyAndStart()" class="btn-action" style="width:100%; height:60px;">VERIFY & DEPLOY</button>
                <button onclick="toggleModal('allocationModal', false)" style="width:100%; background:none; border:none; color:var(--sub); margin-top:15px; cursor:pointer; font-weight:700;">Cancel</button>
            </div>
        </div>

        <script>
            function showSection(id) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active-tab'));
                document.getElementById(id).classList.add('active-tab');
                window.scrollTo(0,0);
            }}

            function toggleModal(id, show) {{ document.getElementById(id).style.display = show ? 'flex' : 'none'; }}
            function openAllocation(stratId) {{ toggleModal('allocationModal', true); }}

            async function verifyAndStart() {{
                const amt = document.getElementById('alloc-amt').value;
                const btn = document.getElementById('verify-btn');
                const err = document.getElementById('err-box');
                if(!amt || amt <= 0) return;
                
                err.style.display = 'none';
                btn.innerText = "AUDITING ON-CHAIN...";
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