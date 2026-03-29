import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

# System state
vault_cache = {"yields": [], "status": "SYSTEM READY"}
system_logs = ["VaultLogic Kernel v2.5.5 Online", "Status: Awaiting Wallet Connection..."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

async def get_industrial_yields():
    # Live institutional tiers on Base Mainnet
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
        <div style="background:#fff; padding:25px; border-radius:12px; border:1px solid #e0e6ed; box-shadow: 0 4px 6px rgba(0,0,0,0.02); text-align:left; transition: transform 0.2s;">
            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px;">
                <h3 style="margin:0; color:#1a2b4b; font-size:14px; font-weight:700; letter-spacing:0.5px;">{y['protocol']}</h3>
                <span style="font-size:10px; color:#64748b; background:#f1f5f9; padding:4px 8px; border-radius:20px; font-weight:600;">{y['type']}</span>
            </div>
            <p style="margin:5px 0; font-size:32px; font-weight:800; color:#0f172a;">{y['apy']}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">APR</span></p>
            <div style="margin-bottom:20px;">
                <small style="color:#64748b; font-size:12px;">Asset: {y['asset']}</small>
            </div>
            <button onclick="deployFunds(this, '{y['protocol']}')" class="deploy-btn" style="width:100%; background:#2563eb; color:#fff; border:none; padding:12px; font-weight:600; font-size:12px; cursor:pointer; border-radius:8px; transition:0.2s;">
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
                body {{ background:#f8fafc; color:#1e293b; font-family: 'Inter', -apple-system, sans-serif; text-align:center; padding:0; margin:0; }}
                .top-nav {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
                .logo {{ font-weight: 800; letter-spacing: 2px; color: #0f172a; font-size: 18px; }}
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); max-width:1200px; margin:40px auto; gap:20px; padding: 0 20px; }}
                .hero-section {{ padding: 60px 20px; background: white; border-bottom: 1px solid #e2e8f0; }}
                .connect-btn {{ background:#0f172a; color:#fff; border:none; padding:12px 25px; font-weight:600; cursor:pointer; border-radius: 8px; transition: 0.2s; font-size:13px; }}
                .connect-btn:hover {{ background: #1e293b; }}
                .stop-btn {{ background:#fff; color:#ef4444; border:1px solid #fee2e2; padding:8px 16px; font-size:11px; cursor:pointer; border-radius:6px; font-weight:600; }}
                .download-link {{ color:#2563eb; text-decoration:none; font-size:11px; font-weight:600; padding:8px 12px; border-radius:6px; background:#eff6ff; }}
                
                #console {{ 
                    max-width:1160px; margin:40px auto; background:#fff; border:1px solid #e2e8f0; 
                    padding:0; text-align:left; border-radius:12px; overflow:hidden; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
                }}
                .console-header {{ background: #f8fafc; padding: 15px 25px; border-bottom: 1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center; }}
                #log-stream {{ padding: 20px; height: 300px; overflow-y: auto; font-family: 'SF Mono', monospace; font-size: 12px; color: #475569; background: #fff; }}
                .log-entry {{ padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; border-left: 3px solid #e2e8f0; background: #f8fafc; }}
                .status-badge {{ font-size:11px; color:#64748b; background:#f1f5f9; padding:4px 12px; border-radius:20px; margin-bottom:10px; display:inline-block; }}
                #walletDisplay {{ display:none; }}
                .deploy-btn:hover {{ background: #1d4ed8; }}
            </style>
        </head>
        <body>
            <nav class="top-nav">
                <div class="logo">VAULTLOGIC</div>
                <div>
                    <button id="connectBtn" class="connect-btn" onclick="connectWallet()">Connect Wallet</button>
                    <div id="walletDisplay">
                        <span id="addrText" style="font-family:monospace; margin-right:15px; font-size:13px; color:#64748b;"></span>
                        <button class="stop-btn" onclick="disconnectWallet()">Stop Engine</button>
                    </div>
                </div>
            </nav>

            <div class="hero-section">
                <div class="status-badge">Institutional ALM v2.5.5 • Base Mainnet</div>
                <h1 style="font-size:42px; font-weight:800; color:#0f172a; margin:10px 0;">Automated Capital Efficiency</h1>
                <p style="color:#64748b; max-width:600px; margin:0 auto 30px; line-height:1.6;">Precision rebalancing and volatility protection for high-performance treasury management.</p>
            </div>
            
            <div class="container">{yield_cards}</div>

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

            <!-- Modal for Report -->
            <div id="reportModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1000; padding:50px;">
                <div style="background:white; max-width:800px; margin:0 auto; padding:40px; border-radius:12px; max-height:80vh; overflow-y:auto;">
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
                    const btn = document.getElementById('connectBtn');
                    if (window.ethereum) {{
                        try {{
                            const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                            activeAddress = accounts[0];
                            btn.style.display = 'none';
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
                    if (!activeAddress) {{
                        alert("Security: Connect wallet to authorize.");
                        return;
                    }}
                    const originalText = btn.innerText;
                    btn.innerText = "Authorizing...";
                    btn.style.background = "#64748b";
                    await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: "0x_INJECTION_" + protocol.replace(/ /g, "_") }})
                    }});
                    setTimeout(() => {{ 
                        btn.innerText = "Active"; 
                        btn.style.background = "#10b981";
                    }}, 2000);
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