import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from yieldscout import get_all_yields, heartbeat_monitor

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("🚀 Background Sync Task Initialized.")
    asyncio.create_task(heartbeat_monitor())

# --- THIS MAKES THE DASHBOARD THE MAIN PAGE ---
@app.get("/", response_class=HTMLResponse)
@app.get("/vault", response_class=HTMLResponse)
async def get_vault(request: Request):
    data = get_all_yields()
    
    yield_cards = ""
    for item in data["yields"]:
        yield_cards += f"""
        <div style="border: 1px solid #444; padding: 20px; margin: 10px; border-radius: 12px; background: #1e1e1e; min-width: 200px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
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
        </head>
        <body style="background: #111; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px;">
            <h1 style="color: #ffffff; letter-spacing: 2px; margin-bottom: 40px;">VAULTLOGIC COMMAND CENTER</h1>
            <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px;">{yield_cards}</div>
            <div style="margin-top: 50px; background: #1a1a1a; padding: 25px; border-radius: 15px; display: inline-block; border: 1px solid #333;">
                <h2 style="margin-top: 0; font-size: 18px; color: #aaa;">WALLET BALANCES (BASE)</h2>
                <p style="font-size: 22px; margin: 10px 0;">
                    <span style="color: #00ffcc;">{data['wallet']['eth']}</span> ETH &nbsp;|&nbsp; 
                    <span style="color: #00ffcc;">${data['wallet']['usdc']}</span> USDC
                </p>
                <p style="color: #555; font-size: 12px; margin-bottom: 0;">Synced: {data['last_updated']}</p>
            </div>
        </body>
    </html>
    """

# --- THIS FIXES THE API PATH ---
@app.get("/api/yield")
async def yield_api():
    return get_all_yields()