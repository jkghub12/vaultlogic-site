import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

# System state - Upgraded for Institutional Depth
vault_cache = {
    "yields": [], 
    "metrics": {
        "tvl": "$142.8M",
        "health": "99.8%",
        "active_nodes": 12,
        "last_rebalance": "14m ago"
    }
}
system_logs = [
    "VaultLogic Kernel v2.5.7 Online", 
    "Status: AI Predictive Engine Engaged.", 
    "Log: System ready for session initiation."
]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

async def get_industrial_yields():
    # Simulated high-fidelity institutional data
    return [
        {"protocol": "MORPHO BLUE", "apy": 3.62, "predicted": 3.85, "asset": "USDC", "type": "STABLE", "risk": "LOW", "utilization": "82%"},
        {"protocol": "AAVE V3", "apy": 4.12, "predicted": 4.25, "asset": "EURC", "type": "GLOBAL", "risk": "MINIMAL", "utilization": "74%"},
        {"protocol": "AERODROME", "apy": 12.41, "predicted": 11.15, "asset": "PYUSD/USDC", "type": "BOOSTED", "risk": "MED", "utilization": "91%"},
        {"protocol": "UNISWAP V3", "apy": 3.55, "predicted": 4.10, "asset": "USDC/EURC", "type": "FOREX", "risk": "LOW", "utilization": "65%"},
        {"protocol": "BEEFY", "apy": 8.15, "predicted": 8.02, "asset": "EURC/USDC LP", "type": "AUTO-COMPOUND", "risk": "MED", "utilization": "88%"}
    ]

@app.post("/connect-wallet")
async def connect(data: WalletConnect):
    try:
        from engine import run_alm_engine
        # Terminate Logic
        if "TERMINATE" in data.address:
            original_addr = data.address.replace("TERMINATE_", "")
            add_log(f"HALT: Terminating Engine for {original_addr[:10]}...")
            # In engine.py, active_sessions.pop(addr) would stop the while loop
            return {"status": "terminated"}
            
        # Initialization Logic
        add_log(f"AUTH: Wallet {data.address[:10]}... verified.")
        return {"status": "success"}
    except Exception as e:
        add_log(f"ERR: {str(e)}")
        return {"status": "error"}

@app.post("/start-engine")
async def start_engine(data: WalletConnect):
    from engine import run_alm_engine
    add_log(f"INIT: Spawning ALM Kernel for {data.address[:10]}...")
    asyncio.create_task(run_alm_engine(data.address, log_callback=add_log))
    return {"status": "running"}

@app.get("/logs")
async def get_logs():
    return {"logs": system_logs, "metrics": vault_cache["metrics"]}

