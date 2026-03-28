import asyncio
import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")

# Shared state for the dashboard
vault_cache = {"yields": [], "status": "STABLE: MONITORING MODE"}
system_logs = ["VaultLogic Kernel Initialized...", "Frontend Wallet Auth Disabled.", "Monitoring YieldScout Streams..."]

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 15: system_logs.pop(0)

@app.get("/logs")
async def get_logs():
    return {"logs": system_logs}

@app.on_event("startup")
async def startup():
    async def sync():
        while True:
            try:
                vault_cache["yields"] = await get_all_yields()
                add_log("Yield Map Synchronized.")
            except Exception as e:
                add_log(f"Sync Warning: {str(e)}")
            await asyncio.sleep(60)
    asyncio.create_task(sync())

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    yield_cards = "".join([f"""
        <div style="background:#111; padding:20px; margin:10px; border-radius:8px; border-left:4px solid #00ffcc; text-align:left;">
            <h3 style="margin:0; color:#00ffcc; font-size:12px; text-transform:uppercase;">{y['protocol']}</h3>
            <p style="margin:5px 0; font-size:24px; font-weight:bold;">{y['apy']}% APY</p>
            <small style="color:#666;">{y['asset']} | Industrial Grade</small>
        </div>""" for y in vault_cache["yields"]])

    return f"""
    <html>
        <head>
            <title>VaultLogic | Monitoring</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background:#0a0a0a; color:white; font-family:sans-serif; text-align:center; padding:40px; margin:0; }}
                .container {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); max-width:1100px; margin:0 auto; }}
                #console {{ 
                    max-width:1000px; margin:50px auto; background:#050505; border:1px solid #222; 
                    padding:20px; text-align:left; font-family:monospace; font-size:12px; color:#666; 
                    height:180px; overflow-y:auto; border-radius:8px;
                }}
                .log-entry {{ border-bottom:1px solid #111; padding:5px 0; }}
            </style>
        </head>
        <body>
            <h1 style="letter-spacing:15px; margin-bottom: 5px;">VAULTLOGIC</h1>
            <p style="color:#00ffcc; font-size:11px; margin-bottom:30px; letter-spacing: 2px;">{vault_cache['status']}</p>
            
            <div class="container">{yield_cards}</div>

            <div id="console">
                <div style="color:#333; margin-bottom:10px; text-transform:uppercase; font-size:10px; font-weight:bold;">Industrial ALM Kernel Log</div>
                <div id="log-stream"></div>
            </div>

            <script>
                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        stream.innerHTML = data.logs.map(l => `<div class="log-entry">${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 2000);
            </script>
        </body>
    </html>
    """