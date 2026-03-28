import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields

app = FastAPI()
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420'
DATABASE_URL = os.getenv("DATABASE_URL")

# Shared state for the dashboard
vault_cache = {"yields": [], "status": "ACTIVE: SYSTEM NOMINAL"}
system_logs = ["VaultLogic Kernel Initialized...", "Awaiting Wallet Connection..."]

class WalletConnect(BaseModel):
    address: str

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 15: system_logs.pop(0)

@app.post("/connect-wallet")
async def connect(data: WalletConnect):
    try:
        if DATABASE_URL:
            try:
                conn = psycopg2.connect(DATABASE_URL)
                cur = conn.cursor()
                cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                add_log(f"DB Log Skip: {str(e)}")
        
        add_log(f"Authenticated: {data.address[:6]}...{data.address[-4:]}")
        from engine import run_alm_engine
        asyncio.create_task(run_alm_engine(data.address, log_callback=add_log))
        return {"status": "ENGINE_ACTIVE"}
    except Exception as e:
        add_log(f"Kernel Error: {str(e)}")
        return {"status": "error", "message": str(e)}

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
                .btn:hover {{ background: #fff; box-shadow: 0 0 20px rgba(0,255,204,0.3); }}
                #console {{ 
                    max-width:1000px; margin:50px auto; background:#050505; border:1px solid #222; 
                    padding:20px; text-align:left; font-family:monospace; font-size:12px; color:#666; 
                    height:180px; overflow-y:auto; border-radius:8px;
                }}
                .log-entry {{ border-bottom:1px solid #111; padding:5px 0; }}
            </style>
        </head>
        <body>
            <h1 style="letter-spacing:15px; margin-bottom: 5px;">VAULTLOGIC</h1>
            <p style="color:#00ffcc; font-size:11px; margin-bottom:30px; letter-spacing: 2px;">{vault_cache['status']}</p>
            
            <button id="cta" class="btn">INITIALIZE ENGINE</button>
            
            <div class="container" style="margin-top:40px;">{yield_cards}</div>

            <div id="console">
                <div style="color:#333; margin-bottom:10px; text-transform:uppercase; font-size:10px; font-weight:bold;">Industrial ALM Kernel Log</div>
                <div id="log-stream"></div>
            </div>

            <script type="module">
                // FINAL ARCHITECTURE: Single-entry bundle to eliminate "export not found" errors
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi@4.2.0?bundle'
                import * as ViemChains from 'https://esm.sh/viem/chains'
                import * as WagmiCore from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}';
                const metadata = {{
                    name: 'VaultLogic',
                    description: 'Industrial DeFi Strategy',
                    url: window.location.origin,
                    icons: ['https://avatars.githubusercontent.com/u/37784886']
                }};

                const chains = [ViemChains.mainnet, ViemChains.base];
                const config = defaultWagmiConfig({{ chains, projectId, metadata }});
                const modal = createWeb3Modal({{ 
                    wagmiConfig: config, 
                    projectId, 
                    enableAnalytics: false,
                    themeMode: 'dark' 
                }});

                window.vaultModal = modal;
                WagmiCore.reconnect(config);

                WagmiCore.watchAccount(config, {{
                    onChange(acc) {{
                        if (acc.isConnected && acc.address) {{
                            const btn = document.getElementById('cta');
                            btn.innerText = "ENGINE ACTIVE";
                            btn.style.background = "#111";
                            btn.style.color = "#00ffcc";
                            
                            fetch("/connect-wallet", {{ 
                                method: "POST", 
                                headers: {{ "Content-Type": "application/json" }}, 
                                body: JSON.stringify({{ address: acc.address }}) 
                            }});
                        }}
                    }}
                }});

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div class="log-entry">${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 2000);
            </script>

            <script>
                // Direct interaction layer
                document.getElementById('cta').onclick = function() {{
                    if (window.vaultModal) {{
                        window.vaultModal.open();
                    }} else {{
                        console.log("VaultLogic: Kernel initializing...");
                    }}
                }};
            </script>
        </body>
    </html>
    """