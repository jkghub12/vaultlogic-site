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
    "wallet_balance": "0.000 ETH",
    "usdc_balance": "0.00 USDC",
    "engine_status": "OFFLINE",
    "wallet_address": None
}

class WalletConnect(BaseModel):
    address: str
    eth_balance: str = "0.000 ETH"
    usdc_balance: str = "0.00 USDC"

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        # Update cache with data from the frontend
        vault_cache["wallet_address"] = data.address
        vault_cache["wallet_balance"] = data.eth_balance
        vault_cache["usdc_balance"] = data.usdc_balance
        
        # --- DATABASE LOGGING ---
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
            conn.commit()
            cur.close()
            conn.close()

        # --- ENGINE TRIGGER ---
        from engine import run_alm_engine 
        asyncio.create_task(run_alm_engine(data.address))
        
        return {"status": "success", "engine": "activated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return f"""
    <html>
        <head>
            <title>VaultLogic | Strategy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: #ccc; font-family: 'Segoe UI', sans-serif; line-height: 1.8; padding: 60px 20px; }}
                .container {{ max-width: 850px; margin: 0 auto; border-left: 1px solid #222; padding-left: 40px; }}
                h1 {{ color: #00ffcc; letter-spacing: 4px; text-transform: uppercase; }}
                h2 {{ color: #eee; margin-top: 40px; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 10px; }}
                .highlight {{ color: #00ffcc; font-weight: bold; }}
                .back {{ color: #666; text-decoration: none; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; display: block; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back">← Return to Command Center</a>
                <h1>The Deterministic Vision</h1>
                <p>VaultLogic Dev LLC provides industrial-grade logic for complex systems.</p>
            </div>
        </body>
    </html>
    """

@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body{background:#0a0a0a;color:#eee;font-family:sans-serif;padding:50px 20px;text-align:center;}
                h1{color:#00ffcc;letter-spacing:2px;margin-bottom:30px;}
                .box{max-width:600px; margin:0 auto; padding:40px; border:1px solid #222; border-radius:12px; background:#111; text-align:center;}
            </style>
        </head>
        <body>
            <div class="box">
                <h1>2026 CLARITY ACT AUDIT</h1>
                <a href="/" style="display:block; margin-top:40px; color:#666; text-decoration:none;">← Return to Command Center</a>
            </div>
        </body>
    </html>
    """

async def background_sync():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                vault_cache["yields"] = await get_all_yields()
                vault_cache["gas_price"] = "0.0012 Gwei (OPTIMAL)"
                vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
            except Exception as e:
                vault_cache["last_updated"] = f"SYNC ERROR: {str(e)}"
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())
    asyncio.create_task(run_alm_engine("SYSTEM_DIAGNOSTIC", is_debug=True))

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = "".join([f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
        </div>""" for y in vault_cache["yields"]])

    addr = vault_cache["wallet_address"]
    display_addr = f"{addr[:6]}...{addr[-4:]}" if addr else "NOT CONNECTED"

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
                .balance-bar {{ color: #00ffcc; font-family: monospace; font-size: 12px; margin: 20px 0; letter-spacing: 1px; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px;">{vault_cache['last_updated']}</p>
                
                <div class="balance-bar">
                    ADDR: {display_addr} | ETH: {vault_cache['wallet_balance']} | USDC: {vault_cache['usdc_balance']}
                </div>

                <w3m-button></w3m-button>
            </div>

            <div class="container">{yield_cards}</div>

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
                      // Fetch ETH Balance
                      const ethB = await getBalance(config, {{ address: acc.address, chainId: base.id }});
                      
                      // Fetch USDC Balance (Base USDC Contract)
                      let usdcVal = "0.00 USDC";
                      try {{
                        const usdcB = await getBalance(config, {{ 
                            address: acc.address, 
                            chainId: base.id, 
                            token: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913' 
                        }});
                        usdcVal = usdcB.formatted.substring(0, 7) + " USDC";
                      }} catch(e) {{ console.log("USDC fetch skipped"); }}

                      await fetch("/connect-wallet", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ 
                            address: acc.address, 
                            eth_balance: ethB.formatted.substring(0, 6) + " ETH",
                            usdc_balance: usdcVal
                        }})
                      }});
                      window.location.reload();
                    }}
                  }}
                }})
            </script>
        </body>
    </html>
    """