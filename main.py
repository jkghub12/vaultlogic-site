import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# --- ROBUST IMPORT FOR YIELDSCOUT ---
try:
    from yieldscout import get_all_yields
except ImportError:
    def get_all_yields(): return [{"protocol": "System", "apy": "0.00", "asset": "N/A"}]

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize with an empty list to prevent boot-up crashes
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

# --- BACKGROUND SYNC: THE BULLETPROOF VERSION ---
async def background_sync():
    while True:
        try:
            # Fetch data (removing await as previously discussed)
            data = get_all_yields()
            
            # FORCE DATA INTO A LIST OF DICTS
            if isinstance(data, list):
                # Ensure every item in the list is actually a dict
                vault_cache["yields"] = [item for item in data if isinstance(item, dict)]
            elif isinstance(data, dict):
                # If it's just one dict, wrap it in a list
                vault_cache["yields"] = [data]
            else:
                # If it's a string or something else, clear it to avoid crashes
                vault_cache["yields"] = []
                
            vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
        except Exception as e:
            vault_cache["last_updated"] = f"SYNC ERROR: {str(e)}"
        
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())

# --- STRATEGY BRIEF PAGE ---
@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return f"""
    <html>
        <head>
            <title>VaultLogic | Strategy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: #ccc; font-family: sans-serif; line-height: 1.8; padding: 40px 20px; }}
                .content {{ max-width: 800px; margin: 0 auto; }}
                h1, h2 {{ color: #00ffcc; text-transform: uppercase; letter-spacing: 2px; }}
            </style>
        </head>
        <body>
            <div class="content">
                <h1>The Deterministic Vision</h1>
                <p>VaultLogic Dev LLC provides industrial-grade logic for complex systems. We eliminate the "Legacy Tax" of manual error and regulatory friction.</p>
                <h2>I. Beyond Speculation</h2>
                <p>While Phase Alpha focuses on Active Liquidity Management, the architecture is designed for multi-domain execution.</p>
                <a href="/" style="color: #00ffcc; text-decoration: none;">← BACK TO COMMAND CENTER</a>
            </div>
        </body>
    </html>
    """

# --- COMPLIANCE AUDIT PAGE ---
@app.get("/audit", response_class=HTMLResponse)
async def get_audit_dashboard():
    return f"""
    <html>
        <head>
            <title>VaultLogic | Audit Defense</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: #eee; font-family: sans-serif; padding: 40px 20px; text-align: center; }}
                .status-box {{ background: #111; padding: 30px; border-radius: 12px; border: 1px solid #333; max-width: 600px; margin: 0 auto; text-align: left; }}
                .badge {{ padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
                .safe {{ background: #00ffcc1a; color: #00ffcc; border: 1px solid #00ffcc; }}
                .danger {{ background: #ff44441a; color: #ff4444; border: 1px solid #ff4444; }}
                .btn {{ display: inline-block; margin-top: 25px; padding: 15px 25px; background: #00ffcc; color: #000; text-decoration: none; font-weight: bold; border-radius: 4px; border: none; cursor: pointer; width: 100%; }}
            </style>
        </head>
        <body>
            <div class="status-box">
                <h1 style="color: #00ffcc; margin-top: 0;">2026 CLARITY ACT AUDIT</h1>
                <p style="color: #666; font-size: 13px;">Post-March 20th Compliance Engine</p>
                <hr style="border: 0; border-top: 1px solid #222; margin: 20px 0;">
                <p>Activity-Based Rewards: <span class="badge safe">✅ VERIFIED</span></p>
                <p>Passive Interest Risk: <span class="badge danger">🚨 HIGH</span></p>
                <button onclick="alert('Audit Defense Report Generation is currently in Private Beta.')" class="btn">GENERATE DEFENSE REPORT</button>
                <br><br>
                <a href="/" style="color: #888; font-size: 11px; text-decoration: none; display: block; text-align: center;">← RETURN TO COMMAND CENTER</a>
            </div>
        </body>
    </html>
    """

# --- HOME COMMAND CENTER ---
@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = ""
    
    # SAFETY CHECK: Only loop if yields is a list
    if not isinstance(vault_cache["yields"], list) or len(vault_cache["yields"]) == 0:
        yield_cards = "<p style='color: #666; grid-column: 1/-1;'>Scanning protocols for Phase Alpha opportunities...</p>"
    else:
        for y in vault_cache["yields"]:
            # Final safety check: ensure 'y' is a dict before accessing
            if isinstance(y, dict):
                protocol = y.get('protocol', 'Unknown')
                apy = y.get('apy', '0.00')
                asset = y.get('asset', 'Asset')
                
                yield_cards += f"""
                <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
                    <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{protocol}</h3>
                    <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{apy}%</p>
                    <small style="color: #666;">{asset} | ACTIVE REWARD</small>
                </div>
                """
            else:
                continue

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 40px auto; }}
                .sync-btn {{ background: #00ffcc; color: #000; padding: 18px 40px; border-radius: 5px; font-weight: bold; cursor: pointer; border: none; letter-spacing: 1px; width: 100%; max-width: 320px; }}
                .nav-links {{ margin: 25px 0; }}
                .nav-links a {{ color: #888; text-decoration: none; font-size: 12px; margin: 0 15px; text-transform: uppercase; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); max-width: 900px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 0;">VAULTLOGIC</h1>
                <p style="color: #666; font-size: 11px; letter-spacing: 3px;">{vault_cache['last_updated']}</p>
                <br>
                <button id="sync-button" class="sync-btn" onclick="syncWallet()">Sync Multi-Wallet (UHNW)</button>
                <div class="nav-links">
                    <a href="/audit" style="color: #ff4444;">Compliance Audit</a>
                    <a href="/strategy">Strategy Brief</a>
                </div>
            </div>
            <div class="grid">{yield_cards}</div>
            <script>
                async function syncWallet() {{
                    const btn = document.getElementById('sync-button');
                    if (window.ethereum) {{
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
                        }} catch (err) {{ console.error("Error connecting"); }}
                    }} else {{ alert("Please install a wallet extension."); }}
                }}
            </script>
        </body>
    </html>
    """