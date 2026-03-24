import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    from yieldscout import get_all_yields
except ImportError:
    def get_all_yields(): return []

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")

vault_cache = {
    "yields": [],
    "last_updated": "INITIALIZING SCAN..."
}

class WalletConnect(BaseModel):
    address: str

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def background_sync():
    while True:
        try:
            data = get_all_yields()
            if data:
                vault_cache["yields"] = data
                vault_cache["last_updated"] = "SYSTEM ONLINE | LIVE MARKET DATA"
        except Exception:
            pass
        await asyncio.sleep(300) # Refresh every 5 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())

# --- NAVIGATION ROUTES ---
@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return """<html><head><style>body{background:#0a0a0a;color:#ccc;font-family:sans-serif;padding:50px;line-height:1.6;}h1{color:#00ffcc;}</style></head>
    <body><h1>VaultLogic Strategy</h1><p>Deterministic yield optimization for the 2026 regulatory environment.</p><a href="/" style="color:#00ffcc;">← RETURN</a></body></html>"""

@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return """<html><head><style>body{background:#0a0a0a;color:#eee;font-family:sans-serif;padding:50px;text-align:center;}h1{color:#ff4444;}</style></head>
    <body><h1>2026 CLARITY ACT AUDIT</h1><p>Scanning connected wallets for non-compliant interest structures...</p><a href="/" style="color:#666;">← RETURN</a></body></html>"""

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = ""
    for y in vault_cache["yields"]:
        yield_cards += f"""
        <div style="background:#111;padding:20px;margin:10px;border-radius:8px;border-left:4px solid #00ffcc;text-align:left;">
            <h3 style="margin:0;color:#00ffcc;font-size:12px;text-transform:uppercase;">{y['protocol']}</h3>
            <p style="margin:5px 0;font-size:24px;font-weight:bold;">{y['apy']}%</p>
            <small style="color:#666;">{y['asset']} | BASE NETWORK</small>
        </div>"""

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .sync-btn {{ background: #00ffcc; color: #000; padding: 18px 40px; border-radius: 5px; font-weight: bold; cursor: pointer; border: none; width: 100%; max-width: 320px; }}
                .nav {{ margin: 20px 0; }} .nav a {{ color: #666; text-decoration: none; margin: 0 15px; font-size: 12px; text-transform: uppercase; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); max-width: 1000px; margin: 40px auto; }}
            </style>
        </head>
        <body>
            <h1 style="letter-spacing:10px;">VAULTLOGIC</h1>
            <p style="color:#444; font-size:10px;">{vault_cache['last_updated']}</p>
            <div class="nav"><a href="/audit" style="color:#ff4444;">Compliance Audit</a><a href="/strategy">Strategy Brief</a></div>
            <button id="sync-button" class="sync-btn" onclick="syncWallet()">Sync Multi-Wallet (UHNW)</button>
            <div class="grid">{yield_cards}</div>
            <script>
                async function syncWallet() {{
                    const btn = document.getElementById('sync-button');
                    if (!window.ethereum) return alert("Wallet not detected.");
                    const provider = new ethers.providers.Web3Provider(window.ethereum);
                    await provider.send("eth_requestAccounts", []);
                    const address = await provider.getSigner().getAddress();
                    btn.innerText = "CONNECTED: " + address.substring(0,6);
                    await fetch("/connect-wallet", {{ method: "POST", headers: {{"Content-Type":"application/json"}}, body: JSON.stringify({{address:address}}) }});
                }}
            </script>
        </body>
    </html>
    """