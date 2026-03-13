import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from yieldscout import get_all_yields, heartbeat_monitor

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("🚀 Vaultlogic Background Sync Task Initialized.")
    asyncio.create_task(heartbeat_monitor())

# Updated Mapping for forced Base Market loading
CHART_LINKS = {
    "Aave V3": "https://app.aave.com/reserve-overview/?underlyingAsset=0x833589fcd6edbe08f4c7c32d4f71b54bda02913&marketName=proto_base_v3",
    "Aave-v3": "https://app.aave.com/reserve-overview/?underlyingAsset=0x833589fcd6edbe08f4c7c32d4f71b54bda02913&marketName=proto_base_v3",
    "Uniswap V3": "https://app.uniswap.org/explore/pools/base/0x4C36388bE6F416A29C8d8Eee81c771cE6bE14B18",
    "STEAKUSDC": "https://app.morpho.org/base/vault/0xbeeF010f9cb27031ad51e3333f9aF9C6B1228183/steakhouse-usdc",
    "GTUSDCP": "https://app.morpho.org/base/vault/0xba5856d116c478676662e08620808a3d3ed072c4/gauntlet-usdc-prime"
}

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    data = get_all_yields()
    
    yield_cards = ""
    for item in data["yields"]:
        label = item.get('label', 'New')
        badge_color = "#00ffcc" if label == "Core" else "#ffcc00"
        
        # Determine the link based on Asset name first, then Protocol name
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
                .container {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; }}
                .wallet-box {{ margin-top: 50px; background: #151515; padding: 25px; border-radius: 15px; display: inline-block; border: 1px solid #333; box-shadow: 0 0 20px rgba(0,255,204,0.05); }}
                .footnote {{ color: #444; font-size: 10px; margin-top: 30px; text-transform: uppercase; letter-spacing: 2px; }}
            </style>
        </head>
        <body>
            <h1 style="color: #ffffff; letter-spacing: 3px; margin-bottom: 5px;">VAULTLOGIC COMMAND CENTER</h1>
            <p style="color: #00ffcc; font-size: 12px; margin-bottom: 40px; font-weight: bold; text-transform: uppercase;">Verified AI-Agentic Yield Intelligence</p>
            
            <div class="container">{yield_cards}</div>
            
            <div class="wallet-box">
                <h2 style="margin-top: 0; font-size: 14px; color: #ffcc00; text-transform: uppercase; letter-spacing: 1px;">Test Vault (Internal Monitoring)</h2>
                <p style="font-size: 24px; margin: 12px 0; font-weight: bold;">
                    <span style="color: #ffffff;">{data['wallet']['eth']}</span> <span style="font-size: 14px; color: #666;">ETH</span> &nbsp;|&nbsp; 
                    <span style="color: #ffffff;">${data['wallet']['usdc']}</span> <span style="font-size: 14px; color: #666;">USDC</span>
                </p>
                <p style="color: #444; font-size: 11px; margin-bottom: 0;">System Pulse: {data['last_updated']}</p>
            </div>
            
            <p class="footnote">Real-time performance monitoring via canary wallet address</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)