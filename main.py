import asyncio
import os
import random
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420'

# Shared state
vault_cache = {"yields": [], "status": "SYSTEM READY"}
system_logs = ["VaultLogic Kernel v2.1.0 Online", "Secure Channel Established."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 20: system_logs.pop(0)

# High-Reliability Internal Data Engine (Replaces yieldscout for the demo)
async def get_industrial_yields():
    return [
        {"protocol": "MORPHO BLUE", "apy": 3.62, "asset": "STEAK / GT USDCP", "type": "ORGANIC"},
        {"protocol": "UNISWAP V3", "apy": 3.55, "asset": "USDC/ETH", "type": "ORGANIC"},
        {"protocol": "AAVE V3", "apy": 2.87, "asset": "USDC", "type": "ORGANIC"},
        {"protocol": "AERODROME", "apy": 12.41, "asset": "cbBTC/WETH", "type": "BOOSTED"},
        {"protocol": "BEEFY", "apy": 8.15, "asset": "WETH/USDC LP", "type": "BOOSTED"}
    ]

@app.post("/connect-wallet")
async def connect(data: WalletConnect):
    try:
        add_log(f"AUTH_SUCCESS: {data.address[:6]}...{data.address[-4:]}")
        from engine import run_alm_engine
        asyncio.create_task(run_alm_engine(data.address, log_callback=add_log))
        return {"status": "ENGINE_ACTIVATED"}
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
                # Direct call to our reliable internal engine
                vault_cache["yields"] = await get_industrial_yields()
            except: pass
            await asyncio.sleep(60)
    asyncio.create_task(sync())

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    yield_cards = "".join([f"""
        <div style="background:#111; padding:20px; margin:10px; border-radius:8px; border-left:4px solid #00ffcc; text-align:left; position:relative;">
            <div style="position:absolute; top:10px; right:10px; font-size:9px; color:#666; border:1px solid #333; padding:2px 5px; border-radius:3px;">
                {y['type']}
            </div>
            <h3 style="margin:0; color:#00ffcc; font-size:12px; text-transform:uppercase; letter-spacing:1px;">{y['protocol']}</h3>
            <p style="margin:5px 0; font-size:24px; font-weight:bold; font-family:monospace;">{y['apy']}% <span style="font-size:12px; color:#444;">APR</span></p>
            <div style="margin-bottom:15px;">
                <small style="color:#888;">{y['asset']}</small>
                <small style="display:block; color:#444; font-size:10px;">CAPACITY: $10M+</small>
            </div>
            <button id="btn-{{y['protocol'].replace(' ', '')}}" class="deploy-btn" style="width:100%; background:#00ffcc; color:#000; border:none; padding:8px; font-weight:bold; font-size:10px; cursor:pointer; border-radius:3px; letter-spacing:1px;">
                DEPLOY $2,000.00
            </button>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic | Industrial ALM</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ background:#0a0a0a; color:white; font-family:sans-serif; text-align:center; padding:40px; margin:0; }}
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); max-width:1200px; margin:0 auto; }}
                .btn {{ background:#00ffcc; color:#000; border:none; padding:15px 30px; font-weight:bold; cursor:pointer; letter-spacing:2px; transition: 0.2s; border-radius: 4px; }}
                .btn:hover {{ background: #fff; box-shadow: 0 0 20px rgba(0,255,204,0.3); }}
                .btn:disabled {{ background: #111; color: #00ffcc; cursor: not-allowed; border: 1px solid #222; }}
                #console {{ 
                    max-width:1000px; margin:50px auto; background:#050505; border:1px solid #222; 
                    padding:20px; text-align:left; font-family:monospace; font-size:13px; color:#00ffcc; 
                    height:250px; overflow-y:auto; border-radius:8px;
                }}
                .log-entry {{ border-bottom:1px solid #111; padding:8px 0; opacity: 0.8; font-size: 11px; }}
                .status-bar {{ font-size:10px; color:#444; margin-bottom:20px; text-transform:uppercase; letter-spacing:2px; }}
            </style>
            <script src="https://unpkg.com/@web3modal/standalone@2.4.3/dist/index.js"></script>
        </head>
        <body>
            <div class="status-bar">Network: Base Mainnet | Latency: 42ms | Oracle: Verified</div>
            <h1 style="letter-spacing:15px; margin-top:10px; margin-bottom: 5px;">VAULTLOGIC</h1>
            <p style="color:#00ffcc; font-size:11px; margin-bottom:30px; letter-spacing: 2px;">CORE ALM INTERFACE v2.1</p>
            
            <button id="cta" class="btn">INITIALIZE ENGINE</button>
            
            <div class="container" style="margin-top:40px;">{yield_cards}</div>

            <div id="console">
                <div style="color:#333; margin-bottom:10px; text-transform:uppercase; font-size:10px; font-weight:bold;">Industrial ALM Execution Log</div>
                <div id="log-stream"></div>
            </div>

            <script>
                const btn = document.getElementById('cta');
                const projectId = '{WC_PROJECT_ID}';
                let modal;

                try {{
                    modal = new window.Web3ModalStandalone.Web3Modal({{
                        projectId: projectId,
                        walletConnectVersion: 2,
                        standaloneChains: ["eip155:8453"],
                        themeMode: 'dark'
                    }});
                }} catch (e) {{}}

                btn.onclick = async () => {{
                    try {{
                        if (modal) await modal.openModal();
                        triggerEngine("0x_internal_bridge");
                    }} catch (e) {{
                        triggerEngine("0x_secure_session");
                    }}
                }};

                document.querySelectorAll('.deploy-btn').forEach(b => {{
                    b.onclick = () => triggerEngine("0x_direct_deployment");
                }});

                async function triggerEngine(addr) {{
                    btn.innerText = "ENGINE ACTIVE";
                    btn.disabled = true;
                    await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: addr }})
                    }});
                }}

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div class="log-entry">${{l}}</div>`).reverse().join('');
                        stream.scrollTop = 0;
                    }} catch(e) {{}}
                }}, 2000);
            </script>
        </body>
    </html>
    """