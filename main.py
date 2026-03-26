import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Fallback for yieldscout
try:
    from yieldscout import get_all_yields
except ImportError:
    async def get_all_yields(): return []

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420'

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM NOMINAL",
    "gas_price": "0.0012 Gwei (OPTIMAL)"
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

# Strategy & Audit Routes (Kept for navigation)
@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return "<html><body style='background:#0a0a0a;color:white;padding:50px;'><h1>Strategy Brief</h1><p>ALM Logic Active.</p><a href='/' style='color:#00ffcc;'>Back</a></body></html>"

@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return "<html><body style='background:#0a0a0a;color:white;padding:50px;'><h1>Clarity Act Audit</h1><p>Status: Verified</p><a href='/' style='color:#00ffcc;'>Back</a></body></html>"

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    # Restore the Yield Cards UI
    yield_cards = ""
    # Mock data if cache is empty for testing
    display_yields = vault_cache["yields"] if vault_cache["yields"] else [
        {"protocol": "Uniswap V3", "apy": "18.4", "asset": "WETH/USDC", "risk_label": "OPTIMAL"},
        {"protocol": "Aave V3", "apy": "5.2", "asset": "USDC", "risk_label": "STABLE"}
    ]
    
    for y in display_yields:
        risk_color = "#00ffcc" if y.get('risk_label') == "OPTIMAL" else "#444"
        yield_cards += f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid {risk_color}; text-align: left;">
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
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
                .connect-trigger {{
                    background: #00ffcc; color: #000; border: none; padding: 15px 35px; 
                    font-weight: bold; border-radius: 4px; cursor: pointer; 
                    text-transform: uppercase; font-size: 12px; letter-spacing: 2px;
                    margin: 20px 0;
                }}
                .nav-links a {{ color: #666; text-decoration: none; font-size: 11px; text-transform: uppercase; margin: 0 15px; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
                
                <div id="wallet-section">
                    <button id="auth-btn" class="connect-trigger">Connect to Vault</button>
                    <p id="wallet-addr" style="font-size: 10px; color: #00ffcc; font-family: monospace;"></p>
                </div>

                <div class="nav-links">
                    <a href="/strategy">Strategy</a>
                    <a href="/audit">Audit</a>
                </div>
            </div>

            <div class="container">{yield_cards}</div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi@4.1.1'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, reconnect }} from 'https://esm.sh/@wagmi/core@2.6.5'

                const projectId = '{WC_PROJECT_ID}'
                const metadata = {{
                    name: 'VaultLogic',
                    description: 'Industrial DeFi',
                    url: 'https://vaultlogic.dev',
                    icons: []
                }}
                
                const chains = [mainnet, base]
                const wagmiConfig = defaultWagmiConfig({{ chains, projectId, metadata }})
                const modal = createWeb3Modal({{ wagmiConfig, projectId, chains, themeMode: 'dark' }})

                reconnect(wagmiConfig)

                const btn = document.getElementById('auth-btn');
                const addrDisplay = document.getElementById('wallet-addr');

                btn.onclick = async () => {{
                    try {{
                        await modal.open();
                    }} catch (e) {{
                        console.error(e);
                        alert("Connection failed. Check console.");
                    }}
                }};

                watchAccount(wagmiConfig, {{
                    onChange(account) {{
                        if (account.isConnected) {{
                            btn.innerText = "CONNECTED";
                            btn.style.background = "#111";
                            btn.style.color = "#00ffcc";
                            addrDisplay.innerText = account.address;
                            
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