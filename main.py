import asyncio
import os
import psycopg2
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420' 

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "0.0012 Gwei (OPTIMAL)",
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
        # Engine trigger can go here
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    # PRE-RENDER Yield Cards to avoid f-string nesting issues
    yield_html = ""
    for y in vault_cache["yields"]:
        yield_html += f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
            <small style="color: #666;">Asset: {y['asset']}</small>
        </div>"""

    # THE MAIN TEMPLATE: Note the doubled {{ }} for JavaScript
    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
                .stat-box {{ background: #050505; border: 1px solid #222; padding: 15px; margin: 10px auto; max-width: 400px; display: flex; justify-content: space-between; font-family: monospace; font-size: 12px; }}
                .stat-val {{ color: #00ffcc; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
                
                <div class="stat-box"><span>BASE ETH:</span> <span id="eth-bal" class="stat-val">0.0000</span></div>
                <div class="stat-box"><span>BASE USDC:</span> <span id="usdc-bal" class="stat-val">0.00</span></div>

                <w3m-button></w3m-button>
            </div>

            <div class="container">
                {yield_html}
            </div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi@4.1.1'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, getBalance }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}';
                const chains = [mainnet, base];
                const config = defaultWagmiConfig({{ 
                    chains, 
                    projectId, 
                    metadata: {{ name: 'VaultLogic', url: 'https://vaultlogic.dev' }} 
                }});
                
                createWeb3Modal({{ wagmiConfig: config, projectId, chains, themeMode: 'dark' }});

                watchAccount(config, {{
                    async onChange(acc) {{
                        const ethEl = document.getElementById('eth-bal');
                        const usdcEl = document.getElementById('usdc-bal');

                        if (acc.isConnected && acc.address) {{
                            try {{
                                const ethRes = await getBalance(config, {{ address: acc.address, chainId: base.id }});
                                ethEl.innerText = parseFloat(ethRes.formatted).toFixed(4) + " ETH";

                                const usdcRes = await getBalance(config, {{ 
                                    address: acc.address, 
                                    chainId: base.id, 
                                    token: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913' 
                                }});
                                usdcEl.innerText = parseFloat(usdcRes.formatted).toFixed(2) + " USDC";

                                fetch("/connect-wallet", {{ 
                                    method: "POST", 
                                    headers: {{ "Content-Type": "application/json" }}, 
                                    body: JSON.stringify({{ address: acc.address }}) 
                                }});
                            }} catch (e) {{ console.error(e); }}
                        }}
                    }}
                }});
            </script>
        </body>
    </html>
    """