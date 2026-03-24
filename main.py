import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# --- IMPORTING YOUR YIELDSCOUT LOGIC ---
try:
    from yieldscout import get_all_yields
except ImportError:
    def get_all_yields(): return [{"protocol": "System", "apy": "0.00", "asset": "N/A"}]

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

vault_cache = {
    "yields": [],
    "last_updated": "INITIALIZING..."
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

# --- BACKGROUND DATA REFRESH (CRASH PROTECTED) ---
async def background_sync():
    while True:
        try:
            data = get_all_yields()
            if isinstance(data, list):
                vault_cache["yields"] = [y for y in data if isinstance(y, dict)]
            elif isinstance(data, dict):
                vault_cache["yields"] = [data]
            else:
                vault_cache["yields"] = []
            vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
        except Exception as e:
            vault_cache["last_updated"] = f"SYNC ERROR: {str(e)}"
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())

# --- PAGES ---
@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return """<html><body style="background:#0a0a0a;color:#eee;text-align:center;padding:50px;font-family:sans-serif;">
    <h1 style="color:#00ffcc;">CLARITY ACT AUDIT</h1><p>Risk detected in passive yield accounts.</p>
    <a href="/" style="color:#666;text-decoration:none;">← BACK</a></body></html>"""

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = ""
    if not vault_cache["yields"]:
        yield_cards = "<p style='color: #666; grid-column: 1/-1;'>Scanning protocols...</p>"
    else:
        for y in vault_cache["yields"]:
            p = y.get('protocol', 'Unknown')
            a = y.get('apy', '0.00')
            ast = y.get('asset', 'Asset')
            yield_cards += f"""
            <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
                <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{p}</h3>
                <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{a}%</p>
                <small style="color: #666;">{ast} | ACTIVE REWARD</small>
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
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); max-width: 900px; margin: 40px auto; }}
            </style>
        </head>
        <body>
            <h1 style="letter-spacing: 12px;">VAULTLOGIC</h1>
            <p style="color: #666; font-size: 11px;">{vault_cache['last_updated']}</p>
            <br>
            <button id="sync-button" class="sync-btn" onclick="syncWallet()">Sync Multi-Wallet (UHNW)</button>
            <div class="grid">{yield_cards}</div>

            <script>
                async function syncWallet() {{
                    const btn = document.getElementById('sync-button');
                    if (window.ethereum) {{
                        try {{
                            // This detects ANY wallet (MetaMask, Coinbase, Trust, etc.)
                            const provider = new ethers.providers.Web3Provider(window.ethereum);
                            await provider.send("eth_requestAccounts", []);
                            const signer = provider.getSigner();
                            const address = await signer.getAddress();
                            
                            btn.innerText = "SYNCED: " + address.substring(0,6) + "...";
                            btn.style.background = "#fff";

                            await fetch("/connect-wallet", {{ 
                                method: "POST", 
                                headers: {{ "Content-Type": "application/json" }}, 
                                body: JSON.stringify({{ address: address }}) 
                            }});
                        }} catch (err) {{ console.error("User cancelled"); }}
                    }} else {{
                        alert("No wallet extension detected. Please install MetaMask, Coinbase Wallet, or Trust Wallet.");
                    }}
                }}
            </script>
        </body>
    </html>
    """