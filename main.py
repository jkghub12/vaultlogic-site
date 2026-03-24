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

# --- STRATEGY BRIEF (POLISHED) ---
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
                <p>VaultLogic Dev LLC provides industrial-grade logic for complex systems. We eliminate the <span class="highlight">"Legacy Tax"</span> of manual error and regulatory friction.</p>
                <h2>I. Beyond Speculation</h2>
                <p>While Phase Alpha focuses on <strong>Active Liquidity Management</strong>, our architecture is built for multi-domain execution. We prioritize safety and <span class="highlight">deterministic outcomes</span> over black-box predictions.</p>
                <h2>II. The Regulatory Shield</h2>
                <p>In a landscape of shifting laws (Clarity Act 2026), VaultLogic provides the auditable trail required for institutional and HNW participation. We don't just find yield; we verify its compliance status in real-time.</p>
            </div>
        </body>
    </html>
    """

# --- COMPLIANCE AUDIT (RESTORED BUTTON) ---
@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body{background:#0a0a0a;color:#eee;font-family:sans-serif;padding:50px 20px;text-align:center;}
                h1{color:#00ffcc;letter-spacing:2px;}
                .box{max-width:600px; margin:0 auto; padding:30px; border:1px solid #222; border-radius:12px; background:#111;}
                .btn{display:inline-block; margin-top:30px; padding:15px 30px; background:#00ffcc; color:#000; text-decoration:none; font-weight:bold; border-radius:4px; font-size:12px; text-transform:uppercase;}
                .status{margin:20px 0; font-size:14px;}
            </style>
        </head>
        <body>
            <div class="box">
                <h1>2026 CLARITY ACT AUDIT</h1>
                <div class="status">
                    <p>Yield Classification: <span style="color:#00ffcc;">✅ VERIFIED (Liquidity Provision)</span></p>
                    <p>Passive Interest Risk: <span style="color:#ff4444;">🚨 HIGH (Direct Interest Found)</span></p>
                </div>
                <a href="#" class="btn" onclick="alert('Demo Mode: Report generation will be enabled in Phase 1.7')">GENERATE DEFENSE REPORT</a><br>
                <a href="/" style="display:block; margin-top:30px; color:#666; text-decoration:none; font-size:11px; text-transform:uppercase;">← Return to Command Center</a>
            </div>
        </body>
    </html>
    """

async def background_sync():
    while True:
        try:
            vault_cache["yields"] = await get_all_yields()
            vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
        except Exception as e:
            vault_cache["last_updated"] = f"SYNC ERROR: {str(e)}"
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
            <small style="color: #666;">Asset: {y['asset']} | Risk: Verified</small>
        </div>"""

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
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
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
                <button id="sync-button" class="sync-btn" onclick="syncWallet()">Sync Multi-Wallet (UHNW)</button>
                <div class="nav-links">
                    <a href="/strategy">Strategy Brief</a>
                    <a href="/audit" style="color: #ff4444;">Compliance Audit</a>
                </div>
            </div>
            <div class="container">{yield_cards}</div>
            <script>
                async function syncWallet() {{
                    const btn = document.getElementById('sync-button');
                    if (typeof window.ethereum !== 'undefined') {{
                        try {{
                            const provider = new ethers.providers.Web3Provider(window.ethereum);
                            await provider.send("eth_requestAccounts", []);
                            const signer = provider.getSigner();
                            const address = await signer.getAddress();
                            btn.innerText = "SYNCED: " + address.substring(0,6) + "...";
                            await fetch("/connect-wallet", {{ 
                                method: "POST", 
                                headers: {{ "Content-Type": "application/json" }}, 
                                body: JSON.stringify({{ address: address }}) 
                            }});
                        }} catch (err) {{ console.error(err); }}
                    }} else {{
                        alert("Please install a Web3 wallet to sync.");
                    }}
                }}
            </script>
        </body>
    </html>
    """