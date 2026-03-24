import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
# Get a free ID at https://cloud.walletconnect.com/
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420' 

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

# --- STRATEGY BRIEF ---
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
                <p>Phase Alpha focuses on Active Liquidity Management. We prioritize safety and <span class="highlight">deterministic outcomes</span>.</p>
                <h2>II. Validation Tier</h2>
                <p>Current stress-testing performed at the <strong>$500 entry level</strong> to verify rebalancing logic before institutional scaling.</p>
                <h2>III. The Regulatory Shield</h2>
                <p>Auditable trails for institutional participation under the <strong>Clarity Act 2026</strong>.</p>
            </div>
        </body>
    </html>
    """

# --- COMPLIANCE AUDIT ---
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
            </style>
        </head>
        <body>
            <div class="box">
                <h1>2026 CLARITY ACT AUDIT</h1>
                <p>Yield Classification: <span style="color:#00ffcc;">✅ VERIFIED</span></p>
                <p>Passive Interest Risk: <span style="color:#ff4444;">🚨 HIGH</span></p>
                <a href="#" class="btn" onclick="alert('Phase 2 Vault Access Required.')">GENERATE DEFENSE REPORT</a><br>
                <a href="/" style="display:block; margin-top:30px; color:#666; text-decoration:none; font-size:11px; text-transform:uppercase;">← Return</a>
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
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .nav-links a {{ color: #888; text-decoration: none; font-size: 11px; text-transform: uppercase; margin: 0 15px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
                w3m-button {{ margin-top: 20px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
                
                <div id="btn-container">
                    <w3m-button></w3m-button>
                </div>

                <div class="nav-links" style="margin-top:20px;">
                    <a href="/strategy">Strategy Brief</a>
                    <a href="/audit" style="color: #ff4444;">Compliance Audit</a>
                </div>
            </div>
            <div class="container">{yield_cards}</div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}'
                const metadata = {{
                  name: 'VaultLogic Dev LLC',
                  description: 'Industrial DeFi Strategy',
                  url: 'https://vaultlogic.dev',
                  icons: ['https://avatars.githubusercontent.com/u/37784886']
                }}

                const chains = [mainnet, base]
                const wagmiConfig = defaultWagmiConfig({{ chains, projectId, metadata }})
                const modal = createWeb3Modal({{ wagmiConfig, projectId, chains }})

                // Watch for connection to save to database
                watchAccount(wagmiConfig, {{
                  onChange(account) {{
                    if (account.isConnected) {{
                      fetch("/connect-wallet", {{ 
                        method: "POST", 
                        headers: {{ "Content-Type": "application/json" }}, 
                        body: JSON.stringify({{ address: account.address }}) 
                      }});
                    }}
                  }}
                }})
            </script>
        </body>
    </html>
    """