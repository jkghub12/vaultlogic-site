import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

# System state
vault_cache = {"yields": [], "status": "SYSTEM READY"}
system_logs = ["VaultLogic Kernel v2.5.7 Online", "Status: Awaiting Wallet Connection..."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

async def get_industrial_yields():
    return [
        {"protocol": "MORPHO BLUE", "apy": 3.62, "asset": "STEAK / GT USDCP", "type": "ORGANIC"},
        {"protocol": "AAVE V3", "apy": 2.87, "asset": "USDC", "type": "ORGANIC"},
        {"protocol": "AERODROME", "apy": 12.41, "asset": "cbBTC/WETH", "type": "BOOSTED"},
        {"protocol": "UNISWAP V3", "apy": 3.55, "asset": "USDC/ETH", "type": "CONCENTRATED"},
        {"protocol": "BEEFY", "apy": 8.15, "asset": "WETH/USDC LP", "type": "AUTO-COMPOUND"}
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
        <div style="background:#fff; padding:25px; border-radius:12px; border:1px solid #e0e6ed; box-shadow: 0 4px 6px rgba(0,0,0,0.02); text-align:left;">
            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px;">
                <h3 style="margin:0; color:#1a2b4b; font-size:14px; font-weight:700;">{y['protocol']}</h3>
                <span style="font-size:10px; color:#64748b; background:#f1f5f9; padding:4px 8px; border-radius:20px; font-weight:600;">{y['type']}</span>
            </div>
            <p style="margin:5px 0; font-size:32px; font-weight:800; color:#0f172a;">{y['apy']}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">APR</span></p>
            <div style="margin-bottom:20px;">
                <small style="color:#64748b; font-size:12px;">Asset: {y['asset']}</small>
            </div>
            <button onclick="deployFunds(this, '{y['protocol']}')" class="deploy-btn" style="width:100%; background:#2563eb; color:#fff; border:none; padding:12px; font-weight:600; font-size:12px; cursor:pointer; border-radius:8px;">
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
                body {{ background:#f8fafc; color:#1e293b; font-family: 'Inter', sans-serif; text-align:center; padding:0; margin:0; line-height:1.6; scroll-behavior: smooth; }}
                .top-nav {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
                .logo {{ font-weight: 800; letter-spacing: 2px; color: #0f172a; font-size: 18px; }}
                .nav-links a {{ margin-left: 20px; text-decoration: none; color: #64748b; font-size: 13px; font-weight: 600; cursor:pointer; }}
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); max-width:1200px; margin:40px auto; gap:20px; padding: 0 20px; }}
                .hero-section {{ padding: 80px 20px; background: white; border-bottom: 1px solid #e2e8f0; }}
                .info-section {{ max-width: 900px; margin: 60px auto; text-align: left; padding: 0 20px; }}
                .card-header {{ font-weight: 800; color: #0f172a; margin-bottom: 20px; font-size: 24px; }}
                .connect-btn {{ background:#0f172a; color:#fff; border:none; padding:12px 25px; font-weight:600; cursor:pointer; border-radius: 8px; font-size:13px; }}
                .stop-btn {{ background:#fff; color:#ef4444; border:1px solid #fee2e2; padding:8px 16px; font-size:11px; cursor:pointer; border-radius:6px; font-weight:600; }}
                .download-link {{ color:#2563eb; text-decoration:none; font-size:11px; font-weight:600; padding:8px 12px; border-radius:6px; background:#eff6ff; }}
                #console {{ max-width:1160px; margin:40px auto; background:#fff; border:1px solid #e2e8f0; padding:0; text-align:left; border-radius:12px; overflow:hidden; }}
                .console-header {{ background: #f8fafc; padding: 15px 25px; border-bottom: 1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center; }}
                #log-stream {{ padding: 20px; height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; color: #475569; }}
                .log-entry {{ padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; border-left: 3px solid #e2e8f0; background: #f8fafc; }}
                .status-badge {{ font-size:11px; color:#64748b; background:#f1f5f9; padding:4px 12px; border-radius:20px; margin-bottom:10px; display:inline-block; }}
                #walletDisplay {{ display:none; }}
                .blog-card {{ background: #fff; border: 1px solid #e2e8f0; padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
                
                /* Private Access UI */
                #privateOverlay {{ 
                    background: #f1f5f9; border: 2px dashed #cbd5e1; padding: 40px; text-align: center; border-radius: 12px;
                }}
                .lock-icon {{ font-size: 32px; margin-bottom: 15px; display: block; }}
                .pw-input {{ padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; width: 200px; margin-bottom: 10px; }}
                #privateContent {{ display: none; }}
            </style>
        </head>
        <body>
            <nav class="top-nav">
                <div class="logo">VAULTLOGIC</div>
                <div class="nav-links">
                    <a href="#strategies">Strategies</a>
                    <a href="#about">About</a>
                    <a onclick="unlockPrompt()">Private Blog</a>
                    <button id="connectBtn" class="connect-btn" style="margin-left:20px;" onclick="connectWallet()">Connect Wallet</button>
                    <div id="walletDisplay" style="margin-left:20px;">
                        <span id="addrText" style="font-family:monospace; margin-right:15px; font-size:13px; color:#64748b;"></span>
                        <button class="stop-btn" onclick="disconnectWallet()">Stop Engine</button>
                    </div>
                </div>
            </nav>

            <div class="hero-section">
                <div class="status-badge">Institutional ALM v2.5.7 • Base Mainnet</div>
                <h1 style="font-size:48px; font-weight:800; color:#0f172a; margin:10px 0; letter-spacing:-1px;">Precision Wealth.</h1>
                <p style="color:#64748b; max-width:650px; margin:0 auto 30px; font-size:18px;">Automated Liquidity Management built with Engineering discipline for the next generation of Trust funds.</p>
            </div>
            
            <div id="strategies" class="container">{yield_cards}</div>

            <div id="console">
                <div class="console-header">
                    <span style="font-weight:700; font-size:13px; color:#1e293b;">Transaction & Strategy Audit</span>
                    <div style="display:flex; gap:10px;">
                        <button onclick="toggleReport()" class="download-link" style="border:none; cursor:pointer;">VIEW LIVE REPORT</button>
                        <a href="/download-logs" class="download-link">DOWNLOAD CSV</a>
                    </div>
                </div>
                <div id="log-stream"></div>
            </div>

            <section id="about" class="info-section">
                <h2 class="card-header">Engineered for Longevity</h2>
                <div class="blog-card">
                    <p>VaultLogic was founded by a Mechanical Engineer who saw a gap in the digital asset market: the lack of <strong>Industrial Discipline</strong>. In the physical world, engines require precise tolerances and automated governors to prevent failure. We apply those same principles to capital.</p>
                    <p>Our mission is to provide families and institutions with an "Autopilot" for their liquidity on the Base network, ensuring that capital is always working at peak efficiency while maintaining strict risk boundaries.</p>
                </div>
            </section>

            <section id="coinbase-blog" class="info-section">
                <h2 class="card-header">Partnership Insights</h2>
                
                <div id="privateOverlay">
                    <span class="lock-icon">🔒</span>
                    <p style="font-weight: 600; margin-bottom: 20px;">This section contains proprietary strategy insights.<br><small style="font-weight: 400; color: #64748b;">Authorized Personnel Only</small></p>
                    <input type="password" id="accessKey" class="pw-input" placeholder="Enter Access Key"><br>
                    <button onclick="checkKey()" class="connect-btn">Unlock Strategy Blog</button>
                </div>

                <div id="privateContent">
                    <div class="blog-card">
                        <h3 style="margin-top:0; color:#2563eb;">Why Base is the Choice for Institutional ALM</h3>
                        <p style="color:#64748b; font-size:14px;">Feb 22, 2026 • By Vaultlogic</p>
                        <p>For the Coinbase Asset Management team, the challenge has always been gas efficiency vs. rebalancing frequency. By building VaultLogic on Base, we can execute "Micro-Adjustments" to liquidity ranges that would be cost-prohibitive on Ethereum Mainnet.</p>
                        <p>Our ALM Kernel v2.5.7 is designed to integrate seamlessly with Coinbase Prime, allowing for automated "In-Range" maintenance of USDC positions, effectively turning idle treasury into a productive, fee-earning asset without the overhead of manual management.</p>
                    </div>
                </div>
            </section>

            <div id="reportModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1000; padding:50px;">
                <div style="background:white; max-width:800px; margin:0 auto; padding:40px; border-radius:12px; max-height:80vh; overflow-y:auto; text-align:left;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                        <h2 style="margin:0;">Audit Report</h2>
                        <button onclick="toggleReport()" style="cursor:pointer; background:none; border:none; font-size:20px;">&times;</button>
                    </div>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        <thead>
                            <tr style="border-bottom:2px solid #f1f5f9; text-align:left; color:#64748b;">
                                <th style="padding:12px;">Event Description</th>
                            </tr>
                        </thead>
                        <tbody id="reportTableBody"></tbody>
                    </table>
                </div>
            </div>

            <script>
                // Password for the Coinbase team is "cb-institutional"
                const SECRET_KEY = "cb-institutional";

                function checkKey() {{
                    const input = document.getElementById('accessKey').value;
                    if (input === SECRET_KEY) {{
                        document.getElementById('privateOverlay').style.display = 'none';
                        document.getElementById('privateContent').style.display = 'block';
                    }} else {{
                        alert("Invalid Access Key. Access Denied.");
                    }}
                }}

                function unlockPrompt() {{
                    document.getElementById('coinbase-blog').scrollIntoView();
                }}

                let activeAddress = null;
                function toggleReport() {{
                    const modal = document.getElementById('reportModal');
                    modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
                    if(modal.style.display === 'block') refreshReport();
                }}
                async function refreshReport() {{
                    const res = await fetch('/logs');
                    const data = await res.json();
                    const body = document.getElementById('reportTableBody');
                    body.innerHTML = data.logs.map(l => `<tr style="border-bottom:1px solid #f8fafc;"><td style="padding:12px;">${{l}}</td></tr>`).reverse().join('');
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
                    await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: "DISCONNECT" }})
                    }});
                }}
                async function deployFunds(btn, protocol) {{
                    if (!activeAddress) {{ alert("Security: Connect wallet to authorize."); return; }}
                    btn.innerText = "Authorizing...";
                    btn.style.background = "#64748b";
                    await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: "0x_INJECTION_" + protocol.replace(/ /g, "_") }})
                    }});
                    setTimeout(() => {{ btn.innerText = "Active"; btn.style.background = "#10b981"; }}, 2000);
                }}
                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div class="log-entry">${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 2000);
            </script>
        </body>
    </html>
    """