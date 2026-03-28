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
    "gas_price": "0.0012 Gwei (OPTIMAL)",
    "wallet_balance": "0.000 ETH",
    "usdc_balance": "0.00 USDC",
    "wallet_address": None
}

class WalletConnect(BaseModel):
    address: str
    eth_balance: str
    usdc_balance: str

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        vault_cache["wallet_address"] = data.address
        vault_cache["wallet_balance"] = data.eth_balance
        vault_cache["usdc_balance"] = data.usdc_balance
        
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

async def background_sync():
    while True:
        try:
            vault_cache["yields"] = await get_all_yields()
        except:
            pass
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_sync())

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    addr = vault_cache["wallet_address"]
    display_addr = f"{addr[:6]}...{addr[-4:]}" if addr else "NOT CONNECTED"
    
    # Hide table if no wallet is connected
    balance_table = ""
    if addr:
        balance_table = f"""
        <table style="margin: 20px auto; border-collapse: collapse; width: 300px; font-family: monospace; font-size: 12px; border: 1px solid #222;">
            <tr style="border-bottom: 1px solid #222;">
                <td style="padding: 10px; color: #666; text-align: left;">ASSET</td>
                <td style="padding: 10px; color: #00ffcc; text-align: right;">BALANCE</td>
            </tr>
            <tr>
                <td style="padding: 10px; text-align: left;">Ethereum</td>
                <td style="padding: 10px; text-align: right;">{vault_cache['wallet_balance']}</td>
            </tr>
            <tr>
                <td style="padding: 10px; text-align: left;">USDC (Base)</td>
                <td style="padding: 10px; text-align: right;">{vault_cache['usdc_balance']}</td>
            </tr>
        </table>
        """

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .gas-tag {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; }}
                w3m-button {{ margin-top: 20px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
                <div class="gas-tag">Network Fee (Base): {vault_cache['gas_price']}</div>
                
                {balance_table}
                <p style="font-size: 11px; color: #444; margin-top: 5px;">WALLET: {display_addr}</p>

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

                let isSyncing = false;

                watchAccount(config, {{
                    async onChange(acc) {{
                        if (acc.isConnected && !isSyncing && !"{addr}") {{
                            isSyncing = true;
                            const ethB = await getBalance(config, {{ address: acc.address, chainId: base.id }});
                            let usdcVal = "0.00 USDC";
                            try {{
                                const usdcB = await getBalance(config, {{ 
                                    address: acc.address, 
                                    chainId: base.id, 
                                    token: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913' 
                                }});
                                usdcVal = usdcB.formatted.substring(0, 7) + " USDC";
                            }} catch(e) {{ }}

                            const res = await fetch("/connect-wallet", {{ 
                                method: "POST", 
                                headers: {{ "Content-Type": "application/json" }}, 
                                body: JSON.stringify({{ 
                                    address: acc.address,
                                    eth_balance: ethB.formatted.substring(0, 6) + " ETH",
                                    usdc_balance: usdcVal
                                }}) 
                            }});
                            
                            if (res.ok) {{
                                window.location.reload();
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
    </html>
    """