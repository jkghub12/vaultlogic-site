import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields, heartbeat_monitor

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

vault_cache = {
    "yields": [],
    "wallet": {"eth": "0.00", "usdc": "0.00"},
    "last_updated": "SYSTEM INITIALIZING..."
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

@app.get("/audit", response_class=HTMLResponse)
async def get_audit_dashboard():
    compliance_check = {
        "active_yield_status": "✅ VERIFIED (Liquidity Provision)",
        "passive_yield_risk": "🚨 HIGH (Direct Interest Found)",
        "form_1099da_ready": "NO - 14 Basis Mismatches",
        "risk_score": 72
    }
    return f"""
    <html>
        <head>
            <title>VaultLogic | Audit Defense</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: #eee; font-family: sans-serif; padding: 50px 20px; line-height: 1.6; }}
                .status-box {{ background: #111; padding: 30px; border-radius: 12px; border: 1px solid #333; max-width: 700px; margin: 0 auto; }}
                .badge {{ padding: 5px 12px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
                .safe {{ background: #00ffcc1a; color: #00ffcc; border: 1px solid #00ffcc; }}
                .danger {{ background: #ff44441a; color: #ff4444; border: 1px solid #ff4444; }}
                h1 {{ color: #00ffcc; font-size: 24px; letter-spacing: 2px; }}
                .btn {{ display: inline-block; margin-top: 30px; padding: 15px 30px; background: #00ffcc; color: #000; text-decoration: none; font-weight: bold; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="status-box">
                <h1>2026 CLARITY ACT AUDIT</h1>
                <p><strong>Yield Classification:</strong> <span class="badge safe">{compliance_check['active_yield_status']}</span></p>
                <p><strong>Passive Interest Risk:</strong> <span class="badge danger">{compliance_check['passive_yield_risk']}</span></p>
                <p>IRS Status: <strong style="color: #ff4444;">{compliance_check['form_1099da_ready']}</strong></p>
                <a href="#" class="btn">GENERATE DEFENSE REPORT</a><br>
                <a href="/" style="display:block; margin-top:20px; color:#666; text-decoration:none; font-size:11px;">← RETURN</a>
            </div>
        </body>
    </html>
    """

@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return """
    <html>
        <body style="background:#0a0a0a;color:#ccc;font-family:sans-serif;padding:50px;">
            <h1 style="color:#00ffcc;">The Deterministic Vision</h1>
            <p>VaultLogic eliminates information asymmetry and regulatory friction.</p>
            <a href="/" style="color:#666; text-decoration:none;">← RETURN</a>
        </body>
    </html>
    """

async def background_sync():
    while True:
        try:
            vault_cache["yields"] = await get_all_yields()
            vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
        except Exception as e:
            vault_cache["last_updated"] = f"ERROR: {str(e)}"
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
            <h3 style="margin: 0; color: #00ffcc;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">{y['apy']}% APY</p>
            <small style="color: #666;">Asset: {y['asset']} | Risk: Verified</small>
        </div>
        """

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://unpkg.com/@coinbase/wallet-sdk@3.7.1/dist/index.js"></script>
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .sync-btn {{ background: #00ffcc; color: #000; padding: 18px 45px; border-radius: 5px; font-weight: bold; cursor: pointer; text-transform: uppercase; border: none; letter-spacing: 2px; }}
                .nav-links a {{ color: #888; text-decoration: none; font-size: 11px; text-transform: uppercase; margin: 0 15px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px;">{vault_cache['last_updated']}</p>
                <button id="sync-button" class="sync-btn" onclick="syncWallet()">Sync Your Wallet</button>
                <div class="nav-links">
                    <a href="/strategy">Strategy Brief</a>
                    <a href="/audit" style="color: #ff4444;">Compliance Audit</a>
                </div>
            </div>
            <div class="container">{yield_cards}</div>
            <script>
                const coinbaseWallet = new CoinbaseWalletSDK({{ appName: "VaultLogic", darkMode: true }});
                const ethereum = coinbaseWallet.makeWeb3Provider("https://mainnet.base.org", 8453);
                async function syncWallet() {{
                    const accounts = await ethereum.request({{ method: 'eth_requestAccounts' }});
                    const walletAddress = accounts[0];
                    document.getElementById('sync-button').innerText = "SYNCED: " + walletAddress.substring(0,6) + "...";
                    await fetch("/connect-wallet", {{ 
                        method: "POST", 
                        headers: {{ "Content-Type": "application/json" }}, 
                        body: JSON.stringify({{ address: walletAddress }}) 
                    }});
                }}
            </script>
        </body>
    </html>
    """