@app.on_event("startup")
async def startup():
    async def sync():
        while True:
            try:
                vault_cache["yields"] = await get_industrial_yields()
            except: pass
            await asyncio.sleep(60)
    asyncio.create_task(sync())

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    yield_cards = "".join([f"""
        <div class="strategy-card" data-asset="{y['asset']}">
            <div class="card-header">
                <div>
                    <span class="protocol-label">{y['protocol']}</span>
                    <h3 class="asset-title">{y['asset']}</h3>
                </div>
                <div class="risk-badge risk-{y['risk'].lower()}">{y['risk']} RISK</div>
            </div>
            <div class="yield-grid">
                <div class="yield-box">
                    <label>NET APY</label>
                    <div class="value">{y['apy']}%</div>
                </div>
                <div class="yield-box highlighted">
                    <label>AI FORECAST</label>
                    <div class="value">{y['predicted']}%</div>
                </div>
            </div>
            <div class="util-bar">
                <div class="util-fill" style="width: {y['utilization']}"></div>
                <span class="util-text">Utilization: {y['utilization']}</span>
            </div>
            <button onclick="deployFunds(this, '{y['protocol']}')" class="deploy-btn">SELECT STRATEGY</button>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
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
                    featuredWalletIds: [
                        'fd20dc426fb37566d803205b19bbc1d4096b248ac04547e3cfb6b3a38bd033aa',
                        'c57ca71047597b42ddc9d30d30569074b83049102b4d8f5a62e399580577b30c'
                    ],
                    themeMode: 'light',
                    themeVariables: {{ '--w3m-accent': '#0f172a' }}
                }});
                window.modal = modal;
                modal.subscribeAccount(state => {{ 
                    if(state.isConnected) {{
                        window.userAddress = state.address;
                        setupWalletUI(state.address); 
                    }} else {{
                        resetUI();
                    }}
                }});
            </script>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
                :root {{ --primary: #0f172a; --accent: #2563eb; --border: #e2e8f0; --danger: #ef4444; --success: #22c55e; }}
                body {{ background:#f1f5f9; color:var(--primary); font-family: 'Public Sans', sans-serif; margin:0; -webkit-font-smoothing: antialiased; }}
                
                .top-nav {{ 
                    background: rgba(255, 255, 255, 0.95); 
                    backdrop-filter: blur(10px);
                    border-bottom: 1px solid var(--border); 
                    padding: 0 40px; 
                    height: 70px;
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center; 
                    position: sticky; 
                    top: 0; 
                    z-index: 100; 
                }}
                .logo {{ display: flex; align-items: center; gap: 12px; text-decoration: none; font-weight: 800; color: var(--primary); font-size: 19px; }}
                .logo img {{ height: 34px; width: auto; border-radius: 6px; }}
                
                .nav-actions {{ display: flex; gap: 24px; align-items: center; }}
                .nav-link {{ color: #64748b; font-size: 12px; font-weight: 700; text-decoration: none; cursor: pointer; }}
                .btn-connect {{ background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 13px; }}
                
                /* Control Panel */
                #control-panel {{ 
                    max-width: 1200px; 
                    margin: 20px auto 0; 
                    padding: 20px; 
                    background: white; 
                    border: 1px solid var(--border); 
                    border-radius: 12px; 
                    display: none; 
                    align-items: center; 
                    justify-content: space-between;
                    animation: slideDown 0.3s ease-out;
                }}
                @keyframes slideDown {{ from {{ opacity:0; transform: translateY(-10px); }} to {{ opacity:1; transform: translateY(0); }} }}
                
                .status-block {{ display: flex; align-items: center; gap: 15px; }}
                .status-indicator {{ width: 10px; height: 10px; border-radius: 50%; background: #94a3b8; }}
                .status-active {{ background: var(--success); box-shadow: 0 0 10px var(--success); }}
                
                .engine-actions {{ display: flex; gap: 10px; }}
                .btn-start {{ background: var(--success); color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 800; cursor: pointer; font-size: 12px; }}
                .btn-stop {{ background: white; color: var(--danger); border: 1px solid var(--danger); padding: 10px 20px; border-radius: 6px; font-weight: 800; cursor: pointer; font-size: 12px; }}

                /* Rest of UI */
                .stats-ribbon {{ background: white; border-bottom: 1px solid var(--border); padding: 20px 40px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
                .stat-item label {{ font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; }}
                .stat-item .val {{ font-size: 20px; font-weight: 800; }}

                .container {{ max-width: 1200px; margin: 40px auto; padding: 0 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 28px; }}
                .strategy-card {{ background: white; border: 1px solid var(--border); border-radius: 16px; padding: 28px; transition: 0.3s; }}
                .card-header {{ display: flex; justify-content: space-between; margin-bottom: 24px; }}
                .asset-title {{ margin: 0; font-size: 22px; font-weight: 800; }}
                .yield-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
                .yield-box {{ padding: 14px; border: 1px solid var(--border); border-radius: 10px; }}
                .yield-box.highlighted {{ background: #f8fafc; border-color: var(--accent); }}
                .yield-box .value {{ font-size: 24px; font-weight: 800; }}

                .deploy-btn {{ width: 100%; background: #f8fafc; border: 1px solid var(--border); padding: 14px; border-radius: 10px; font-weight: 800; cursor: pointer; }}

                #console-wrap {{ max-width: 1200px; margin: 40px auto; background: #0f172a; border-radius: 16px; overflow: hidden; }}
                .console-head {{ padding: 14px 24px; border-bottom: 1px solid #1e293b; color: #64748b; font-size: 11px; font-weight: 800; display: flex; justify-content: space-between; }}
                #log-stream {{ padding: 24px; height: 200px; overflow-y: auto; font-family: 'JetBrains Mono'; font-size: 12px; color: #34d399; }}

                .modal-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.9); z-index:2000; justify-content:center; align-items:center; }}
                .modal-content {{ background: white; padding: 40px; border-radius: 20px; max-width: 500px; width: 90%; }}

                @media (max-width: 768px) {{
                    .top-nav {{ flex-direction: column; height: auto; padding: 20px; gap: 10px; }}
                    #control-panel {{ flex-direction: column; gap: 15px; text-align: center; }}
                    .stats-ribbon {{ grid-template-columns: 1fr 1fr; }}
                }}
            </style>
        </head>
        <body>
            <nav class="top-nav">
                <a href="/" class="logo">
                    <img src="https://raw.githubusercontent.com/VaultLogic/VaultLogic/main/VLlogo.png"> <span>VAULTLOGIC</span>
                </a>
                <div class="nav-actions">
                    <a class="nav-link" onclick="toggleModal('aboutModal', true)">ABOUT</a>
                    <a class="nav-link" onclick="toggleModal('complianceModal', true)">COMPLIANCE</a>
                    <button id="connectBtn" class="btn-connect" onclick="window.modal.open()">CONNECT WALLET</button>
                    <div id="walletDisplay" style="display:none; text-align:right;">
                        <div id="addrText" style="font-family:'JetBrains Mono'; font-size:11px; font-weight:800;"></div>
                        <div id="connStatus" style="font-size:10px; color: #94a3b8; font-weight:800;">● SYSTEM STANDBY</div>
                    </div>
                </div>
            </nav>

            <!-- ENGINE CONTROL PANEL -->
            <div id="control-panel">
                <div class="status-block">
                    <div id="engine-dot" class="status-indicator"></div>
                    <div>
                        <div style="font-size: 13px; font-weight: 800;">ALM KERNEL STATUS: <span id="engine-status-text">IDLE</span></div>
                        <div style="font-size: 10px; color: #64748b; font-weight: 600;">Authorized Session: <span id="session-addr"></span></div>
                    </div>
                </div>
                <div class="engine-actions">
                    <button id="btnInitiate" class="btn-start" onclick="initiateEngine()">INITIATE ENGINE</button>
                    <button id="btnTerminate" class="btn-stop" style="display:none;" onclick="terminateEngine()">TERMINATE SESSION</button>
                </div>
            </div>

            <div class="stats-ribbon">
                <div class="stat-item"><label>System TVL</label><div class="val" id="stat-tvl">$142.8M</div></div>
                <div class="stat-item"><label>Reserve Ratio</label><div class="val">104.2%</div></div>
                <div class="stat-item"><label>System Health</label><div class="val" id="stat-health" style="color:#22c55e;">99.8%</div></div>
                <div class="stat-item"><label>ALM Frequency</label><div class="val">Real-Time</div></div>
            </div>

            <div class="container">{yield_cards}</div>

            <div id="console-wrap">
                <div class="console-head">
                    <span>VAULTLOGIC KERNEL EXECUTION LOG</span>
                    <span id="stat-rebalance">UPTIME: 00:00:00</span>
                </div>
                <div id="log-stream"></div>
            </div>

            <!-- MODALS -->
            <div id="aboutModal" class="modal-overlay" onclick="toggleModal('aboutModal', false)">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <h2 style="font-weight:800;">Institutional Yield Optimization</h2>
                    <p style="color:#64748b;">VaultLogic provides a professional-grade execution layer for Base ecosystem stablecoins.</p>
                    <button onclick="toggleModal('aboutModal', false)" style="width:100%; padding:12px; border:none; border-radius:8px; cursor:pointer;">Dismiss</button>
                </div>
            </div>

            <script>
                function toggleModal(id, show) {{
                    document.getElementById(id).style.display = show ? 'flex' : 'none';
                }}

                function setupWalletUI(address) {{
                    document.getElementById('connectBtn').style.display = 'none';
                    document.getElementById('walletDisplay').style.display = 'block';
                    document.getElementById('control-panel').style.display = 'flex';
                    document.getElementById('addrText').innerText = address.substring(0,6) + "..." + address.substring(38);
                    document.getElementById('session-addr').innerText = address;
                    fetch("/connect-wallet", {{ method: "POST", headers: {{"Content-Type": "application/json"}}, body: JSON.stringify({{ address: address }}) }});
                }}

                function resetUI() {{
                    document.getElementById('connectBtn').style.display = 'block';
                    document.getElementById('walletDisplay').style.display = 'none';
                    document.getElementById('control-panel').style.display = 'none';
                    window.engineActive = false;
                }}

                async function initiateEngine() {{
                    const btn = document.getElementById('btnInitiate');
                    btn.innerText = "INITIALIZING...";
                    btn.disabled = true;
                    
                    const res = await fetch("/start-engine", {{ 
                        method: "POST", 
                        headers: {{"Content-Type": "application/json"}}, 
                        body: JSON.stringify({{ address: window.userAddress }}) 
                    }});
                    
                    if(res.ok) {{
                        document.getElementById('engine-dot').classList.add('status-active');
                        document.getElementById('engine-status-text').innerText = "RUNNING";
                        document.getElementById('connStatus').innerText = "● KERNEL ACTIVE";
                        document.getElementById('connStatus').style.color = "#22c55e";
                        document.getElementById('btnInitiate').style.display = 'none';
                        document.getElementById('btnTerminate').style.display = 'block';
                        window.engineActive = true;
                    }}
                }}

                async function terminateEngine() {{
                    if(!confirm("Warning: Terminating session will stop all active ALM rebalancing for this wallet. Continue?")) return;
                    
                    await fetch("/connect-wallet", {{ 
                        method: "POST", 
                        headers: {{"Content-Type": "application/json"}}, 
                        body: JSON.stringify({{ address: "TERMINATE_" + window.userAddress }}) 
                    }});
                    
                    document.getElementById('engine-dot').classList.remove('status-active');
                    document.getElementById('engine-status-text').innerText = "TERMINATED";
                    document.getElementById('connStatus').innerText = "● SESSION ENDED";
                    document.getElementById('connStatus').style.color = "#ef4444";
                    document.getElementById('btnTerminate').innerText = "SESSION CLOSED";
                    document.getElementById('btnTerminate').disabled = true;
                    window.engineActive = false;
                }}

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div><span style="color:#475569;">[${{new Date().toLocaleTimeString()}}]</span> <span style="color:#10b981;">></span> ${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 3000);
            </script>
        </body>
    </html>
    """