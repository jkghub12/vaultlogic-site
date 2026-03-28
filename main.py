import asyncio
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Initialize the app BEFORE any routes
app = FastAPI()

# Configuration & Cache
DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420'

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
    "wallet_balance": "0.000 ETH",
    "usdc_balance": "0.00 USDC",
    "engine_status": "OFFLINE"
}

class WalletConnect(BaseModel):
    address: str

# NOW you can define your routes
@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    # ... (rest of your code)
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
                .gas-tag {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; }}
                .simulator {{ max-width: 1000px; margin: 40px auto; padding: 20px; background: #050505; border: 1px dashed #222; border-radius: 8px; }}
                w3m-button {{ margin-top: 20px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
                <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
                
                <div style="background: #050505; border: 1px solid #222; padding: 15px; margin: 20px auto; max-width: 400px; font-family: monospace; font-size: 12px; text-align: left; border-left: 3px solid #00ffcc; line-height: 1.6;">
                    <div style="color: #666;">> ENGINE_STATUS: <span style="color: #00ffcc;">{vault_cache.get('engine_status', 'OFFLINE')}</span></div>
                    <div style="color: #666;">> ASSET_ETH: <span style="color: #eee;">{vault_cache.get('wallet_balance', '0.000 ETH')}</span></div>
                    <div style="color: #666;">> ASSET_USDC: <span style="color: #eee;">{vault_cache.get('usdc_balance', '0.00 USDC')}</span></div>
                </div>

                <div class="gas-tag">Network Fee (Base): {vault_cache['gas_price']}</div>
                
                <div id="btn-container">
                    <w3m-button></w3m-button>
                </div>

                <div class="nav-links" style="margin-top:20px;">
                    <a href="/strategy">Strategy Brief</a>
                    <a href="/audit" style="color: #ff4444;">Compliance Audit</a>
                </div>
            </div>

            <div class="container">{yield_cards}</div>

            <div class="simulator">
                <h2 style="font-size: 14px; color: #00ffcc; text-transform: uppercase; letter-spacing: 3px;">Validation Tier Simulator ($500 Base)</h2>
                <div style="display: flex; justify-content: space-around; padding: 20px;">
                    <div style="text-align: left;">
                        <p style="margin:0; font-size: 11px; color: #666;">PASSIVE HOLDING (2.8%)</p>
                        <p style="margin:0; font-size: 20px;">$500.55 <small style="font-size: 10px; color: #ff4444;">(-$0.00 Fee)</small></p>
                    </div>
                    <div style="text-align: right;">
                        <p style="margin:0; font-size: 11px; color: #00ffcc;">VAULTLOGIC ACTIVE (ALM)</p>
                        <p style="margin:0; font-size: 20px;">$534.20 <small style="font-size: 10px; color: #00ffcc;">(+$34.20 Proj.)</small></p>
                    </div>
                </div>
                <p style="font-size: 10px; color: #444;">*Projected 14-day cycle performance based on Uniswap V3 WETH/USDC efficiency.</p>
            </div>

            <script type="module">
                import {{ createAppKit }} from 'https://esm.sh/@reown/appkit'
                import {{ mainnet, base }} from 'https://esm.sh/@reown/appkit/networks'
                import {{ WagmiAdapter }} from 'https://esm.sh/@reown/appkit-adapter-wagmi'
                import {{ watchAccount, reconnect, disconnect, getAccount, signMessage }} from 'https://esm.sh/@wagmi/core'

                const projectId = '{WC_PROJECT_ID}'
                const networks = [base, mainnet]

                const wagmiAdapter = new WagmiAdapter({{
                    projectId,
                    networks
                }})

                const modal = createAppKit({{
                    adapters: [wagmiAdapter],
                    networks,
                    projectId,
                    features: {{ analytics: false, email: false, socials: false }},
                    themeMode: 'dark'
                }})

                async function forceSync() {{
                    try {{
                        const state = getAccount(wagmiAdapter.wagmiConfig);
                        if (state.status === 'connecting') {{
                            await disconnect(wagmiAdapter.wagmiConfig);
                        }}
                        await reconnect(wagmiAdapter.wagmiConfig);
                    }} catch (e) {{ console.warn("Reset handled."); }}
                }}
                forceSync();

                async function secureSignIn(address) {{
                    const currentEth = "{vault_cache.get('wallet_balance', '0.000 ETH')}";
                    if (currentEth !== "0.000 ETH") return;

                    try {{
                        await signMessage(wagmiAdapter.wagmiConfig, {{
                            message: `VaultLogic Auth\\nAddress: ${{address}}\\nTS: ${{Date.now()}}`
                        }});

                        const res = await fetch('/connect-wallet', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ address }})
                        }});
                        if (res.ok) setTimeout(() => window.location.reload(), 1200);
                    }} catch (err) {{
                        await disconnect(wagmiAdapter.wagmiConfig);
                    }}
                }}

                watchAccount(wagmiAdapter.wagmiConfig, {{
                    onChange(account) {{
                        if (account.isConnected && account.address) {{
                            secureSignIn(account.address);
                        }}
                    }}
                }})
            </script>
        </body>
    </html>
    """