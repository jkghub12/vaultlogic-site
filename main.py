import asyncio
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields
from engine import run_alm_engine

app = FastAPI()

# 1. Hardware-Level State
vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
    "wallet_balance": "0.000 ETH",
    "engine_status": "OFFLINE",
    "is_connected": False
}

class WalletConnect(BaseModel):
    address: str

# 2. Logic Layer
async def fetch_wallet_balances(address: str):
    try:
        async with httpx.AsyncClient() as client:
            rpc_url = "https://mainnet.base.org"
            payload = {"jsonrpc":"2.0","method":"eth_getBalance","params":[address, "latest"],"id":1}
            resp = await client.post(rpc_url, json=payload)
            data = resp.json()
            if 'result' in data:
                vault_cache["wallet_balance"] = f"{int(data['result'], 16) / 10**18:.4f} ETH"
                vault_cache["engine_status"] = "SCOUTING ACTIVE"
                vault_cache["is_connected"] = True
    except Exception as e:
        print(f"DIAGNOSTIC: Balance fetch failed -> {e}")

async def background_sync():
    while True:
        try:
            vault_cache["yields"] = await get_all_yields()
            vault_cache["gas_price"] = "0.0012 Gwei (OPTIMAL)"
            vault_cache["last_updated"] = f"ACTIVE: {len(vault_cache['yields'])} SOURCES"
        except: pass
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    asyncio.create_task(run_alm_engine(data.address))
    asyncio.create_task(fetch_wallet_balances(data.address))
    return {"status": "success"}

@app.post("/terminate-session")
async def terminate_session():
    vault_cache.update({"is_connected": False, "engine_status": "OFFLINE", "wallet_balance": "0.000 ETH"})
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = "".join([f"""
        <div style="background:#111; padding:20px; margin:10px; border-radius:8px; border-left:4px solid #00ffcc; text-align:left;">
            <h3 style="margin:0; color:#00ffcc; font-size:12px;">{y['protocol']}</h3>
            <p style="margin:5px 0; font-size:24px; font-weight:bold;">{y['apy']}%</p>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic Command</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding:40px 20px; }}
                .status-box {{ background:#050505; border:1px solid #222; padding:15px; margin:20px auto; max-width:400px; border-left:3px solid #00ffcc; text-align:left; }}
                .reset-btn {{ color:#444; font-size:10px; text-decoration:none; display:block; margin-top:40px; cursor:pointer; text-transform:uppercase; letter-spacing:1px; }}
            </style>
        </head>
        <body>
            <h1 style="letter-spacing:10px;">VAULTLOGIC</h1>
            <p style="color:#00ffcc; font-size:10px;">{vault_cache['last_updated']}</p>
            
            <div class="status-box">
                <div>> ENGINE: <span style="color:#00ffcc;">{vault_cache['engine_status']}</span></div>
                <div>> BALANCE: <span style="color:#eee;">{vault_cache['wallet_balance']}</span></div>
            </div>

            <div id="w3m-slot" style="margin-top:20px;"><w3m-button></w3m-button></div>
            
            <a onclick="window.hardReset()" class="reset-btn">[ RESET CACHE & DISCONNECT ]</a>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); max-width:1000px; margin:40px auto;">{yield_cards}</div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, disconnect }} from 'https://esm.sh/@wagmi/core'

                const projectId = '2b936cf692d84ae6da1ba91950c96420'
                const config = defaultWagmiConfig({{ chains: [mainnet, base], projectId, metadata: {{ name: 'VaultLogic' }} }})
                
                // Force theme variables to fix Black Font visibility
                createWeb3Modal({{ 
                    wagmiConfig: config, projectId, chains: [mainnet, base], themeMode: 'dark',
                    themeVariables: {{ '--w3m-accent': '#00ffcc', '--w3m-color-mix': '#fff', '--w3m-color-mix-strength': 20 }}
                }})

                window.hardReset = async () => {{
                    console.log("VAULTLOGIC: EXECUTING HARD RESET");
                    try {{ await disconnect(config); }} catch (e) {{}}
                    ['wagmi.store', 'wagmi.connected', 'wagmi.account', 'wagmi.recentConnectorId'].forEach(k => localStorage.removeItem(k));
                    await fetch("/terminate-session", {{ method: "POST" }});
                    window.location.reload();
                }}

                // Diagnostic: If stuck "Connecting" for 2s, auto-reset
                setTimeout(() => {{
                    const b = document.querySelector('w3m-button');
                    if(b && b.shadowRoot && b.shadowRoot.textContent.includes('Connecting')) window.hardReset();
                }}, 2000);

                watchAccount(config, {{
                  onChange(acc) {{
                    if (acc.isConnected && acc.address) {{
                      fetch("/connect-wallet", {{ 
                        method: "POST", 
                        headers: {{ "Content-Type": "application/json" }}, 
                        body: JSON.stringify({{ address: acc.address }}) 
                      }}).then(r => {{ if(r.ok) setTimeout(() => window.location.reload(), 500); }});
                    }}
                  }}
                }})
            </script>
        </body>
    </html>
    """