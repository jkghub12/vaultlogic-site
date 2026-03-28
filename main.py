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

# The source of truth for the UI
vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
    "wallet_balance": "0.000 ETH",
    "usdc_balance": "0.00 USDC",
    "wallet_address": None
}

class WalletConnect(BaseModel):
    address: str
    eth_balance: str = "0.000 ETH"
    usdc_balance: str = "0.00 USDC"

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        # Silently update the cache so the NEXT page load sees the data
        vault_cache["wallet_address"] = data.address
        vault_cache["wallet_balance"] = data.eth_balance
        vault_cache["usdc_balance"] = data.usdc_balance
        
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
            conn.commit()
            cur.close()
            conn.close()

        # Trigger the engine scout
        from engine import run_alm_engine 
        asyncio.create_task(run_alm_engine(data.address))
        
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def background_sync():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                vault_cache["yields"] = await get_all_yields()
                vault_cache["gas_price"] = "0.0012 Gwei (OPTIMAL)"
                vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
            except:
                vault_cache["last_updated"] = "SYNC ERROR"
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    # Dynamic Address Formatting
    addr = vault_cache["wallet_address"]
    display_addr = f"{addr[:6]}...{addr[-4:]}" if addr else "NOT CONNECTED"
    
    # Build the Yield Cards
    yield_cards = "".join([f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
            <small style="color: #666;">Asset: {y['asset']}</small>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .status-line {{ color: #00ffcc; font-family: monospace; font-size: 12px; margin: 20px 0; letter-spacing: 1px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
                w3m-button {{ margin-top: 20px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #666; font-size: 10px;">{vault_cache['last_updated']}</p>
                
                <div class="status-line">
                    ADDR: {display_addr} | ETH: {vault_cache['wallet_balance']} | USDC: {vault_cache['usdc_balance']}
                </div>

                <w3m-button></w3m-button>

                <div style="margin-top:25px;">
                    <a href="/strategy" style="color: #888; text-decoration: none; font-size: 11px; text-transform: uppercase; margin: 0 15px;">Strategy Brief</a>
                    <a href="/audit" style="color: #ff4444; text-decoration: none; font-size: 11px; text-transform: uppercase; margin: 0 15px;">Compliance Audit</a>
                </div>
            </div>

            <div class="container">{yield_cards}</div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, getBalance }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}'
                const config = defaultWagmiConfig({{ chains: [mainnet, base], projectId, metadata: {{ name: 'VaultLogic' }} }})
                createWeb3Modal({{ wagmiConfig: config, projectId, chains: [mainnet, base] }})

                let hasSynced = { "true" if addr else "false" };

                watchAccount(config, {{
                  async onChange(acc) {{
                    if (acc.isConnected && !hasSynced) {{
                      const ethB = await getBalance(config, {{ address: acc.address, chainId: base.id }});
                      
                      let usdcVal = "0.00 USDC";
                      try {{
                        const usdcB = await getBalance(config, {{ 
                            address: acc.address, 
                            chainId: base.id, 
                            token: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913' 
                        }});
                        usdcVal = usdcB.formatted.substring(0, 7) + " USDC";
                      }} catch(e) {{ console.log("USDC Scout Failed"); }}

                      const response = await fetch("/connect-wallet", {{ 
                        method: "POST", 
                        headers: {{ "Content-Type": "application/json" }}, 
                        body: JSON.stringify({{ 
                            address: acc.address,
                            eth_balance: ethB.formatted.substring(0, 6) + " ETH",
                            usdc_balance: usdcVal
                        }}) 
                      }});

                      if (response.ok) {{
                        hasSynced = true;
                        window.location.reload();
                      }}
                    }
                  }
                }})
            </script>
        </body>
    </html>
    """