import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from yieldscout import get_all_yields, heartbeat_monitor

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("🚀 Vaultlogic Background Sync Task Initialized.")
    asyncio.create_task(heartbeat_monitor())

# --- THE MAIN DASHBOARD ---
@app.get("/", response_class=HTMLResponse)
@app.get("/vault", response_class=HTMLResponse)
async def get_vault(request: Request):
    data = get_all_yields()
    
    yield_cards = ""
    for item in data["yields"]:
        # Logic for the "Whale-Proof" labels
        label = item.get('label', 'New')
        badge_color = "#00ffcc" if label == "Core" else "#ffcc00" # Aqua for Core, Gold for AI-Approved
        
        yield_cards += f"""
        <div style="border: 1px solid #444; padding: 20px; margin: 10px; border-radius: 12px; background: #1e1e1e; min-width: 200px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); position: relative;">
            <span style="position: absolute; top: 10px; right: 10px; font-size: 10px; padding: 3px 8px; border-radius: 10px; background: {badge_color}; color: #000; font-weight: bold;">{label}</span>
            <h3 style="color: #00ffcc; margin-top: 0;">{item['protocol']}</h3>
            <p style="font-size: 28px; font-weight: bold; margin: 10px 0;">{item['yield']}</p>
            <p style="color: #888; font-size: 14px;">Asset: {item['asset']}</p>
        </div>
        """

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #111; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .container {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; }}
                .wallet-box {{ margin-top: 50px; background: #1a1a1a; padding: 25px; border-radius: 15px; display: inline-block; border: 1px solid #333; }}
            </style>
        </head>
        <body>
            <h1 style="color: #ffffff; letter-spacing: 2px; margin-bottom: 10px;">VAULTLOGIC COMMAND CENTER</h1>
            <p style="color: #666; margin-bottom: 40px;">March 2026 | AI-Agentic Yield Intelligence</p>
            
            <div class="container">{yield_cards}</div>
            
            <div class="wallet-box">
                <h2 style="margin-top: 0; font-size: 18px; color: #aaa;">VAULT BALANCE (BASE)</h2>
                <p style="font-size: 22px; margin: 10px 0;">
                    <span style="color: #00ffcc;">{data['wallet']['eth']}</span> ETH &nbsp;|&nbsp; 
                    <span style="color: #00ffcc;">${data['wallet']['usdc']}</span> USDC
                </p>
                <p style="color: #555; font-size: 12px; margin-bottom: 0;">Last Scouted: {data['last_updated']}</p>
            </div>
        </body>
    </html>
    """
# --- API ENDPOINT ---
@app.get("/api/yield")
async def yield_api():
    return get_all_yields()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

#Version 1