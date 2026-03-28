import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields

app = FastAPI()
# Institutional Project ID for VaultLogic
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420'
DATABASE_URL = os.getenv("DATABASE_URL")

# Shared state for the dashboard
vault_cache = {"yields": [], "status": "SYSTEM READY: AWAITING AUTH"}
system_logs = ["VaultLogic Kernel v2.1.0 Online", "Secure Channel Established."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 20: system_logs.pop(0)

@app.post("/connect-wallet")
async def connect(data: WalletConnect):
    try:
        add_log(f"AUTH_SUCCESS: {data.address[:6]}...{data.address[-4:]}")
        # Trigger the Engine Logic immediately upon connection
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
                vault_cache["yields"] = await get_all_yields()
            except: pass
            await asyncio.sleep(60)
    asyncio.create_task(sync())

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    yield_cards = "".join([f"""
        <div style="background:#111; padding:20px; margin:10px; border-radius:8px; border-left:4px solid #00ffcc; text-align:left;">
            <h3 style="margin:0; color:#00ffcc; font-size:12px; text-transform:uppercase;">{y['protocol']}</h3>
            <p style="margin:5px 0; font-size:24px; font-weight:bold;">{y['apy']}% APY</p>
            <small style="color:#666;">{y['asset']} | Industrial Grade</small>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic | Industrial ALM</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background:#0a0a0a; color:white; font-family:sans-serif; text-align:center; padding:40px; margin:0; }}
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); max-width:1100px; margin:0 auto; }}
                .btn {{ background:#00ffcc; color:#000; border:none; padding:15px 30px; font-weight:bold; cursor:pointer; letter-spacing:2px; transition: 0.2s; border-radius: 4px; }}
                .btn:disabled {{ background: #222; color: #444; cursor: not-allowed; }}
                #console {{ 
                    max-width:1000px; margin:50px auto; background:#050505; border:1px solid #222; 
                    padding:20px; text-align:left; font-family:monospace; font-size:13px; color:#00ffcc; 
                    height:250px; overflow-y:auto; border-radius:8px; box-shadow: 0 0 20px rgba(0,255,204,0.05);
                }}
                .log-entry {{ border-bottom:1px solid #111; padding:8px 0; opacity: 0.8; font-size: 11px; }}
                .log-entry:first-child {{ opacity: 1; font-weight: bold; color: white; }}
            </style>
        </head>
        <body>
            <h1 style="letter-spacing:15px; margin-top:40px; margin-bottom: 5px;">VAULTLOGIC</h1>
            <p style="color:#00ffcc; font-size:11px; margin-bottom:30px; letter-spacing: 2px;">CORE ALM INTERFACE</p>
            
            <button id="cta" class="btn" disabled>LOADING KERNEL...</button>
            
            <div class="container" style="margin-top:40px;">{yield_cards}</div>

            <div id="console">
                <div style="color:#333; margin-bottom:10px; text-transform:uppercase; font-size:10px; font-weight:bold;">Industrial ALM Execution Log</div>
                <div id="log-stream"></div>
            </div>

            <script type="module">
                console.log("VaultLogic: Initializing Web3 Bridge...");
                
                // Optimized Bundle Imports
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi@4.1.1?bundle'
                import * as ViemChains from 'https://esm.sh/viem/chains?bundle'
                import * as WagmiCore from 'https://esm.sh/@wagmi/core?bundle'

                const projectId = '{WC_PROJECT_ID}';
                const metadata = {{
                    name: 'VaultLogic',
                    description: 'Industrial ALM',
                    url: window.location.origin,
                    icons: ['https://avatars.githubusercontent.com/u/37784886']
                }};

                const chains = [ViemChains.mainnet, ViemChains.base];
                const config = defaultWagmiConfig({{ chains, projectId, metadata }});
                
                try {{
                    const modal = createWeb3Modal({{ wagmiConfig: config, projectId, chains, themeMode: 'dark' }});
                    
                    const btn = document.getElementById('cta');
                    btn.innerText = "INITIALIZE ENGINE";
                    btn.disabled = false;
                    
                    btn.onclick = () => {{
                        console.log("VaultLogic: Opening Wallet Selector...");
                        modal.open();
                    }};
                    
                    WagmiCore.reconnect(config);
                }} catch (err) {{
                    console.error("VaultLogic Bridge Error:", err);
                }}

                // Listen for Connection to Trigger Backend Engine
                WagmiCore.watchAccount(config, {{
                    onChange(acc) {{
                        if (acc.isConnected && acc.address) {{
                            console.log("VaultLogic: Wallet Connected:", acc.address);
                            document.getElementById('cta').innerText = "ENGINE ACTIVE";
                            document.getElementById('cta').style.background = "#111";
                            document.getElementById('cta').style.color = "#00ffcc";
                            
                            fetch("/connect-wallet", {{ 
                                method: "POST", 
                                headers: {{ "Content-Type": "application/json" }}, 
                                body: JSON.stringify({{ address: acc.address }}) 
                            }});
                        }}
                    }}
                }});

                // Poll Logs for Visual Feedback
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