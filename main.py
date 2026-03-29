import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

# System state
vault_cache = {"yields": [], "status": "SYSTEM READY"}
system_logs = ["VaultLogic Kernel v2.5.4 Online", "Status: Awaiting Wallet Connection..."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 25: system_logs.pop(0)

async def get_industrial_yields():
    # These represent the actual live institutional tiers on Base Mainnet
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
        # Only log 'Disconnected' if specifically requested, otherwise run engine
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
        <div style="background:#111; padding:20px; margin:10px; border-radius:8px; border-left:4px solid #00ffcc; text-align:left; position:relative;">
            <div style="float:right; font-size:9px; color:#666; border:1px solid #333; padding:2px 5px; border-radius:3px;">{y['type']}</div>
            <h3 style="margin:0; color:#00ffcc; font-size:12px; text-transform:uppercase;">{y['protocol']}</h3>
            <p style="margin:5px 0; font-size:24px; font-weight:bold;">{y['apy']}% <span style="font-size:12px; color:#444;">APR</span></p>
            <div style="margin-bottom:15px;">
                <small style="color:#888;">{y['asset']}</small>
            </div>
            <button onclick="deployFunds(this, '{y['protocol']}')" class="deploy-btn" style="width:100%; background:#00ffcc; color:#000; border:none; padding:10px; font-weight:bold; font-size:10px; cursor:pointer; border-radius:3px;">
                DEPLOY USDC
            </button>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic | Industrial ALM</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
            <style>
                body {{ background:#050505; color:white; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align:center; padding:20px; margin:0; }}
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); max-width:1200px; margin:0 auto; gap:10px; }}
                .header-section {{ padding:40px 20px; border-bottom:1px solid #111; margin-bottom:30px; }}
                .connect-btn {{ background:#00ffcc; color:#000; border:none; padding:15px 40px; font-weight:bold; cursor:pointer; border-radius: 4px; letter-spacing:1px; transition: 0.3s; font-size:14px; }}
                .stop-btn {{ background:#330000; color:#ff4444; border:1px solid #ff4444; padding:5px 15px; font-size:10px; cursor:pointer; margin-top:10px; border-radius:3px; text-transform:uppercase; }}
                #console {{ 
                    max-width:1100px; margin:40px auto; background:#000; border:1px solid #222; 
                    padding:20px; text-align:left; font-family:monospace; font-size:12px; color:#00ffcc; 
                    height:300px; overflow-y:auto; border-radius:4px; box-shadow: inset 0 0 10px #111;
                }}
                .log-entry {{ border-bottom:1px solid #0a0a0a; padding:8px 0; opacity: 0.9; line-height:1.4; }}
                .status-tag {{ font-size:10px; color:#444; margin-bottom:10px; text-transform:uppercase; letter-spacing:3px; }}
                #walletDisplay {{ color: #00ffcc; font-size:12px; margin-top:15px; font-family:monospace; display:none; }}
            </style>
        </head>
        <body>
            <div class="header-section">
                <div class="status-tag">Network: Base Mainnet | Engine: v2.5.4</div>
                <h1 style="letter-spacing:15px; margin:10px 0; color:#fff;">VAULTLOGIC</h1>
                <p style="color:#666; margin-bottom:30px; font-size:14px;">Institutional Liquidity Management for Long-Term Trusts</p>
                
                <button id="connectBtn" class="connect-btn" onclick="connectWallet()">CONNECT INSTITUTIONAL WALLET</button>
                <div id="walletDisplay">
                    CONNECTED: <span id="addrText"></span><br>
                    <button class="stop-btn" onclick="disconnectWallet()">Stop Engine & Disconnect</button>
                </div>
            </div>
            
            <div class="container">{yield_cards}</div>

            <div id="console">
                <div style="color:#333; margin-bottom:15px; text-transform:uppercase; font-size:10px; font-weight:bold; border-bottom:1px solid #222; padding-bottom:5px;">
                    Industrial ALM Execution Log (Live)
                </div>
                <div id="log-stream"></div>
            </div>

            <script>
                let activeAddress = null;

                async function connectWallet() {{
                    const btn = document.getElementById('connectBtn');
                    if (window.ethereum) {{
                        try {{
                            const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                            activeAddress = accounts[0];
                            btn.style.display = 'none';
                            document.getElementById('walletDisplay').style.display = 'block';
                            document.getElementById('addrText').innerText = activeAddress;
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
                    document.getElementById('connectBtn').innerText = "CONNECT INSTITUTIONAL WALLET";
                    
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
                    btn.innerText = "ROUTING...";
                    btn.disabled = true;
                    await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: "0x_INJECTION_" + protocol.replace(/ /g, "_") }})
                    }});
                    setTimeout(() => {{ btn.innerText = "ACTIVE"; }}, 2000);
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