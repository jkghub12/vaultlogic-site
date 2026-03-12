import os
import json
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from eth_account import Account
from dotenv import load_dotenv

from yieldscout import get_all_yields, heartbeat_monitor

load_dotenv()
app = FastAPI(title="VaultLogic Ecosystem")
app.mount("/static", StaticFiles(directory="."), name="static")

@app.on_event("startup")
async def startup_event():
    # Glue the background sync to the server's lifecycle
    asyncio.create_task(heartbeat_monitor())
    print("🚀 Background Sync Task Initialized.")

# --- LANDING & DASHBOARD HTML (Omitted for brevity, keep your existing HTML strings) ---
# [Keep your LANDING_HTML and DASHBOARD_HTML here]

@app.get("/", response_class=HTMLResponse)
async def home():
    return LANDING_HTML

@app.get("/vault", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/api/yield")
async def yield_api():
    return get_all_yields()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)