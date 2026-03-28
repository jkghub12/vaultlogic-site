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

# The "Source of Truth"
vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
    "wallet_balance": "0.000 ETH",
    "usdc_balance": "0.00 USDC",
    "wallet_address": None,
    "is_connected": False
}

class WalletConnect(BaseModel):
    address: str
    eth_balance: str = "0.000 ETH"

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        vault_cache.update({
            "is_connected": True,
            "wallet_address": data.address,
            "wallet_balance": data.eth_balance
        })
        
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
            conn.commit()
            cur.close()
            conn.close()

        # Fire the ALM Engine in the background
        asyncio.create_task(run_alm_engine(data.address))
        return {"status": "success"}
    except Exception:
        return {"status": "silent_fail"}

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    is_conn = vault_cache.get("is_connected", False)
    raw_addr = vault_cache.get("wallet_address")
    
    # Safe rendering: no slicing if it's None
    display_addr = f"{raw_addr[:6]}...{raw_addr[-4:]}" if is_conn and raw_addr else "NOT CONNECTED"
    
    yield_cards = "".join([f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
        </div>""" for y in vault_cache.get("yields", [])])

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <style>
                body {{ background: #0a0a0a; color: white; font-family: monospace; text-align: center; padding: 40px; }}
                .balance-box {{ display: {"block" if is_conn else "none"}; max-width: 400px; margin: 20px auto; padding: 20px; border: 1px solid #222; background: #050505; text-align: left; }}
                .row {{ display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #111; padding: 5px; }}
            </style>
        </head>
        <body>
            <h1 style="letter-spacing: 10px;">VAULTLOGIC</h1>
            <p style="color: #00ffcc; font-size: 12px;">{vault_cache['last_updated']}</p>
            
            <div style="display: {"none" if is_conn else "block"};"><w3m-button></w3m-button></div>

            <div class="balance-box">
                <div class="row"><span>WALLET</span><span style="color:#666;">{display_addr}</span></div>
                <div class="row"><span>BASE ETH</span><span>{vault_cache['wallet_balance']}</span></div>
                <div class="row"><span>BASE USDC</span><span>{vault_cache['usdc_balance']}</span></div>
            </div>

            <div style="display: flex; flex-wrap: wrap; justify-content: center; margin-top: 30px;">{yield_cards}</div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, getBalance }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}'
                const config = defaultWagmiConfig({{ chains: [mainnet, base], projectId, metadata: {{ name: 'VaultLogic' }} }})
                createWeb3Modal({{ wagmiConfig: config, projectId, chains: [mainnet, base] }})

                watchAccount(config, {{
                  async onChange(acc) {{
                    if (acc.isConnected) {{
                      let bal = "0.000 ETH";
                      try {{
                         const res = await getBalance(config, {{ address: acc.address, chainId: base.id }});
                         bal = res.formatted.substring(0,6) + " ETH";
                      }} catch(e) {{ console.log("Balance fetch delayed"); }}

                      await fetch("/connect-wallet", {{ 
                        method: "POST", 
                        headers: {{ "Content-Type": "application/json" }}, 
                        body: JSON.stringify({{ address: acc.address, eth_balance: bal }}) 
                      }});
                      window.location.reload();
                    }}
                  }}
                }})
            </script>
        </body>
    </html>
    """