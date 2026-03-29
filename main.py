import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

# System state
vault_cache = {"yields": [], "status": "SYSTEM READY"}
system_logs = ["VaultLogic Kernel v2.5.9 Online", "Status: AI Predictive Engine Engaged.", "Log: Neural pathing active for Multi-Currency pairs."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

async def get_industrial_yields():
    return [
        {"protocol": "MORPHO BLUE", "apy": 3.62, "predicted": 3.85, "asset": "USDC", "type": "ORGANIC", "currency": "USD"},
        {"protocol": "AAVE V3", "apy": 2.87, "predicted": 2.95, "asset": "USDC", "type": "ORGANIC", "currency": "USD"},
        {"protocol": "AERODROME", "apy": 12.41, "predicted": 11.15, "asset": "cbBTC/WETH", "type": "BOOSTED", "currency": "MULTI"},
        {"protocol": "UNISWAP V3", "apy": 3.55, "predicted": 4.10, "asset": "USDC/ETH", "type": "CONCENTRATED", "currency": "MULTI"},
        {"protocol": "BEEFY", "apy": 8.15, "predicted": 8.02, "asset": "WETH/USDC LP", "type": "AUTO-COMPOUND", "currency": "MULTI"}
    ]

@app.post("/connect-wallet")
async def connect(data: WalletConnect):
    try:
        from engine import run_alm_engine
        if data.address == "DISCONNECT":
            add_log("SYSTEM: Wallet Session Terminated.")
            return {"status": "disconnected"}
        asyncio.create_task(run_alm_engine(data.address, log_callback=add_log))
        return {"status": "success"}
    except Exception as e:
        add_log(f"KERNEL_ERR: {str(e)}")
        return {"status": "error"}

@app.get("/logs")
async def get_logs():
    return {"logs": system_logs}

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
            <div class="card-glow"></div>
            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px; position:relative; z-index:1;">
                <h3 style="margin:0; color:#00ffa3; font-size:12px; letter-spacing:1px; font-weight:800;">{y['protocol']}</h3>
                <span class="type-tag">{y['type']}</span>
            </div>
            <div class="yield-display">
                <div class="current-apy">
                    <p style="margin:5px 0; font-size:32px; font-weight:800; color:#ffffff;">{y['apy']}% <span style="font-size:12px; color:#475569; font-weight:400;">APR</span></p>
                    <small style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:1px;">{y['asset']}</small>
                </div>
                <div class="ai-shadow">
                    <span style="font-size:9px; letter-spacing:1px; color:#00ffa3; font-weight:bold; text-transform:uppercase;">AI FORECAST (24H)</span>
                    <span style="font-size:24px; font-weight:800; color:#fff; display:block;">{y['predicted']}%</span>
                </div>
            </div>
            <button onclick="deployFunds(this, '{y['protocol']}')" class="deploy-btn">
                DEPLOY {y['asset'].split('/')[0]}
            </button>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic | Industrial ALM</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
                
                :root {{
                    --bg: #000000;
                    --card-bg: #0a0a0a;
                    --accent: #00ffa3;
                    --border: #1a1a1a;
                    --text: #ffffff;
                    --text-muted: #666666;
                }}

                body {{ 
                    background: var(--bg); 
                    color: var(--text); 
                    font-family: 'Inter', sans-serif; 
                    margin:0; 
                    line-height:1.6;
                }}
                
                .top-nav {{ 
                    background: rgba(0,0,0,0.8); 
                    backdrop-filter: blur(10px);
                    border-bottom: 1px solid var(--border); 
                    padding: 15px 40px; 
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center; 
                    position: sticky; 
                    top: 0; 
                    z-index: 100; 
                }}

                .logo-container {{ display: flex; align-items: center; gap: 12px; text-decoration: none; color: inherit; }}
                .logo-img {{ height: 28px; width: auto; }}
                .logo-fallback {{ 
                    display: none; background: var(--accent); color: #000; 
                    padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 14px; 
                }}
                
                .nav-links a {{ margin-left: 20px; text-decoration: none; color: var(--text-muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; cursor:pointer; }}
                .nav-links a:hover {{ color: var(--accent); }}

                .hero-section {{ padding: 80px 20px; text-align: center; border-bottom: 1px solid var(--border); background: radial-gradient(circle at 50% 0%, #00ffa311 0%, transparent 50%); }}
                
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); max-width:1200px; margin:40px auto; gap:20px; padding: 0 20px; }}
                
                .strategy-card {{ 
                    background: var(--card-bg); 
                    padding: 25px; 
                    border-radius: 4px; 
                    border: 1px solid var(--border); 
                    position: relative; 
                    transition: all 0.3s ease;
                    overflow: hidden;
                }}
                .strategy-card:hover {{ border-color: var(--accent); }}
                .card-glow {{ 
                    position: absolute; top:0; left:0; width:2px; height:100%; 
                    background: var(--accent); opacity: 0.5; 
                }}

                .type-tag {{ font-size:9px; color: var(--text-muted); border: 1px solid var(--border); padding:2px 8px; border-radius:2px; text-transform: uppercase; font-weight: 700; }}

                .yield-display {{ position: relative; height: 90px; margin: 20px 0; }}
                .ai-shadow {{ 
                    position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                    background: var(--card-bg); opacity: 0; transform: translateY(10px); 
                    transition: all 0.3s ease; display: flex; flex-direction: column; justify-content: center;
                }}
                .strategy-card:hover .ai-shadow {{ opacity: 1; transform: translateY(0); }}

                .deploy-btn {{ 
                    width:100%; background: var(--accent); color:#000; border:none; 
                    padding:12px; font-weight:800; font-size:11px; cursor:pointer; 
                    letter-spacing: 1px; transition: opacity 0.2s;
                }}
                .deploy-btn:hover {{ opacity: 0.8; }}

                #console {{ max-width:1160px; margin:40px auto; background: #050505; border: 1px solid var(--border); border-radius: 4px; }}
                .console-header {{ background: #0a0a0a; padding: 12px 20px; display:flex; justify-content:space-between; border-bottom: 1px solid var(--border); }}
                #log-stream {{ padding: 20px; height: 250px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--accent); text-align: left; }}
                
                .status-badge {{ font-size:10px; color: var(--accent); border: 1px solid var(--accent); padding:4px 12px; border-radius:20px; display:inline-block; font-weight: 800; text-transform: uppercase; margin-bottom: 20px; }}

                .connect-btn {{ background: transparent; color: var(--text); border: 1px solid var(--text); padding: 8px 20px; font-size: 12px; font-weight: 700; cursor: pointer; }}
                .connect-btn:hover {{ background: var(--text); color: #000; }}
            </style>
        </head>
        <body>
            <nav class="top-nav">
                <a href="/" class="logo-container">
                    <img id="mainLogo" src="https://raw.githubusercontent.com/VaultLogic/VaultLogic/main/VLlogo.png" 
                         onerror="document.getElementById('mainLogo').style.display='none'; document.getElementById('logoFallback').style.display='block';" 
                         class="logo-img" alt="VaultLogic">
                    <div id="logoFallback" class="logo-fallback">VAULTLOGIC</div>
                </a>
                <div class="nav-links">
                    <a href="#strategies">Vaults</a>
                    <a href="#compliance">Audit</a>
                    <button id="connectBtn" class="connect-btn" onclick="connectWallet()">CONNECT WALLET</button>
                    <div id="walletDisplay" style="display:none; color: var(--accent); font-family: 'JetBrains Mono'; font-size: 11px;"></div>
                </div>
            </nav>

            <div class="hero-section">
                <div class="status-badge">Kernel v2.5.9 // Online</div>
                <h1 style="font-size:52px; font-weight:800; margin:0; letter-spacing:-2px;">INDUSTRIAL LIQUIDITY.</h1>
                <p style="color: var(--text-muted); max-width:500px; margin:15px auto; font-size:16px;">Autonomous yield forecasting and principal protection for institutional-grade stablecoins.</p>
            </div>
            
            <div id="strategies" class="container">{yield_cards}</div>

            <div id="console">
                <div class="console-header">
                    <span style="font-weight:800; font-size:10px; color: var(--text-muted); letter-spacing:1px;">EXECUTION LOG (LIVE)</span>
                    <button onclick="window.location='/download-logs'" style="background:none; border:none; color:var(--accent); font-size:10px; cursor:pointer; font-weight:800;">EXPORT AUDIT</button>
                </div>
                <div id="log-stream"></div>
            </div>

            <script>
                let activeAddress = null;

                async function connectWallet() {{
                    if (window.ethereum) {{
                        try {{
                            const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                            activeAddress = accounts[0];
                            document.getElementById('connectBtn').style.display = 'none';
                            const disp = document.getElementById('walletDisplay');
                            disp.style.display = 'block';
                            disp.innerText = activeAddress.substring(0,6) + "..." + activeAddress.substring(38);
                            
                            await fetch("/connect-wallet", {{
                                method: "POST",
                                headers: {{ "Content-Type": "application/json" }},
                                body: JSON.stringify({{ address: activeAddress }})
                            }});
                        }} catch (err) {{ console.error(err); }}
                    }}
                }}

                function deployFunds(btn, protocol) {{
                    if (!activeAddress) {{ alert("Connection Required"); return; }}
                    btn.innerText = "EXECUTING...";
                    btn.disabled = true;
                    setTimeout(() => {{ btn.innerText = "ACTIVE"; btn.style.background = "#fff"; }}, 2000);
                }}

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div><span style="opacity:0.5; margin-right:10px;">></span> ${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 3000);
            </script>
        </body>
    </html>
    """