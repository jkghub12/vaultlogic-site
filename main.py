import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from yieldscout import get_all_yields, heartbeat_monitor

app = FastAPI()

# 🛡️ GLOBAL CACHE: Updated with a more professional initialization message.
vault_cache = {
    "yields": [],
    "wallet": {"eth": "0.00", "usdc": "0.00"},
    "last_updated": "SYNCING WITH BASE MAINNET..."
}

# 🚀 BACKGROUND TASK: Keeps the cache fresh without slowing down the site.
async def background_sync():
    global vault_cache
    while True:
        try:
            print("🔍 Vaultlogic Scout: Syncing with Base Network...")
            new_data = get_all_yields()
            if new_data:
                vault_cache = new_data
                print(f"✅ Sync Complete: {new_data['last_updated']}")
        except Exception as e:
            print(f"❌ Scout Error: {e}")
        
        # Wait 60 seconds before scouting again
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    print("🚀 Vaultlogic Command Center Initialized.")
    asyncio.create_task(heartbeat_monitor())
    asyncio.create_task(background_sync())

CHART_LINKS = {
    "Aave V3": "https://app.aave.com/reserve-overview/?underlyingAsset=0x833589fcd6edbe08f4c7c32d4f71b54bda02913&marketName=proto_base_v3",
    "Aave-v3": "https://app.aave.com/reserve-overview/?underlyingAsset=0x833589fcd6edbe08f4c7c32d4f71b54bda02913&marketName=proto_base_v3",
    "Uniswap V3": "https://app.uniswap.org/explore/pools/base/0x4C36388bE6F416A29C8d8Eee81c771cE6bE14B18",
    "STEAKUSDC": "https://app.morpho.org/base/vault/0xbeeF010f9cb27031ad51e3333f9aF9C6B1228183/steakhouse-usdc",
    "GTUSDCP": "https://app.morpho.org/base/vault/0xba5856d116c478676662e08620808a3d3ed072c4/gauntlet-usdc-prime"
}

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    data = vault_cache
    
    yield_cards = ""
    for item in data.get("yields", []):
        label = item.get('label', 'New')
        badge_color = "#00ffcc" if label == "Core" else "#ffcc00"
        target_link = CHART_LINKS.get(item['asset'], CHART_LINKS.get(item['protocol'], "https://basescan.org"))
        
        yield_cards += f"""
        <a href="{target_link}" target="_blank" style="text-decoration: none; color: inherit;">
            <div style="border: 1px solid #444; padding: 20px; margin: 10px; border-radius: 12px; background: #1e1e1e; min-width: 220px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); position: relative; transition: transform 0.2s, border-color 0.2s; cursor: pointer;" 
                 onmouseover="this.style.transform='scale(1.03)'; this.style.borderColor='#00ffcc';" 
                 onmouseout="this.style.transform='scale(1)'; this.style.borderColor='#444';">
                <span style="position: absolute; top: 10px; right: 10px; font-size: 10px; padding: 3px 8px; border-radius: 10px; background: {badge_color}; color: #000; font-weight: bold;">{label}</span>
                <h3 style="color: #00ffcc; margin-top: 0;">{item['protocol']}</h3>
                <p style="font-size: 28px; font-weight: bold; margin: 10px 0;">{item['yield']}</p>
                <p style="color: #888; font-size: 14px;">Asset: {item['asset']}</p>
                <div style="margin-top: 15px; font-size: 11px; color: #00ffcc; border-top: 1px solid #333; padding-top: 10px;">
                    VERIFY ON-CHAIN ↗
                </div>
            </div>
        </a>
        """

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 40px 20px; }}
                .container {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; max-width: 1200px; margin: 0 auto; }}
                
                /* Mission Section */
                .mission-brief {{ max-width: 700px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 30px; }}
                .mission-brief h1 {{ color: #ffffff; letter-spacing: 5px; margin-bottom: 10px; text-transform: uppercase; }}
                .mission-brief h2 {{ font-size: 14px; color: #888; text-transform: uppercase; letter-spacing: 4px; margin-bottom: 20px; }}
                .mission-brief p {{ font-size: 18px; line-height: 1.6; color: #ccc; font-style: italic; }}
                
                .wallet-box {{ margin-top: 50px; background: #151515; padding: 25px; border-radius: 15px; display: inline-block; border: 1px solid #333; box-shadow: 0 0 20px rgba(0,255,204,0.05); }}
                .footnote {{ color: #444; font-size: 10px; margin-top: 30px; text-transform: uppercase; letter-spacing: 2px; }}
                
                /* Pulse Animation for the Agent */
                .agent-pulse {{ display: inline-block; width: 8px; height: 8px; background: #00ffcc; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 10px #00ffcc; animation: pulse 2s infinite; }}
                @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} 100% {{ opacity: 1; }} }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
                <h1>VAULTLOGIC</h1>
                <h2>Deterministic DeFi Intelligence</h2>
                <p>"The 'Legacy Tax' is the cost of manual error. We build autonomous guardrails to eliminate it."</p>
                <div style="margin-top: 20px; font-size: 12px; color: #00ffcc; font-weight: bold; text-transform: uppercase;">
                    <span class="agent-pulse"></span> SYSTEM PULSE: ACTIVE ON BASE MAINNET
                </div>
            </div>

            <div class="container">{yield_cards}</div>
            
            <div class="wallet-box">
                <h2 style="margin-top: 0; font-size: 14px; color: #ffcc00; text-transform: uppercase; letter-spacing: 1px;">Strategic Canary Vault</h2>
                <p style="font-size: 24px; margin: 12px 0; font-weight: bold;">
                    <span style="color: #ffffff;">{data['wallet']['eth']}</span> <span style="font-size: 14px; color: #666;">ETH</span> &nbsp;|&nbsp; 
                    <span style="color: #ffffff;">${data['wallet']['usdc']}</span> <span style="font-size: 14px; color: #666;">USDC</span>
                </p>
                <p style="color: #444; font-size: 11px; margin-bottom: 0;">Last On-Chain Sync: {data['last_updated']}</p>
            </div>
            
            <p class="footnote">VaultLogic.dev — Built for the $BNKR Ecosystem</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    # Railway typically injects a PORT environment variable
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)