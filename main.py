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
    "Log: Analyzing Morpho Blue liquidity depth...",
    "Risk: EURC/USDC peg stability confirmed at 1.0002."
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
        if data.address == "DISCONNECT":
            add_log("SYSTEM: Session Terminated.")
            return {"status": "disconnected"}
        asyncio.create_task(run_alm_engine(data.address, log_callback=add_log))
        return {"status": "success"}
    except Exception as e:
        add_log(f"ERR: {str(e)}")
        return {"status": "error"}

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
            <button onclick="deployFunds(this, '{y['protocol']}')" class="deploy-btn">DEPLOY CAPITAL</button>
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
                modal.subscribeAccount(state => {{ if(state.isConnected) setupWalletUI(state.address); }});
            </script>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
                :root {{ --primary: #0f172a; --accent: #2563eb; --border: #e2e8f0; }}
                body {{ background:#f1f5f9; color:var(--primary); font-family: 'Public Sans', sans-serif; margin:0; -webkit-font-smoothing: antialiased; }}
                
                /* Institutional Header Refinement */
                .top-nav {{ 
                    background: rgba(255, 255, 255, 0.9); 
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
                .logo {{ 
                    display: flex; 
                    align-items: center; 
                    gap: 12px; 
                    text-decoration: none; 
                    font-weight: 800; 
                    color: var(--primary); 
                    letter-spacing: -0.5px; 
                    font-size: 19px;
                    white-space: nowrap;
                }}
                .logo img {{ 
                    height: 34px; 
                    width: auto;
                    border-radius: 6px; 
                    object-fit: contain;
                }}
                
                .nav-actions {{ display: flex; gap: 24px; align-items: center; }}
                .nav-link {{ color: #64748b; font-size: 12px; font-weight: 700; text-decoration: none; cursor: pointer; letter-spacing: 0.5px; transition: color 0.2s; }}
                .nav-link:hover {{ color: var(--accent); }}
                
                .btn-connect {{ background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 13px; transition: transform 0.1s; }}
                .btn-connect:active {{ transform: scale(0.98); }}
                .btn-inst {{ border: 1px solid var(--border); background: white; padding: 10px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 13px; }}

                /* Stats Dashboard */
                .stats-ribbon {{ background: white; border-bottom: 1px solid var(--border); padding: 20px 40px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
                .stat-item label {{ font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 4px; }}
                .stat-item .val {{ font-size: 20px; font-weight: 800; color: var(--primary); }}

                /* Main Content */
                .container {{ max-width: 1200px; margin: 40px auto; padding: 0 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 28px; }}
                
                .strategy-card {{ background: white; border: 1px solid var(--border); border-radius: 16px; padding: 28px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }}
                .strategy-card:hover {{ border-color: var(--accent); transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.05); }}
                
                .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }}
                .protocol-label {{ font-size: 11px; font-weight: 800; color: var(--accent); text-transform: uppercase; }}
                .asset-title {{ margin: 4px 0 0 0; font-size: 22px; font-weight: 800; }}
                .risk-badge {{ font-size: 9px; font-weight: 900; padding: 5px 10px; border-radius: 6px; letter-spacing: 0.5px; }}
                .risk-low {{ background: #f0fdf4; color: #166534; }}
                .risk-minimal {{ background: #eff6ff; color: #1e40af; }}
                .risk-med {{ background: #fffbeb; color: #92400e; }}

                .yield-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
                .yield-box {{ padding: 14px; border: 1px solid var(--border); border-radius: 10px; }}
                .yield-box.highlighted {{ background: #f8fafc; border-color: var(--accent); }}
                .yield-box label {{ font-size: 10px; font-weight: 700; color: #64748b; display: block; margin-bottom: 4px; }}
                .yield-box .value {{ font-size: 24px; font-weight: 800; }}

                .util-bar {{ background: #f1f5f9; height: 20px; border-radius: 6px; position: relative; margin-bottom: 24px; overflow: hidden; border: 1px solid #e2e8f0; }}
                .util-fill {{ background: #cbd5e1; height: 100%; transition: width 1s ease; }}
                .util-text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 10px; font-weight: 800; color: #475569; }}

                .deploy-btn {{ width: 100%; background: #f8fafc; color: var(--primary); border: 1px solid var(--border); padding: 14px; border-radius: 10px; font-weight: 800; cursor: pointer; transition: 0.2s; font-size: 13px; letter-spacing: 0.5px; }}
                .deploy-btn:hover {{ background: var(--primary); color: white; border-color: var(--primary); }}

                /* Console */
                #console-wrap {{ max-width: 1200px; margin: 40px auto; background: #0f172a; border-radius: 16px; overflow: hidden; text-align: left; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); }}
                .console-head {{ padding: 14px 24px; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; font-size: 11px; font-weight: 800; color: #64748b; letter-spacing: 1px; }}
                #log-stream {{ padding: 24px; height: 220px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #34d399; line-height: 1.7; }}

                /* Modals */
                .modal-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.9); z-index:2000; justify-content:center; align-items:center; }}
                .modal-content {{ background: white; padding: 48px; border-radius: 20px; max-width: 500px; width: 90%; text-align: left; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }}

                @media (max-width: 768px) {{
                    .top-nav {{ padding: 0 20px; height: auto; min-height: 80px; flex-direction: column; justify-content: center; gap: 15px; padding-bottom: 15px; }}
                    .nav-actions {{ gap: 12px; flex-wrap: wrap; justify-content: center; }}
                    .stats-ribbon {{ grid-template-columns: 1fr 1fr; padding: 20px; }}
                    .stat-item .val {{ font-size: 17px; }}
                }}
            </style>
        </head>
        <body>
            <nav class="top-nav">
                <a href="/" class="logo">
                    <img src="https://raw.githubusercontent.com/VaultLogic/VaultLogic/main/VLlogo.png" alt="VL"> <span>VAULTLOGIC</span>
                </a>
                <div class="nav-actions">
                    <a class="nav-link" onclick="toggleModal('aboutModal', true)">ABOUT</a>
                    <a class="nav-link" onclick="toggleModal('complianceModal', true)">COMPLIANCE</a>
                    <button class="btn-inst" onclick="toggleModal('loginModal', true)">INST. LOGIN</button>
                    <button id="connectBtn" class="btn-connect" onclick="window.modal.open()">CONNECT WALLET</button>
                    <div id="walletDisplay" style="display:none; text-align:right;">
                        <div id="addrText" style="font-family:'JetBrains Mono'; font-size:11px; font-weight:800; color:var(--primary);"></div>
                        <div style="font-size:10px; color: #22c55e; font-weight:800;">● KERNEL ACTIVE</div>
                    </div>
                </div>
            </nav>

            <div class="stats-ribbon">
                <div class="stat-item"><label>System TVL</label><div class="val" id="stat-tvl">$142.8M</div></div>
                <div class="stat-item"><label>Reserve Ratio</label><div class="val">104.2%</div></div>
                <div class="stat-item"><label>System Health</label><div class="val" id="stat-health" style="color:#22c55e;">99.8%</div></div>
                <div class="stat-item"><label>ALM Frequency</label><div class="val">Real-Time</div></div>
            </div>

            <div class="container">{yield_cards}</div>

            <div id="console-wrap">
                <div class="console-head">
                    <span>SYSTEM KERNEL LOG</span>
                    <span id="stat-rebalance">LAST REBALANCE: 14M AGO</span>
                </div>
                <div id="log-stream"></div>
            </div>

            <!-- MODALS -->
            <div id="aboutModal" class="modal-overlay" onclick="toggleModal('aboutModal', false)">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <h2 style="font-size:28px; font-weight:800; margin-top:0;">Industrial Yield Optimization</h2>
                    <p style="color:#64748b; line-height:1.6;">VaultLogic uses a proprietary Asset-Liability Management engine to ensure that your digital treasury is always positioned in the highest-yielding, lowest-risk protocols on Base.</p>
                    <button onclick="toggleModal('aboutModal', false)" style="width:100%; background:#f1f5f9; border:none; padding:12px; border-radius:8px; font-weight:700; cursor:pointer; margin-top:20px;">Dismiss</button>
                </div>
            </div>

            <div id="complianceModal" class="modal-overlay" onclick="toggleModal('complianceModal', false)">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <h2 style="font-size:28px; font-weight:800; margin-top:0;">Audit & Transparency</h2>
                    <p style="color:#64748b; line-height:1.6;">All transactions are executed on-chain and are fully auditable. Download your historical data for tax and compliance reporting.</p>
                    <button onclick="location.href='/download-logs'" style="width:100%; background:#0f172a; color:white; padding:14px; border:none; border-radius:8px; font-weight:700; cursor:pointer; margin-top:10px;">Export Audit Trail (CSV)</button>
                    <button onclick="toggleModal('complianceModal', false)" style="width:100%; background:none; border:none; padding:12px; color:#94a3b8; cursor:pointer; font-weight:600;">Close</button>
                </div>
            </div>

            <div id="loginModal" class="modal-overlay" onclick="toggleModal('loginModal', false)">
                <div class="modal-content" style="max-width: 380px; text-align:center;" onclick="event.stopPropagation()">
                    <h3 style="font-size:24px; font-weight:800; margin-top:0;">Institutional Access</h3>
                    <p style="font-size:13px; color:#64748b; margin-bottom:24px;">Please authenticate via your hardware security module (HSM) or system key.</p>
                    <input type="password" placeholder="System Key" style="width:100%; padding:15px; border:1px solid #e2e8f0; border-radius:10px; margin-bottom:15px; font-size:16px;">
                    <button class="btn-connect" style="width:100%; padding:15px;" onclick="alert('Access Restricted to Whitelisted Keys.')">AUTHENTICATE</button>
                    <button onclick="toggleModal('loginModal', false)" style="width:100%; background:none; border:none; padding:12px; color:#94a3b8; cursor:pointer;">Cancel</button>
                </div>
            </div>

            <script>
                function toggleModal(id, show) {{
                    document.getElementById(id).style.display = show ? 'flex' : 'none';
                }}

                function setupWalletUI(address) {{
                    document.getElementById('connectBtn').style.display = 'none';
                    document.getElementById('walletDisplay').style.display = 'block';
                    document.getElementById('addrText').innerText = address.substring(0,6) + "..." + address.substring(38);
                    fetch("/connect-wallet", {{ method: "POST", headers: {{"Content-Type": "application/json"}}, body: JSON.stringify({{ address: address }}) }});
                }}

                async function deployFunds(btn, protocol) {{
                    if (!window.modal.getIsConnectedState()) {{ window.modal.open(); return; }}
                    btn.innerText = "EXECUTING...";
                    btn.style.background = "#0f172a";
                    btn.style.color = "white";
                    setTimeout(() => {{
                        btn.innerText = "POSITION ACTIVE";
                        btn.style.background = "#059669";
                    }}, 1500);
                }}

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div><span style="color:#475569; margin-right:8px;">[${{new Date().toLocaleTimeString()}}]</span> <span style="color:#10b981;">></span> ${{l}}</div>`).reverse().join('');
                        document.getElementById('stat-tvl').innerText = data.metrics.tvl;
                        document.getElementById('stat-health').innerText = data.metrics.health;
                    }} catch(e) {{}}
                }}, 3000);
            </script>
        </body>
    </html>
    """