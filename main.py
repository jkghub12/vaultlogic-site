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
        {"protocol": "MORPHO BLUE", "apy": 3.62, "predicted": 3.85, "asset": "USDC", "risk": "LOW", "util": "82%"},
        {"protocol": "AAVE V3", "apy": 4.12, "predicted": 4.25, "asset": "EURC", "risk": "MINIMAL", "util": "74%"},
        {"protocol": "AERODROME", "apy": 12.41, "predicted": 11.15, "asset": "PYUSD/USDC", "risk": "MED", "util": "91%"},
        {"protocol": "UNISWAP V3", "apy": 3.55, "predicted": 4.10, "asset": "USDC/EURC", "risk": "LOW", "util": "65%"}
    ]
}

system_logs = ["VaultLogic Kernel v2.5.9 Online", "Network: Base Mainnet Verified.", "Status: Awaiting Capital Allocation."]

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

# --- API ENDPOINTS ---

@app.post("/verify-balance")
async def verify_balance(data: EngineInit):
    try:
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        raw_balance = contract.functions.balanceOf(Web3.to_checksum_address(data.address)).call()
        actual_balance = raw_balance / 10**6
        
        if data.amount > actual_balance:
            return {"status": "error", "message": f"Audit Failed: Wallet holds {actual_balance:,.2f} USDC. Requested {data.amount:,.2f}."}
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
    
    # Generate Strategy Cards
    cards_html = "".join([f"""
        <div class="card">
            <div class="card-top">
                <div>
                    <div class="protocol">{s['protocol']}</div>
                    <div class="asset">{s['asset']}</div>
                </div>
                <div class="badge badge-{s['risk'].lower()}">{s['risk']} RISK</div>
            </div>
            <div class="yield-grid">
                <div class="y-box"><label>NET APY</label><div class="val">{s['apy']}%</div></div>
                <div class="y-box active"><label>FORECAST</label><div class="val">{s['predicted']}%</div></div>
            </div>
            <div class="progress-wrap">
                <div class="progress-bar" style="width:{s['util']}"></div>
                <span>Utilization: {s['util']}</span>
            </div>
            <button class="btn-select" onclick="toggleModal('allocationModal', true)">SELECT STRATEGY</button>
        </div>
    """ for s in vault_cache['strategies']])

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VaultLogic | Institutional Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script type="module">
            import {{ createAppKit }} from 'https://esm.sh/@reown/appkit'
            import {{ Ethers5Adapter }} from 'https://esm.sh/@reown/appkit-adapter-ethers5'
            import {{ base }} from 'https://esm.sh/@reown/appkit/networks'

            const modal = createAppKit({{
                adapters: [new Ethers5Adapter()],
                networks: [base],
                projectId: '2b936cf692d84ae6da1ba91950c96420',
                themeMode: 'light'
            }});
            window.modal = modal;
            modal.subscribeAccount(state => {{
                if(state.isConnected) {{ window.userAddress = state.address; setupUI(state.address); }}
                else {{ window.location.reload(); }}
            }});
        </script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
            :root {{ --bg: #f8fafc; --panel: #ffffff; --text: #0f172a; --sub: #64748b; --border: #e2e8f0; --accent: #2563eb; --green: #22c55e; --red: #ef4444; }}
            
            body {{ margin:0; background: var(--bg); color: var(--text); font-family: 'Public Sans', sans-serif; -webkit-font-smoothing: antialiased; }}
            
            nav {{ background: white; border-bottom: 1px solid var(--border); height: 70px; display: flex; align-items: center; justify-content: space-between; padding: 0 40px; position: sticky; top: 0; z-index: 1000; }}
            .logo {{ display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 20px; text-decoration: none; color: var(--text); letter-spacing: -0.5px; }}
            .logo img {{ height: 32px; width: auto; }}
            
            .stats-bar {{ background: white; border-bottom: 1px solid var(--border); display: flex; gap: 40px; padding: 15px 40px; overflow-x: auto; }}
            .stat-unit label {{ display: block; font-size: 10px; font-weight: 800; color: var(--sub); text-transform: uppercase; margin-bottom: 2px; }}
            .stat-unit span {{ font-size: 16px; font-weight: 800; }}

            .main-content {{ max-width: 1200px; margin: 0 auto; padding: 20px 40px; }}
            
            #hero-panel {{ background: white; border: 1px solid var(--border); border-radius: 16px; padding: 30px; display: none; justify-content: space-between; align-items: center; margin-bottom: 30px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .status-tag {{ display: flex; align-items: center; gap: 10px; }}
            .dot {{ width: 10px; height: 10px; border-radius: 50%; background: #cbd5e1; }}
            .dot.active {{ background: var(--green); box-shadow: 0 0 12px var(--green); animation: pulse 2s infinite; }}
            
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .card {{ background: white; border: 1px solid var(--border); border-radius: 16px; padding: 24px; transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-4px); border-color: var(--accent); }}
            .protocol {{ font-size: 11px; font-weight: 800; color: var(--sub); }}
            .asset {{ font-size: 20px; font-weight: 800; margin-bottom: 15px; }}
            
            .yield-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .y-box {{ background: #f1f5f9; padding: 12px; border-radius: 8px; }}
            .y-box.active {{ background: #eff6ff; border: 1px solid #bfdbfe; }}
            .y-box label {{ font-size: 9px; font-weight: 800; color: var(--sub); display: block; }}
            .y-box .val {{ font-size: 18px; font-weight: 800; }}
            
            .btn-start {{ background: var(--green); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 800; cursor: pointer; }}
            .btn-select {{ width:100%; border: 1px solid var(--border); background: white; padding: 12px; border-radius: 8px; font-weight: 700; cursor: pointer; }}

            #log-container {{ background: #0f172a; border-radius: 12px; overflow: hidden; margin-top: 20px; }}
            .log-header {{ padding: 12px 20px; background: #1e293b; color: #94a3b8; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; }}
            #log-stream {{ height: 200px; overflow-y: auto; padding: 20px; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #34d399; line-height: 1.6; }}

            .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.8); z-index:2000; justify-content:center; align-items:center; backdrop-filter: blur(8px); }}
            .modal-box {{ background:white; padding:40px; border-radius:24px; width:100%; max-width:400px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); }}
            
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
        </style>
    </head>
    <body>
        <nav>
            <a href="/" class="logo">
                <img src="{logo_url}" alt="VL" onerror="this.src='https://raw.githubusercontent.com/VaultLogic/vaultlogic-site/main/VLlogo.png'">
                <span>VAULTLOGIC</span>
            </a>
            <div id="auth-zone">
                <button onclick="window.modal.open()" style="background:var(--text); color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:700; cursor:pointer;">CONNECT WALLET</button>
            </div>
            <div id="user-zone" style="display:none; text-align:right;">
                <div id="addr" style="font-family:'JetBrains Mono'; font-weight:800; font-size:12px;"></div>
                <div onclick="window.modal.disconnect()" style="color:var(--red); font-size:10px; font-weight:800; cursor:pointer;">DISCONNECT</div>
            </div>
        </nav>

        <div class="stats-bar">
            <div class="stat-unit"><label>System TVL</label><span>{vault_cache['metrics']['tvl']}</span></div>
            <div class="stat-unit"><label>Protocol Health</label><span style="color:var(--green)">{vault_cache['metrics']['health']}</span></div>
            <div class="stat-unit"><label>Reserve Ratio</label><span>{vault_cache['metrics']['reserve']}</span></div>
            <div class="stat-unit"><label>Active Nodes</label><span>{vault_cache['metrics']['active_nodes']}</span></div>
        </div>

        <div class="main-content">
            <div id="hero-panel">
                <div class="status-tag">
                    <div id="status-dot" class="dot"></div>
                    <div>
                        <div style="font-weight:800; font-size:14px;">ALM KERNEL: <span id="status-text">STANDBY</span></div>
                        <div style="font-size:11px; color:var(--sub)">Verified connection to Base mainnet.</div>
                    </div>
                </div>
                <button id="main-init-btn" class="btn-start" onclick="toggleModal('allocationModal', true)">INITIATE ENGINE</button>
            </div>

            <div class="grid">{cards_html}</div>

            <div id="log-container">
                <div class="log-header"><span>INDUSTRIAL EXECUTION LOG</span><span id="uptime">00:00:00</span></div>
                <div id="log-stream"></div>
            </div>
        </div>

        <div id="allocationModal" class="modal">
            <div class="modal-box">
                <h2 style="margin:0 0 10px 0;">Capital Allocation</h2>
                <p style="font-size:13px; color:var(--sub); margin-bottom:25px;">The ALM engine will perform a read-audit of your USDC balance before deployment.</p>
                <label style="font-size:11px; font-weight:800; color:var(--sub); text-transform:uppercase;">Amount (USDC)</label>
                <input type="number" id="alloc-amt" placeholder="0.00" style="width:100%; padding:15px; font-size:24px; font-weight:800; border:2px solid var(--border); border-radius:12px; margin-top:8px; outline:none; box-sizing:border-box;">
                <div id="error-msg" style="color:var(--red); font-size:12px; font-weight:700; margin-top:10px; display:none;"></div>
                <button id="deploy-btn" onclick="runVerification()" class="btn-start" style="width:100%; margin-top:25px; height:55px;">VERIFY & DEPLOY</button>
                <button onclick="toggleModal('allocationModal', false)" style="width:100%; background:none; border:none; color:var(--sub); font-size:12px; margin-top:15px; cursor:pointer;">Cancel</button>
            </div>
        </div>

        <script>
            function toggleModal(id, show) {{ document.getElementById(id).style.display = show ? 'flex' : 'none'; }}

            function setupUI(addr) {{
                document.getElementById('auth-zone').style.display = 'none';
                document.getElementById('user-zone').style.display = 'block';
                document.getElementById('hero-panel').style.display = 'flex';
                document.getElementById('addr').innerText = addr.slice(0,6) + '...' + addr.slice(-4);
            }}

            async function runVerification() {{
                const amt = document.getElementById('alloc-amt').value;
                const err = document.getElementById('error-msg');
                const btn = document.getElementById('deploy-btn');
                
                if(!amt || amt <= 0) return;
                
                err.style.display = 'none';
                btn.innerText = "AUDITING ON-CHAIN...";
                btn.disabled = true;

                const res = await fetch('/verify-balance', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ address: window.userAddress, amount: parseFloat(amt) }})
                }});
                const data = await res.json();

                if(data.status === 'error') {{
                    err.innerText = data.message;
                    err.style.display = 'block';
                    btn.innerText = "VERIFY & DEPLOY";
                    btn.disabled = false;
                }} else {{
                    await fetch('/start-engine', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ address: window.userAddress, amount: parseFloat(amt) }})
                    }});
                    toggleModal('allocationModal', false);
                    document.getElementById('status-dot').classList.add('active');
                    document.getElementById('status-text').innerText = "RUNNING";
                    document.getElementById('status-text').style.color = "var(--green)";
                    document.getElementById('main-init-btn').style.display = 'none';
                }}
            }}

            setInterval(async () => {{
                try {{
                    const res = await fetch('/logs');
                    const data = await res.json();
                    document.getElementById('log-stream').innerHTML = data.logs.map(l => `<div><span style="color:#475569;">></span> ${{l}}</div>`).reverse().join('');
                }} catch(e) {{}}
            }}, 2000);
        </script>
    </body>
    </html>
    """