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
            <!-- Modern Wallet Connection Library -->
            <script src="https://cdn.jsdelivr.net/npm/@coinbase/wallet-sdk@3.7.1/dist/index.js"></script>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
                body {{ background:#f8fafc; color:#1e293b; font-family: 'Inter', sans-serif; text-align:center; padding:0; margin:0; line-height:1.6; scroll-behavior: smooth; }}
                
                .top-nav {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 10px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
                .logo-container {{ display: flex; align-items: center; gap: 12px; text-decoration: none; color: inherit; }}
                .logo-img {{ height: 36px; width: auto; border-radius: 4px; }}
                .logo-text {{ font-weight: 800; letter-spacing: 1.5px; color: #0f172a; font-size: 20px; text-transform: uppercase; }}
                
                .nav-links a {{ margin-left: 20px; text-decoration: none; color: #64748b; font-size: 13px; font-weight: 600; cursor:pointer; }}
                
                .hero-section {{ padding: 100px 20px; background: white; border-bottom: 1px solid #e2e8f0; }}
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
                .initiate-btn {{ background:#2563eb; border:none; color:white; padding:15px 40px; border-radius:10px; font-weight:800; font-size:16px; cursor:pointer; margin-top: 20px; transition: transform 0.2s; }}
                
                #aboutModal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(255,255,255,0.98); z-index:2000; justify-content:center; align-items:center; }}
                .modal-content {{ max-width: 800px; text-align: left; padding: 40px; }}

                @media (max-width: 768px) {{
                    .top-nav {{ padding: 15px 20px; flex-direction: column; gap: 15px; }}
                    .nav-links {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; width: 100%; }}
                    .nav-links a {{ margin-left: 0; padding: 5px 10px; font-weight: 400; color: #94a3b8; font-size: 12px; }}
                    .logo-text {{ font-size: 16px; }}
                    .hero-section h1 {{ font-size: 38px; }}
                    .initiate-btn {{ width: 100%; }}
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
                    <a onclick="toggleAbout(true)">About</a>
                    <a href="#strategies">Strategies</a>
                    <a href="#tax-center">Compliance</a>
                    <button id="connectBtn" class="connect-btn" onclick="connectWallet()">Connect Wallet</button>
                    <div id="walletDisplay" style="display:none; align-items:center; flex-direction:column; gap:5px;">
                        <span id="addrText" style="font-family:'JetBrains Mono'; font-size:10px; color:#64748b;"></span>
                        <button style="background:#fff; color:#ef4444; border:1px solid #fee2e2; padding:4px 12px; font-size:10px; cursor:pointer; border-radius:8px; font-weight:700;" onclick="location.reload()">Stop Engine</button>
                    </div>
                </div>
            </nav>

            <div id="aboutModal">
                <div class="modal-content">
                    <button onclick="toggleAbout(false)" style="float:right; cursor:pointer; background:none; border:1px solid #e2e8f0; padding:5px 15px; border-radius:5px;">Close</button>
                    <h2 style="font-size: 32px; font-weight: 800; color: #0f172a;">Our Mission</h2>
                    <p style="font-size: 18px; color: #64748b; line-height: 1.8;">Industrial Asset-Liability Management on Base. Built for Institutional Stability.</p>
                </div>
            </div>

            <div class="hero-section">
                <h1 style="font-weight:800; color:#0f172a; margin:10px 0; line-height:1.1;">Global Treasury.<br>Automated Alpha.</h1>
                <p style="color:#64748b; max-width:650px; margin:25px auto 30px; font-size:17px; padding: 0 10px;">Sophisticated yield management for USDC and EURC.</p>
                <button onclick="initiateEngine(this)" class="initiate-btn">Initiate Engine</button>
            </div>

            <div class="filter-bar">
                <div class="filter-pill active" onclick="filterVaults('ALL', this)">All</div>
                <div class="filter-pill" onclick="filterVaults('USD', this)">Digital USD</div>
                <div class="filter-pill" onclick="filterVaults('EUR', this)">Digital Euro</div>
            </div>
            
            <div id="strategies" class="container">{yield_cards}</div>

            <div id="console">
                <div id="log-stream"></div>
            </div>

            <script>
                let activeAddress = null;

                // --- NEW ROBUST CONNECTION LOGIC ---
                async function connectWallet() {{
                    const connectBtn = document.getElementById('connectBtn');
                    connectBtn.innerText = "Requesting Access...";

                    // 1. Check for MetaMask/Browser Extension
                    if (window.ethereum) {{
                        try {{
                            const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                            setupWalletUI(accounts[0]);
                            return;
                        }} catch (err) {{
                            console.error("Browser wallet rejected", err);
                        }}
                    }}

                    // 2. Fallback: Coinbase Wallet SDK (Works on Mobile Safari/Chrome)
                    try {{
                        const coinbaseWallet = new CoinbaseWalletSDK({{
                            appName: "VaultLogic",
                            appLogoUrl: "https://raw.githubusercontent.com/VaultLogic/VaultLogic/main/VLlogo.png",
                            darkMode: false
                        }});
                        const ethereum = coinbaseWallet.makeWeb3Provider("https://mainnet.base.org", 8453);
                        const accounts = await ethereum.request({{ method: 'eth_requestAccounts' }});
                        setupWalletUI(accounts[0]);
                    }} catch (err) {{
                        connectBtn.innerText = "Connection Failed";
                        setTimeout(() => connectBtn.innerText = "Connect Wallet", 2000);
                        alert("No wallet found. Please install Coinbase Wallet or MetaMask.");
                    }}
                }}

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

                function toggleAbout(show) {{
                    document.getElementById('aboutModal').style.display = show ? 'flex' : 'none';
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

                async function initiateEngine(btn) {{
                    if (!activeAddress) {{ 
                        connectWallet();
                        return; 
                    }}
                    btn.innerText = "Engine Engaged...";
                    btn.style.background = "#059669";
                    await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: activeAddress + "_INITIATE_SYSTEM" }})
                    }});
                }}

                async function deployFunds(btn, protocol) {{
                    if (!activeAddress) {{ connectWallet(); return; }}
                    btn.innerText = "Securing Path...";
                    setTimeout(() => {{ btn.innerText = "Active"; btn.style.background = "#059669"; }}, 1000);
                }}

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div style="padding:5px 0; border-bottom:1px solid #1e293b;">> ${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 3000);
            </script>
        </body>
    </html>
    """