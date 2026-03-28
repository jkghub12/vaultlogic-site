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

# Global State - Simplified for reliability
vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM NOMINAL",
    "gas_price": "0.0012 Gwei",
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
        # Update Cache immediately
        vault_cache["is_connected"] = True
        vault_cache["wallet_address"] = data.address
        vault_cache["wallet_balance"] = data.eth_balance
        
        # Database is secondary—don't let it crash the UI
        if DATABASE_URL:
            try:
                conn = psycopg2.connect(DATABASE_URL)
                cur = conn.cursor()
                cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as db_e:
                print(f"[DB ERROR] {db_e}")

        # Trigger ALM Engine
        asyncio.create_task(run_alm_engine(data.address))
        return {"status": "success"}
    except Exception as e:
        print(f"[POST ERROR] {e}")
        return {"status": "error"}

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    # Pre-render logic to prevent NoneType slicing
    is_conn = vault_cache.get("is_connected", False)
    addr = vault_cache.get("wallet_address")
    
    # Safe Address Slicing
    display_addr = f"{addr[:6]}...{addr[-4:]}" if (is_conn and addr) else "NOT CONNECTED"
    
    # Generate yields list safely
    yield_html = ""
    for y in vault_cache.get("yields", []):
        yield_html += f"""
        <div style="background:#111; padding:20px; margin:10px; border-radius:8px; border-left:4px solid #00ffcc; text-align:left;">
            <h3 style="margin:0; color:#00ffcc; font-size:12px;">{y.get('protocol', 'UNKNOWN')}</h3>
            <p style="margin:5px 0; font-size:24px; font-weight:bold;">{y.get('apy', '0.0')}% APY</p>
        </div>"""

    return f"""
    <html>
        <head>
            <title>VaultLogic | Command</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding:20px; }}
                .card {{ max-width:500px; margin:20px auto; padding:20px; border:1px solid #222; background:#050505; text-align:left; }}
                .row {{ display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #111; font-size:13px; }}
                .btn-box {{ display: {"none" if is_conn else "block"}; margin: 40px 0; }}
                .data-box {{ display: {"block" if is_conn else "none"}; }}
            </style>
        </head>
        <body>
            <h1 style="letter-spacing:10px; margin-top:40px;">VAULTLOGIC</h1>
            <p style="color:#00ffcc; font-size:10px;">{vault_cache['last_updated']}</p>

            <div class="btn-box"><w3m-button></w3m-button></div>

            <div class="card data-box">
                <div style="color:#00ffcc; font-size:10px; margin-bottom:15px;">> LIVE_SESSION_ACTIVE</div>
                <div class="row"><span>ADDRESS</span><span style="color:#666;">{display_addr}</span></div>
                <div class="row"><span>BASE ETH</span><span>{vault_cache['wallet_balance']}</span></div>
                <div class="row"><span>BASE USDC</span><span>{vault_cache['usdc_balance']}</span></div>
            </div>

            <div style="display:flex; flex-wrap:wrap; justify-content:center;">{yield_html}</div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, getBalance }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}'
                const chains = [mainnet, base]
                const config = defaultWagmiConfig({{ chains, projectId, metadata: {{ name: 'VaultLogic' }} }})
                createWeb3Modal({{ wagmiConfig: config, projectId, chains }})

                watchAccount(config, {{
                  async onChange(acc) {{
                    if (acc.isConnected) {{
                      let ethVal = "0.000 ETH";
                      try {{
                        const b = await getBalance(config, {{ address: acc.address, chainId: base.id }});
                        ethVal = b.formatted.substring(0,6) + " ETH";
                      }} catch(e) {{ console.error("Balance fetch pending..."); }}

                      await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ address: acc.address, eth_balance: ethVal }})
                      }});
                      window.location.reload();
                    }}
                  }}
                }})
            </script>
        </body>
    </html>
    """