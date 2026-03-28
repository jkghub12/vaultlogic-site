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
    "last_updated": "ACTIVE: SYSTEM NOMINAL",
    "gas_price": "0.0012 Gwei (OPTIMAL)"
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

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .gas-tag {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; }}
                .balance-table {{ margin: 20px auto; border-collapse: collapse; min-width: 300px; font-family: monospace; border: 1px solid #222; }}
                .balance-table td {{ padding: 10px; border: 1px solid #222; }}
                .val {{ color: #00ffcc; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
                <div class="gas-tag">Network Fee (Base): {vault_cache['gas_price']}</div>
                
                <table class="balance-table">
                    <tr><td style="color:#666">STATUS</td><td id="stat-cell" style="color:#ff4444">DISCONNECTED</td></tr>
                    <tr><td style="color:#666">WALLET</td><td id="addr-cell">---</td></tr>
                    <tr><td style="color:#666">ETH</td><td id="eth-cell">0.000</td></tr>
                    <tr><td style="color:#666">USDC</td><td id="usdc-cell">0.00</td></tr>
                </table>

                <w3m-button></w3m-button>
                
                <div style="margin-top:20px;">
                    <a href="/strategy" style="color:#888; text-decoration:none; font-size:11px; text-transform:uppercase; margin:0 15px;">Strategy Brief</a>
                    <a href="/audit" style="color:#ff4444; text-decoration:none; font-size:11px; text-transform:uppercase; margin:0 15px;">Compliance Audit</a>
                </div>
            </div>

            <script type="module">
                import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi'
                import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
                import {{ watchAccount, getBalance }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}';
                const config = defaultWagmiConfig({{ 
                    chains: [mainnet, base], 
                    projectId, 
                    metadata: {{ name: 'VaultLogic' }} 
                }});
                
                createWeb3Modal({{ wagmiConfig: config, projectId, chains: [mainnet, base] }});

                watchAccount(config, {{
                    async onChange(acc) {{
                        if (acc.isConnected) {{
                            // Update UI Instantly
                            document.getElementById('stat-cell').innerText = "CONNECTED";
                            document.getElementById('stat-cell').style.color = "#00ffcc";
                            document.getElementById('addr-cell').innerText = acc.address.substring(0,6) + "..." + acc.address.substring(38);

                            // Fetch Balances
                            const ethB = await getBalance(config, {{ address: acc.address, chainId: base.id }});
                            document.getElementById('eth-cell').innerText = ethB.formatted.substring(0, 6) + " ETH";

                            try {{
                                const usdcB = await getBalance(config, {{ 
                                    address: acc.address, 
                                    chainId: base.id, 
                                    token: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913' 
                                }});
                                document.getElementById('usdc-cell').innerText = usdcB.formatted.substring(0, 7) + " USDC";
                            }} catch(e) {{}}

                            // Notify Server
                            fetch("/connect-wallet", {{ 
                                method: "POST", 
                                headers: {{ "Content-Type": "application/json" }}, 
                                body: JSON.stringify({{ address: acc.address }}) 
                            }});
                        }} else {{
                            document.getElementById('stat-cell').innerText = "DISCONNECTED";
                            document.getElementById('stat-cell').style.color = "#ff4444";
                        }}
                    }}
                }});
            </script>
        </body>
    </html>
    """