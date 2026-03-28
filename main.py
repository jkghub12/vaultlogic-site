import asyncio
import os
import psycopg2
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields
from engine import run_alm_engine

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420' 

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
}

class WalletConnect(BaseModel):
    address: str

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
            conn.commit()
            cur.close()
            conn.close()
        
        from engine import run_alm_engine 
        asyncio.create_task(run_alm_engine(data.address))
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return """<html><body style="background:#0a0a0a;color:#ccc;padding:50px;"><h1>Strategy</h1><a href="/">Back</a></body></html>"""

@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return """<html><body style="background:#0a0a0a;color:#ccc;padding:50px;"><h1>Audit</h1><a href="/">Back</a></body></html>"""

async def background_sync():
    while True:
        try:
            vault_cache["yields"] = await get_all_yields()
            vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
        except:
            vault_cache["last_updated"] = "SYNC ERROR"
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = "".join([f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
            <small style="color: #666;">Asset: {y['asset']}</small>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; }}
                .nav-links a {{ color: #888; text-decoration: none; font-size: 11px; text-transform: uppercase; margin: 0 15px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px;">{vault_cache['last_updated']}</p>
                
                <div style="margin: 30px 0;">
                    <w3m-button></w3m-button>
                </div>

                <div class="nav-links">
                    <a href="/strategy">Strategy Brief</a>
                    <a href="/audit" style="color: #ff4444;">Compliance Audit</a>
                </div>
            </div>

            <div class="container">{yield_cards}</div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi@4.1.1'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}';
                const chains = [mainnet, base];
                
                // Fixed the configuration object to ensure it initializes correctly
                const config = defaultWagmiConfig({{ 
                    chains, 
                    projectId, 
                    metadata: {{ 
                        name: 'VaultLogic', 
                        url: 'https://vaultlogic.dev',
                        icons: ['https://avatars.githubusercontent.com/u/37784886']
                    }} 
                }});

                createWeb3Modal({{ wagmiConfig: config, projectId, chains, themeMode: 'dark' }});

                watchAccount(config, {{
                    onChange(acc) {{
                        if (acc.isConnected && acc.address) {{
                            fetch("/connect-wallet", {{ 
                                method: "POST", 
                                headers: {{ "Content-Type": "application/json" }}, 
                                body: JSON.stringify({{ address: acc.address }}) 
                            }});
                        }}
                    }}
                }});
            </script>
        </body>
    </html>
    """