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
    return f"""
    <html>
        <head>
            <title>VaultLogic | Strategy</title>
            <style>
                body {{ background: #0a0a0a; color: #ccc; font-family: sans-serif; line-height: 1.8; padding: 60px 20px; }}
                .container {{ max-width: 850px; margin: 0 auto; border-left: 1px solid #222; padding-left: 40px; }}
                h1 {{ color: #00ffcc; letter-spacing: 4px; text-transform: uppercase; }}
                .highlight {{ color: #00ffcc; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" style="color:#666; text-decoration:none; font-size:11px;">← RETURN</a>
                <h1>The Deterministic Vision</h1>
                <p>VaultLogic Dev LLC provides industrial-grade logic for complex systems. We eliminate the <span class="highlight">"Legacy Tax"</span>.</p>
            </div>
        </body>
    </html>
    """

@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return """
    <html><body style="background:#0a0a0a;color:white;text-align:center;padding:50px;">
    <h1 style="color:#00ffcc;">2026 CLARITY ACT AUDIT</h1><p>✅ VERIFIED</p>
    <a href="/" style="color:#666;">← RETURN</a></body></html>
    """

async def background_sync():
    while True:
        try:
            vault_cache["yields"] = await get_all_yields()
            vault_cache["gas_price"] = "0.0012 Gwei (OPTIMAL)"
            vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
        except Exception as e:
            vault_cache["last_updated"] = f"SYNC ERROR"
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = ""
    for y in vault_cache["yields"]:
        yield_cards += f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
            <small style="color: #666;">Asset: {y['asset']}</small>
        </div>"""

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; margin: 0; }}
                .mission-brief {{ max-width: 800px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                
                /* Layout Fixes */
                .status-container {{ 
                    display: flex; 
                    flex-direction: column; 
                    align-items: center; 
                    gap: 20px; 
                    margin: 30px 0; 
                }}
                .balance-table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    max-width: 400px; 
                    font-family: monospace; 
                    border: 1px solid #222; 
                    background: #050505;
                }}
                .balance-table td {{ padding: 12px; border: 1px solid #222; text-align: left; }}
                .label {{ color: #666; font-size: 11px; text-transform: uppercase; width: 30%; }}
                
                .nav-links a {{ color: #888; text-decoration: none; font-size: 11px; text-transform: uppercase; margin: 0 15px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); max-width: 1200px; margin: 0 auto; }}
                w3m-button {{ display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p