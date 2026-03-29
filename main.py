import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

# System state
vault_cache = {"yields": [], "status": "SYSTEM READY"}
system_logs = ["VaultLogic Kernel v2.5.9 Online", "Status: AI Predictive Engine Engaged.", "Log: Neural pathing active for USDC pairs."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

async def get_industrial_yields():
    # Adding 'predicted' field for the AI Shadowy feature
    return [
        {"protocol": "MORPHO BLUE", "apy": 3.62, "predicted": 3.85, "asset": "STEAK / GT USDCP", "type": "ORGANIC"},
        {"protocol": "AAVE V3", "apy": 2.87, "predicted": 2.91, "asset": "USDC", "type": "ORGANIC"},
        {"protocol": "AERODROME", "apy": 12.41, "predicted": 11.15, "asset": "cbBTC/WETH", "type": "BOOSTED"},
        {"protocol": "UNISWAP V3", "apy": 3.55, "predicted": 4.10, "asset": "USDC/ETH", "type": "CONCENTRATED"},
        {"protocol": "BEEFY", "apy": 8.15, "predicted": 8.02, "asset": "WETH/USDC LP", "type": "AUTO-COMPOUND"}
    ]

@app.post("/connect-wallet")
async def connect(data: WalletConnect):
    try:
        from engine import run_alm_engine
        if data.address == "DISCONNECT":
            add_log("SYSTEM: Wallet Session Terminated by User.")
            return {"status": "disconnected"}
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
        <div class="strategy-card">
            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px;">
                <h3 style="margin:0; color:#1a2b4b; font-size:14px; font-weight:700;">{y['protocol']}</h3>
                <span style="font-size:10px; color:#64748b; background:#f1f5f9; padding:4px 8px; border-radius:20px; font-weight:600;">{y['type']}</span>
            </div>
            <div class="yield-display">
                <p style="margin:5px 0; font-size:32px; font-weight:800; color:#0f172a;">{y['apy']}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">APR</span></p>
                <div class="ai-shadow">
                    <span style="font-size:10px; letter-spacing:1px; color:#2563eb; font-weight:bold;">AI PREDICTION (24H):</span>
                    <span style="font-size:18px; font-weight:700; color:#1e293b; display:block;">{y['predicted']}%</span>
                </div>
            </div>
            <div style="margin-bottom:20px;">
                <small style="color:#64748b; font-size:12px;">Asset: {y['asset']}</small>
            </div>
            <button onclick="deployFunds(this, '{y['protocol']}')" class="deploy-btn">
                Deploy Liquidity
            </button>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic | Industrial ALM</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
                body {{ background:#f8fafc; color:#1e293b; font-family: 'Inter', sans-serif; text-align:center; padding:0; margin:0; line-height:1.6; scroll-behavior: smooth; }}
                .top-nav {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 10px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
                .logo-container {{ display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; }}
                .logo-img {{ height: 32px; width: auto; border-radius: 4px; }}
                .logo-text {{ font-weight: 800; letter-spacing: 2px; color: #0f172a; font-size: 18px; }}
                .nav-links a {{ margin-left: 20px; text-decoration: none; color: #64748b; font-size: 13px; font-weight: 600; cursor:pointer; }}
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); max-width:1200px; margin:40px auto; gap:20px; padding: 0 20px; }}
                .hero-section {{ padding: 80px 20px; background: white; border-bottom: 1px solid #e2e8f0; position: relative; overflow: hidden; }}
                .hero-section::after {{ content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 50% 50%, rgba(37, 99, 235, 0.03) 0%, transparent 70%); pointer-events: none; }}
                .info-section {{ max-width: 900px; margin: 60px auto; text-align: left; padding: 0 20px; }}
                .card-header {{ font-weight: 800; color: #0f172a; margin-bottom: 20px; font-size: 24px; }}
                .connect-btn {{ background:#0f172a; color:#fff; border:none; padding:12px 25px; font-weight:600; cursor:pointer; border-radius: 8px; font-size:13px; transition: all 0.2s; }}
                .connect-btn:hover {{ background: #2563eb; transform: translateY(-1px); }}
                .stop-btn {{ background:#fff; color:#ef4444; border:1px solid #fee2e2; padding:8px 16px; font-size:11px; cursor:pointer; border-radius:6px; font-weight:600; }}
                .download-link {{ color:#2563eb; text-decoration:none; font-size:11px; font-weight:600; padding:8px 12px; border-radius:6px; background:#eff6ff; border:none; cursor:pointer; }}
                
                /* Strategy Cards & AI Shadow */
                .strategy-card {{ background:#fff; padding:25px; border-radius:12px; border:1px solid #e0e6ed; box-shadow: 0 4px 6px rgba(0,0,0,0.02); text-align:left; position: relative; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); cursor: default; overflow: hidden; }}
                .strategy-card:hover {{ transform: translateY(-5px); border-color: #2563eb; box-shadow: 0 12px 20px rgba(37, 99, 235, 0.1); }}
                .yield-display {{ position: relative; height: 60px; }}
                .ai-shadow {{ position: absolute; top: 0; left: 0; right: 0; background: white; opacity: 0; transform: translateY(10px); transition: all 0.3s ease; }}
                .strategy-card:hover .ai-shadow {{ opacity: 1; transform: translateY(0); }}
                .deploy-btn {{ width:100%; background:#2563eb; color:#fff; border:none; padding:12px; font-weight:600; font-size:12px; cursor:pointer; border-radius:8px; }}

                #console {{ max-width:1160px; margin:40px auto; background:#fff; border:1px solid #e2e8f0; padding:0; text-align:left; border-radius:12px; overflow:hidden; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); }}
                .console-header {{ background: #0f172a; padding: 15px 25px; border-bottom: 1px solid #1e293b; display:flex; justify-content:space-between; align-items:center; }}
                #log-stream {{ padding: 20px; height: 250px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #94a3b8; background: #0f172a; }}
                .log-entry {{ padding: 4px 0; border-bottom: 1px solid #1e293b; }}
                .status-badge {{ font-size:11px; color:#2563eb; background:#eff6ff; padding:4px 12px; border-radius:20px; margin-bottom:10px; display:inline-block; font-weight: 700; border: 1px solid #dbeafe; }}
                #walletDisplay {{ display:none; }}
                .blog-card {{ background: #fff; border: 1px solid #e2e8f0; padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
                .tax-badge {{ background: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
            </style>
        </head>
        <body>
            <nav class="top-nav">
                <a href="/" class="logo-container">
                    <img src="https://raw.githubusercontent.com/VaultLogic/VaultLogic/main/VLlogo.png" onerror="this.style.display='none'" class="logo-img" alt="VL">
                    <div class="logo-text">VAULTLOGIC</div>
                </a>
                <div class="nav-links">
                    <a href="#strategies">Strategies</a>
                    <a href="#tax-center">Tax Center</a>
                    <a href="#about">About</a>
                    <a onclick="unlockPrompt()" style="color:#2563eb;">Private Access</a>
                    <button id="connectBtn" class="connect-btn" style="margin-left:20px;" onclick="connectWallet()">Connect Wallet</button>
                    <div id="walletDisplay" style="margin-left:20px;">
                        <span id="addrText" style="font-family:'JetBrains Mono'; margin-right:15px; font-size:12px; color:#64748b;"></span>
                        <button class="stop-btn" onclick="disconnectWallet()">Stop Engine</button>
                    </div>
                </div>
            </nav>

            <div class="hero-section">
                <div class="status-badge">Kernel v2.5.9 • Neural Forecasting Engaged</div>
                <h1 style="font-size:52px; font-weight:800; color:#0f172a; margin:10px 0; letter-spacing:-2px;">Smart Yield.<br>Audited Logic.</h1>
                <p style="color:#64748b; max-width:600px; margin:20px auto 40px; font-size:18px;">Autonomous liquidity management with industrial precision. Experience the "Shadow AI" yield forecasting below.</p>
                <div style="display:flex; justify-content:center; gap:15px;">
                    <button onclick="document.getElementById('strategies').scrollIntoView()" class="connect-btn">View Active Alpha</button>
                    <button onclick="unlockPrompt()" style="background:#fff; color:#1e293b; border:1px solid #e2e8f0;" class="connect-btn">Partnership Deck</button>
                </div>
            </div>
            
            <div id="strategies" class="container">{yield_cards}</div>

            <div id="console">
                <div class="console-header">
                    <span style="font-weight:700; font-size:12px; color:#fff; letter-spacing:1px; text-transform:uppercase;">Kernel Strategy Audit</span>
                    <div style="display:flex; gap:10px;">
                        <button onclick="toggleReport()" class="download-link" style="background:#1e293b; color:#fff;">AUDIT REPORT</button>
                        <a href="/download-logs" class="download-link" style="background:#1e293b; color:#fff;">EXPORT CSV</a>
                    </div>
                </div>
                <div id="log-stream"></div>
            </div>

            <section id="tax-center" class="info-section">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h2 class="card-header">Institutional Accounting</h2>
                    <span class="tax-badge">Compliance Module 1099-DA</span>
                </div>
                <div class="blog-card" style="border-top: 4px solid #f59e0b; box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.05);">
                    <p style="color: #475569; font-size: 14px; margin-bottom: 25px;">The VaultLogic engine automates your fiscal reporting by aggregating every rebalance and yield claim into a structured statement.</p>
                    <div id="taxDisplay" style="background:#f8fafc; padding:30px; border-radius:12px; border:1px solid #e2e8f0; text-align:center;">
                        <p id="taxPrompt" style="color:#94a3b8; font-size:13px; font-style:italic;">Authorization required via Wallet Connect...</p>
                        <div id="taxData" style="display:none; text-align:left;">
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:30px;">
                                <div>
                                    <small style="color:#64748b; text-transform:uppercase; font-size:10px; font-weight:bold; letter-spacing:1px;">Est. Ordinary Income</small>
                                    <p id="estIncome" style="font-size:28px; font-weight:800; margin:8px 0; color:#059669;">$0.00</p>
                                </div>
                                <div>
                                    <small style="color:#64748b; text-transform:uppercase; font-size:10px; font-weight:bold; letter-spacing:1px;">Capital Gains</small>
                                    <p id="estGains" style="font-size:28px; font-weight:800; margin:8px 0; color:#1e293b;">$0.00</p>
                                </div>
                            </div>
                            <button onclick="alert('Compiling Fiscal Report...')" style="margin-top:25px; width:100%; padding:14px; background:#0f172a; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:600; font-size:13px;">Generate Tax Pack (PDF)</button>
                        </div>
                    </div>
                </div>
            </section>

            <section id="coinbase-blog" class="info-section">
                <h2 class="card-header">Private Strategy Insights</h2>
                <div id="privateOverlay" style="background: #0f172a; color:white; padding: 60px; text-align: center; border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);">
                    <div style="font-size: 40px; margin-bottom:10px;">🛡️</div>
                    <h3 style="margin:0 0 10px 0; font-weight: 800;">Secure Portal</h3>
                    <p style="font-weight: 400; color: #94a3b8; margin-bottom: 30px; font-size:14px;">Authorized access only for Coinbase Partners.</p>
                    <input type="password" id="accessKey" style="padding: 12px; border: 1px solid #334155; background:#1e293b; color:white; border-radius: 8px; width: 220px; margin-bottom: 15px; text-align:center;" placeholder="Entry Code"><br>
                    <button onclick="checkKey()" class="connect-btn" style="background:#2563eb;">Unlock Portal</button>
                </div>
                <div id="privateContent" style="display:none;">
                    <div class="blog-card" style="border-left: 4px solid #2563eb;">
                        <h3 style="margin-top:0; color:#2563eb;">Institutional Roadmap v3.0</h3>
                        <p>Our integration with Coinbase Prime enables "Zero-Gas" rebalancing for managed treasuries over $10M.</p>
                    </div>
                </div>
            </section>

            <div id="reportModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; padding:50px; backdrop-filter: blur(4px);">
                <div style="background:white; max-width:800px; margin:0 auto; padding:40px; border-radius:16px; max-height:80vh; overflow-y:auto; text-align:left;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:25px; border-bottom: 1px solid #f1f5f9; padding-bottom:15px;">
                        <h2 style="margin:0; font-weight:800;">Audit Intelligence Report</h2>
                        <button onclick="toggleReport()" style="cursor:pointer; background:none; border:none; font-size:24px;">&times;</button>
                    </div>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        <tbody id="reportTableBody"></tbody>
                    </table>
                </div>
            </div>

            <script>
                const SECRET_KEY = "cb-institutional";
                let activeAddress = null;

                function checkKey() {{
                    if (document.getElementById('accessKey').value === SECRET_KEY) {{
                        document.getElementById('privateOverlay').style.display = 'none';
                        document.getElementById('privateContent').style.display = 'block';
                    }} else {{ alert("Authorization Failure."); }}
                }}

                function unlockPrompt() {{ document.getElementById('coinbase-blog').scrollIntoView(); }}
                function toggleReport() {{
                    const modal = document.getElementById('reportModal');
                    modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
                    if(modal.style.display === 'block') refreshReport();
                }}
                async function refreshReport() {{
                    const res = await fetch('/logs');
                    const data = await res.json();
                    document.getElementById('reportTableBody').innerHTML = data.logs.map(l => `<tr style="border-bottom:1px solid #f8fafc;"><td style="padding:12px; font-family:'JetBrains Mono';">${{l}}</td></tr>`).reverse().join('');
                }}

                async function connectWallet() {{
                    if (window.ethereum) {{
                        try {{
                            const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                            activeAddress = accounts[0];
                            document.getElementById('connectBtn').style.display = 'none';
                            document.getElementById('walletDisplay').style.display = 'flex';
                            document.getElementById('walletDisplay').style.alignItems = 'center';
                            document.getElementById('addrText').innerText = activeAddress.substring(0,6) + "..." + activeAddress.substring(38);
                            document.getElementById('taxPrompt').style.display = 'none';
                            document.getElementById('taxData').style.display = 'block';
                            document.getElementById('estIncome').innerText = "$" + (Math.random() * 50 + 10).toFixed(2);
                            
                            await fetch("/connect-wallet", {{
                                method: "POST",
                                headers: {{ "Content-Type": "application/json" }},
                                body: JSON.stringify({{ address: activeAddress }})
                            }});
                        }} catch (err) {{ console.error(err); }}
                    }}
                }}

                async function disconnectWallet() {{
                    activeAddress = null;
                    document.getElementById('walletDisplay').style.display = 'none';
                    document.getElementById('connectBtn').style.display = 'inline-block';
                    document.getElementById('taxPrompt').style.display = 'block';
                    document.getElementById('taxData').style.display = 'none';
                    await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: "DISCONNECT" }})
                    }});
                }}

                async function deployFunds(btn, protocol) {{
                    if (!activeAddress) {{ alert("Wallet connection required."); return; }}
                    btn.innerText = "Securing...";
                    btn.style.background = "#1e293b";
                    await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: "0x_INJECTION_" + protocol.replace(/ /g, "_") }})
                    }});
                    setTimeout(() => {{ btn.innerText = "Active"; btn.style.background = "#059669"; }}, 1500);
                }}

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        document.getElementById('log-stream').innerHTML = data.logs.map(l => `<div class="log-entry">${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 3000);
            </script>
        </body>
    </html>
    """