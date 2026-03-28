import asyncio
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields
from engine import run_alm_engine

# 1. Initialize App
app = FastAPI()

# 2. Configuration & Cache
DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420'

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
    "wallet_balance": "0.000 ETH",
    "usdc_balance": "1.50 USDC",
    "engine_status": "OFFLINE",
    "is_connected": False
}

class WalletConnect(BaseModel):
    address: str

# 3. Helper Functions
async def fetch_wallet_balances(address: str):
    try:
        async with httpx.AsyncClient() as client:
            rpc_url = "https://mainnet.base.org"
            payload = {"jsonrpc":"2.0","method":"eth_getBalance","params":[address, "latest"],"id":1}
            resp = await client.post(rpc_url, json=payload)
            data = resp.json()
            if 'result' in data:
                hex_bal = data['result']
                eth_bal = int(hex_bal, 16) / 10**18
                vault_cache["wallet_balance"] = f"{eth_bal:.4f} ETH"
                vault_cache["engine_status"] = "SCOUTING ACTIVE"
                vault_cache["is_connected"] = True
    except Exception as e:
        print(f"BALANCE ERROR: {e}")

async def background_sync():
    while True:
        try:
            vault_cache["yields"] = await get_all_yields()
            vault_cache["gas_price"] = "0.0012 Gwei (OPTIMAL)"
            vault_cache["last_updated"] = f"ACTIVE: {len(vault_cache['yields'])} SOURCES NOMINAL"
        except Exception as e:
            vault_cache["last_updated"] = f"SYNC ERROR: {str(e)}"
        await asyncio.sleep(60)

# 4. Routes
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())
    print("[SYSTEM] PRE-FLIGHT CHECK: INITIALIZING VAULTLOGIC ENGINE...", flush=True)

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        asyncio.create_task(run_alm_engine(data.address))
        asyncio.create_task(fetch_wallet_balances(data.address))
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/terminate-session")
async def terminate_session():
    vault_cache["is_connected"] = False
    vault_cache["engine_status"] = "OFFLINE"
    vault_cache["wallet_balance"] = "0.000 ETH"
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = "".join([f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
            <small style="color: #666;">Asset: {y['asset']} | Risk: Verified</small>
        </div>""" for y in vault_cache["yields"]])

    is_connected_css = "display:none;" if vault_cache["is_connected"] else "display:inline-block;"
    
    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
                .gas-tag {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; }}
                #btn-container {{ margin-top: 20px; {is_connected_css} }}
                .term-btn {{ color:#ff4444; font-size:9px; text-transform:uppercase; text-decoration:none; letter-spacing:1px; margin-top:10px; display:{"block" if vault_cache["is_connected"] else "none"}; cursor:pointer; background:none; border:none; width:100%; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
                <div style="background: #050505; border: 1px solid #222; padding: 15px; margin: 20px auto; max-width: 400px; font-family: monospace; font-size: 12px; text-align: left; border-left: 3px solid #00ffcc; line-height: 1.6;">
                    <div style="color: #666;">> ENGINE_STATUS: <span style="color: #00ffcc;">{vault_cache.get('engine_status', 'OFFLINE')}</span></div>
                    <div style="color: #666;">> ASSET_ETH: <span style="color: #eee;">{vault_cache.get('wallet_balance', '0.000 ETH')}</span></div>
                </div>
                <div class="gas-tag">Network Fee (Base): {vault_cache['gas_price']}</div>
                <div id="btn-container"><w3m-button></w3m-button></div>
                <button class="term-btn" onclick="window.hardDisconnect()">[ TERMINATE SESSION ]</button>
            </div>
            <div class="container">{yield_cards}</div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, disconnect }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}'
                const chains = [mainnet, base]
                const wagmiConfig = defaultWagmiConfig({{ chains, projectId, metadata: {{ name: 'VaultLogic' }} }})
                const modal = createWeb3Modal({{ wagmiConfig, projectId, chains, themeMode: 'dark' }})

                window.hardDisconnect = async () => {{
                    console.log("VAULTLOGIC: FORCED TERMINATION INITIATED");
                    try {{
                        await disconnect(wagmiConfig);
                        localStorage.clear(); // Wipe the cache
                        await fetch("/terminate-session", {{ method: "POST" }});
                        window.location.href = "/"; // Force a full clean redirect
                    }} catch (e) {{ console.error(e); window.location.reload(); }}
                }}

                watchAccount(wagmiConfig, {{
                  onChange(account) {{
                    if (account.isConnected && account.address) {{
                      fetch("/connect-wallet", {{ 
                        method: "POST", 
                        headers: {{ "Content-Type": "application/json" }}, 
                        body: JSON.stringify({{ address: account.address }}) 
                      }}).then(r => {{ if(r.ok) setTimeout(() => window.location.reload(), 500); }});
                    }}
                  }}
                }})
            </script>
        </body>
    </html>
    """