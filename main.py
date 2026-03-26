import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420'

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "0.0012 Gwei"
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

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    # Note: Using double {{ }} for all CSS/JS because this is a Python f-string
    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                
                /* THE POWER BUTTON */
                .connect-trigger {{
                    background: #00ffcc; color: #000; border: none; padding: 15px 35px; 
                    font-weight: bold; border-radius: 4px; cursor: pointer; 
                    text-transform: uppercase; font-size: 13px; letter-spacing: 2px;
                    box-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
                    transition: all 0.3s ease;
                }}
                .connect-trigger:hover {{ transform: scale(1.02); box-shadow: 0 0 25px rgba(0, 255, 204, 0.4); }}
                
                /* Ensure modal sits on top */
                w3m-modal {{ z-index: 99999 !important; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">STATUS: ACTIVE</p>
                
                <div id="wallet-section" style="margin: 40px 0;">
                    <button id="auth-btn" class="connect-trigger">Connect to Vault</button>
                    
                    <div style="display:none;"><w3m-button></w3m-button></div>
                    
                    <p id="wallet-status" style="font-size: 11px; color: #666; margin-top: 15px;"></p>
                </div>
            </div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi@4.1.1'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, reconnect, getAccount }} from 'https://esm.sh/@wagmi/core@2.6.5'

                const projectId = '{WC_PROJECT_ID}'
                const metadata = {{
                    name: 'VaultLogic Dev LLC',
                    description: 'Industrial DeFi Strategy',
                    url: 'https://vaultlogic.dev',
                    icons: ['https://avatars.githubusercontent.com/u/37784886']
                }}
                
                const chains = [mainnet, base]
                const wagmiConfig = defaultWagmiConfig({{ chains, projectId, metadata }})
                const modal = createWeb3Modal({{ wagmiConfig, projectId, chains, themeMode: 'dark' }})

                // Auto-reconnect on refresh
                reconnect(wagmiConfig)

                const btn = document.getElementById('auth-btn');
                const status = document.getElementById('wallet-status');

                // FORCE OPEN MODAL
                btn.onclick = async () => {{
                    console.log("VaultLogic: Initializing Handshake...");
                    await modal.open();
                }};

                // WATCH ACCOUNT STATE
                watchAccount(wagmiConfig, {{
                    onChange(account) {{
                        if (account.isConnected) {{
                            btn.innerText = "VAULT CONNECTED";
                            btn.style.background = "#222";
                            btn.style.color = "#00ffcc";
                            status.innerText = "LOGGED AS: " + account.address.slice(0,6) + "..." + account.address.slice(-4);
                            
                            // Sync to Railway Postgres
                            fetch("/connect-wallet", {{ 
                                method: "POST", 
                                headers: {{ "Content-Type": "application/json" }}, 
                                body: JSON.stringify({{ address: account.address }}) 
                            }});
                        }} else {{
                            btn.innerText = "Connect to Vault";
                            btn.style.background = "#00ffcc";
                            btn.style.color = "#000";
                            status.innerText = "";
                        }}
                    }}
                }})
            </script>
        </body>
    </html>
    """