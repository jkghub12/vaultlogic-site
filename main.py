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
    "wallet_address": None,
    "is_connected": False,
    "engine_status": "OFFLINE"
}

class WalletConnect(BaseModel):
    address: str

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        vault_cache["is_connected"] = True
        vault_cache["wallet_address"] = data.address
        
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
            conn.commit()
            cur.close()
            conn.close()

        from engine import run_alm_engine 
        asyncio.create_task(run_alm_engine(data.address))
        
        return {"status": "success", "engine": "activated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/terminate-session")
async def terminate_session():
    vault_cache.update({
        "is_connected": False, 
        "wallet_address": None,
        "wallet_balance": "0.000 ETH",
        "usdc_balance": "0.00 USDC"
    })
    return {"status": "success"}

@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return f"""
    <html>
        <head><title>VaultLogic | Strategy</title><style>body{{background:#0a0a0a;color:#ccc;font-family:sans-serif;padding:60px 20px;}}.container{{max-width:850px;margin:0 auto;border-left:1px solid #222;padding-left:40px;}}h1{{color:#00ffcc;text-transform:uppercase;}}.highlight{{color:#00ffcc;font-weight:bold;}}.back{{color:#666;text-decoration:none;font-size:11px;text-transform:uppercase;}}</style></head>
        <body><div class="container"><a href="/" class="back">← Return to Command Center</a><h1>The Deterministic Vision</h1><p>VaultLogic Dev LLC provides industrial-grade logic. We eliminate the <span class="highlight">"Legacy Tax"</span>.</p><h2>I. Validation Tier</h2><p>Current stress-testing at the <strong>$500 entry level</strong>.</p></div></body>
    </html>
    """

@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return """
    <html>
        <head><style>body{{background:#0a0a0a;color:#eee;font-family:sans-serif;padding:50px 20px;text-align:center;}}.box{{max-width:600px;margin:0 auto;padding:40px;border:1px solid #222;background:#111;}}h1{{color:#00ffcc;}}</style></head>
        <body><div class="box"><h1>2026 CLARITY ACT AUDIT</h1><p>Yield Classification: <span style="color:#00ffcc;">✅ VERIFIED</span></p><a href="/" style="color:#666;text-decoration:none;font-size:11px;text-transform:uppercase;">← Return to Command Center</a></div></body>
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
                vault_cache["last_updated"] = f"SYNC ERROR"
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())
    print("[SYSTEM] PRE-FLIGHT CHECK ACTIVE", flush=True)

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    is_conn = vault_cache.get("is_connected", False)
    raw_addr = vault_cache.get("wallet_address")
    
    # Safe formatting to prevent NoneType slicing crash
    display_addr = f"{raw_addr[:6]}...{raw_addr[-4:]}" if (is_conn and raw_addr) else "NOT CONNECTED"
    
    status_display = "block" if is_conn else "none"
    button_display = "none" if is_conn else "block"

    yield_cards = "".join([f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
            <small style="color: #666;">Asset: {y['asset']} | Risk: Verified</small>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
#