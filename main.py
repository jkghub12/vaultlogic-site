import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

# System state
vault_cache = {"yields": [], "status": "SYSTEM READY"}
system_logs = ["VaultLogic Kernel v2.5.7 Online", "Status: AI Predictive Engine Engaged.", "Log: Neural pathing active for Multi-Currency pairs."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

async def get_industrial_yields():
    return [
        {"protocol": "MORPHO BLUE", "apy": 3.62, "predicted": 3.85, "asset": "USDC", "type": "STABLE", "currency": "USD"},
        {"protocol": "AAVE V3", "apy": 4.12, "predicted": 4.25, "asset": "EURC", "type": "GLOBAL", "currency": "EUR"},
        {"protocol": "AERODROME", "apy": 12.41, "predicted": 11.15, "asset": "PYUSD/USDC", "type": "BOOSTED", "currency": "USD"},
        {"protocol": "UNISWAP V3", "apy": 3.55, "predicted": 4.10, "asset": "USDC/EURC", "type": "FOREX", "currency": "MULTI"},
        {"protocol": "BEEFY", "apy": 8.15, "predicted": 8.02, "asset": "EURC/USDC LP", "type": "AUTO-COMPOUND", "currency": "EUR"}
    ]

@app.post("/connect-wallet")
async def connect(data: WalletConnect):
    try:
        from engine import run_alm_engine
        if data.address == "DISCONNECT":
            add_log("SYSTEM: Wallet Session Terminated by User.")
            return {"status": "disconnected"}
        if "INITIATE_SYSTEM" in data.address:
            add_log("SYSTEM: Global Engine Start. Scanning for optimal rebalance path...")
        asyncio.create_task(run_alm_engine(data.address, log_callback=add_log))
        return {"status": "success"}
    except Exception as e:
        add_log(f"KERNEL_ERR: {str(e)}")
        return {"status": "error"}

@app.get("/logs")
async def get_logs():
    return {"logs": system_logs}

@app.get("/download-logs")
async def download_logs():
    csv_content = "Timestamp,Event\n"
    for log in system_logs:
        csv_content += f"{log}\n"
    return PlainTextResponse(csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=vaultlogic_audit_log.csv"})

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
        <div class="strategy-card" data-currency="{y['currency']}">
            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px;">
                <h3 style="margin:0; color:#1a2b4b; font-size:14px; font-weight:700;">{y['protocol']}</h3>
                <span style="font-size:10px; color:#2563eb; background:#eff6ff; padding:4px 8px; border-radius:20px; font-weight:600;">{y['type']}</span>
            </div>
            <div class="yield-display">
                <div class="current-apy">
                    <p style="margin:5px 0; font-size:32px; font-weight:800; color:#0f172a;">{y['apy']}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">APR</span></p>
                </div>
                <div class="ai-shadow">
                    <span style="font-size:10px; letter-spacing:1px; color:#2563eb; font-weight:bold;">AI FORECAST (24H):</span>
                    <span style="font-size:22px; font-weight:700; color:#1e293b; display:block;">{y['predicted']}%</span>
                </div>
            </div>
            <div style="margin-bottom:20px;">
                <small style="color:#64748b; font-size:12px;">Asset: <strong>{y['asset']}</strong></small>
            </div>
            <button onclick="deployFunds(this, '{y['protocol']}')" class="deploy-btn">
                Deploy Liquidity
            </button>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic | Global ALM</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <!-- Reown AppKit Configuration -->
            <script type="module">
                import {{ createAppKit }} from 'https://esm.sh/@reown/appkit'
                import {{ Ethers5Adapter }} from 'https://esm.sh/@reown/appkit-adapter-ethers5'
                import {{ base }} from 'https://esm.sh/@reown/appkit/networks'

                const projectId = '2b936cf692d84ae6da1ba91950c96420';

                const modal = createAppKit({{
                    adapters: [new Ethers5Adapter()],
                    networks: [base],
                    projectId,
                    themeMode: 'light',
                    featuredWalletIds: [
                        'fd20dc426fb37566d803205b19bbc1d4096b248ac04547e3cfb6b3a38bd033aa', // Coinbase Wallet
                        'c57ca71047597b42ddc9d30d30569074b83049102b4d8f5a62e399580577b30c', // MetaMask
                        '4622a2b2d6af1c9844944291e5e7351a6aaad53059ba587f21f0089e7a159176'  // Binance
                    ],
                    metadata: {{
                        name: 'VaultLogic',
                        description: 'Institutional ALM on Base',
                        url: window.location.origin,
                        icons: ['https://raw.githubusercontent.com/VaultLogic/VaultLogic/main/VLlogo.png']
                    }},
                    features: {{ analytics: true, email: false, social: false }},
                    themeVariables: {{ '--w3m-accent': '#2563eb', '--w3m-border-radius-master': '10px' }}
                }});

                window.modal = modal;

                modal.subscribeAccount(state => {{
                    if (state.isConnected && state.address) {{
                        setupWalletUI(state.address);
                    }}
                }});
            </script>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
                body {{ background:#f8fafc; color:#1e293b; font-family: 'Inter', sans-serif; text-align:center; padding:0; margin:0; line-height:1.6; scroll-behavior: smooth; }}
                
                .top-nav {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 10px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
                .logo-container {{ display: flex; align-items: center; gap: 12px; text-decoration: none; color: inherit; }}
                .logo-img {{ height: 36px; width: auto; border-radius: 4px; }}
                .logo-text {{ font-weight: 800; letter-spacing: 1.5px; color: #0f172a; font-size: 20px; text-transform: uppercase; }}
                
                .nav-links {{ display: flex; align-items: center; gap: 20px; }}
                .nav-links a {{ text-decoration: none; color: #64748b; font-size: 13px; font-weight: 600; cursor:pointer; transition: color 0.2s; }}
                .nav-links a:hover {{ color: #2563eb; }}
                
                .hero-section {{ padding: 80px 20px; background: white; border-bottom: 1px solid #e2e8f0; }}
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); max-width:1200px; margin:20px auto 60px; gap:25px; padding: 0 20px; }}
                .strategy-card {{ background:#fff; padding:30px; border-radius:16px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); text-align:left; position: relative; transition: all 0.4s ease; overflow: hidden; }}
                .strategy-card:hover {{ transform: translateY(-8px); border-color: #2563eb; }}
                
                .yield-display {{ position: relative; height: 75px; display: flex; align-items: center; }}
                .ai-shadow {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: white; opacity: 0; transform: translateY(20px); transition: all 0.4s ease; display: flex; flex-direction: column; justify-content: center; pointer-events: none; }}
                .strategy-card:hover .ai-shadow {{ opacity: 1; transform: translateY(0); }}
                
                .deploy-btn {{ width:100%; background:#2563eb; color:#fff; border:none; padding:14px; font-weight:700; font-size:13px; cursor:pointer; border-radius:10px; transition: background 0.2s; }}
                
                .filter-bar {{ max-width: 1200px; margin: 30px auto 10px; padding: 0 20px; display: flex; gap: 12px; justify-content: center; overflow-x: auto; }}
                .filter-pill {{ padding: 8px 20px; border-radius: 25px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid #e2e8f0; background: white; color: #64748b; white-space: nowrap; }}
                .filter-pill.active {{ background: #0f172a; color: white; border-color: #0f172a; }}

                #console {{ max-width:1160px; margin:40px auto; background:#0f172a; border-radius:16px; overflow:hidden; }}
                #log-stream {{ padding: 25px; height: 300px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #94a3b8; background: #0f172a; text-align: left; }}
                
                .connect-btn {{ background:#0f172a; color:#fff; border:none; padding:12px 28px; font-weight:700; cursor:pointer; border-radius:10px; font-size:14px; }}
                .inst-btn {{ background:transparent; border:1px solid #e2e8f0; color:#0f172a; padding:12px 20px; border-radius:10px; font-weight:700; cursor:pointer; font-size:14px; }}
                
                .modal-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(255,255,255,0.98); z-index:2000; justify-content:center; align-items:center; }}
                .modal-content {{ max-width: 600px; width: 90%; text-align: left; padding: 40px; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); background: white; }}

                @media (max-width: 768px) {{
                    .top-nav {{ padding: 15px 20px; flex-direction: column; gap: 15px; position: relative; }}
                    .nav-links {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; width: 100%; }}
                    .nav-links a {{ margin-left: 0; padding: 5px 10px; }}
                    .logo-text {{ font-size: 16px; }}
                    .hero-section h1 {{ font-size: 36px; }}
                }}
            </style>
        </head>
        <body>
            <nav class="top-nav">
                <a href="/" class="logo-container">
                    <img id="vlLogoImg" src="https://raw.githubusercontent.com/VaultLogic/VaultLogic/main/VLlogo.png" class="logo-img" alt="VaultLogic">
                    <div class="logo-text">VAULTLOGIC</div>
                </a>
                <div class="nav-links">
                    <a onclick="toggleModal('aboutModal', true)">About</a>
                    <a href="#strategies">Strategies</a>
                    <a onclick="toggleModal('complianceModal', true)">Compliance</a>
                    <button class="inst-btn" onclick="toggleModal('loginModal', true)">Inst. Login</button>
                    <button id="connectBtn" class="connect-btn" onclick="window.modal.open()">Connect</button>
                    <div id="walletDisplay" style="display:none; align-items:center; flex-direction:column; gap:5px;">
                        <span id="addrText" style="font-family:'JetBrains Mono'; font-size:10px; color:#64748b;"></span>
                        <button style="background:#fff; color:#ef4444; border:1px solid #fee2e2; padding:4px 12px; font-size:10px; cursor:pointer; border-radius:8px; font-weight:700;" onclick="location.reload()">Stop Engine</button>
                    </div>
                </div>
            </nav>

            <!-- MODALS -->
            <div id="aboutModal" class="modal-overlay" onclick="toggleModal('aboutModal', false)">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <h2 style="font-size: 28px; font-weight: 800; color: #0f172a;">Industrial Trust</h2>
                    <p style="font-size: 16px; color: #64748b; line-height: 1.6;">VaultLogic provides automated Asset-Liability Management (ALM) for institutional treasuries. We prioritize principal protection and predictable yield over high-risk speculation.</p>
                    <button onclick="toggleModal('aboutModal', false)" style="width:100%; margin-top:20px; padding:12px; background:#f1f5f9; border:none; border-radius:8px; cursor:pointer; font-weight:700;">Dismiss</button>
                </div>
            </div>

            <div id="complianceModal" class="modal-overlay" onclick="toggleModal('complianceModal', false)">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <h2 style="font-size: 28px; font-weight: 800; color: #0f172a;">Compliance Center</h2>
                    <p style="color: #64748b;">Download your audit logs and tax reports below for institutional reporting.</p>
                    <div style="margin-top: 20px; display:flex; flex-direction:column; gap:10px;">
                        <button onclick="location.href='/download-logs'" style="background:#0f172a; color:white; padding:12px 20px; border:none; border-radius:8px; cursor:pointer; font-weight:700;">Download Audit CSV</button>
                        <button onclick="toggleModal('complianceModal', false)" style="padding:12px; background:#f1f5f9; border:none; border-radius:8px; cursor:pointer;">Close</button>
                    </div>
                </div>
            </div>

            <div id="loginModal" class="modal-overlay" onclick="toggleModal('loginModal', false)">
                <div class="modal-content" style="width: 350px; text-align:center;" onclick="event.stopPropagation()">
                    <h2 style="font-size: 22px; font-weight: 800; color: #0f172a;">Institutional Login</h2>
                    <p style="font-size:12px; color:#64748b; margin-bottom:20px;">Secure Key Authentication</p>
                    <input type="password" placeholder="System Key" style="width:100%; padding:15px; border:1px solid #e2e8f0; border-radius:10px; margin-bottom: 15px; box-sizing: border-box;">
                    <button onclick="alert('Access Restricted: Demo active. Please connect via Wallet.')" style="width:100%; background:#2563eb; color:white; padding:15px; border:none; border-radius:10px; font-weight:700; cursor:pointer; margin-bottom:10px;">Authenticate</button>
                    <button onclick="toggleModal('loginModal', false)" style="width:100%; padding:10px; background:none; border:none; color:#94a3b8; cursor:pointer;">Cancel</button>
                </div>
            </div>

            <div class="hero-section">
                <h1 style="font-weight:800; color:#0f172a; margin:10px 0; line-height:1.1; font-size:52px;">Global Treasury.<br>Automated Alpha.</h1>
                <p style="color:#64748b; max-width:600px; margin:25px auto 30px; font-size:16px; padding: 0 10px;">Industrial-grade yield management for digital assets. Optimized for the Base network.</p>
                <button onclick="window.modal.open()" class="initiate-btn" style="background:#2563eb; color:white; padding:18px 45px; border:none; border-radius:12px; font-weight:800; font-size:18px; cursor:pointer; transition:transform 0.1s active;">Initiate ALM Engine</button>
            </div>

            <div class="filter-bar">
                <div class="filter-pill active" onclick="filterVaults('ALL', this)">All Strategies</div>
                <div class="filter-pill" onclick="filterVaults('USD', this)">Digital USD</div>
                <div class="filter-pill" onclick="filterVaults('EUR', this)">Digital Euro</div>
            </div>
            
            <div id="strategies" class="container">{yield_cards}</div>

            <div id="console">
                <div style="background:#1e293b; padding:10px 20px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#94a3b8; font-size:10px; font-weight:800; letter-spacing:1px;">SYSTEM EVENT LOG</span>
                    <span style="color:#34d399; font-size:10px; font-weight:800;">LIVE UPDATES ON</span>
                </div>
                <div id="log-stream"></div>
            </div>

            <script>
                let activeAddress = null;

                function setupWalletUI(address) {{
                    activeAddress = address;
                    document.getElementById('connectBtn').style.display = 'none';
                    document.getElementById('walletDisplay').style.display = 'flex';
                    document.getElementById('addrText').innerText = address.substring(0,6) + "..." + address.substring(38);
                    
                    fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: address }})
                    }});
                }}

                function toggleModal(id, show) {{
                    document.getElementById(id).style.display = show ? 'flex' : 'none';
                }}

                function filterVaults(currency, el) {{
                    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
                    el.classList.add('active');
                    document.querySelectorAll('.strategy-card').forEach(card => {{
                        if (currency === 'ALL' || card.dataset.currency === currency || card.dataset.currency === 'MULTI') {{
                            card.style.display = 'block';
                        }} else {{
                            card.style.display = 'none';
                        }}
                    }});
                }}

                async function deployFunds(btn, protocol) {{
                    if (!activeAddress) {{ window.modal.open(); return; }}
                    btn.innerText = "Securing Path...";
                    setTimeout(() => {{ btn.innerText = "Active"; btn.style.background = "#059669"; }}, 1000);
                }}

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div style="padding:8px 0; border-bottom:1px solid #1e293b; color:#94a3b8; line-height:1.4;">> ${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 3000);
            </script>
        </body>
    </html>
    """