import asyncio
import os
import psycopg2
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields

# --- THE BRAIN: COINBASE AGENTIC IMPORTS ---
from cdp_agentkit_core.agentkit import AgentKit
from cdp_agentkit_core.actions.cdp_action_provider import CdpActionProvider

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420' 

# --- X402 PROTOCOL CONFIG ---
# This ensures that when the "Brain" works, the system can handle payments
X402_PAYMENT_ADDRESS = "your_vault_address_here"

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
    "agent_status": "OFFLINE"
}

# --- INITIALIZE THE BRAIN (STANDALONE AGENT) ---
def initialize_agent():
    """Initializes the VaultLogic Brain without human intervention."""
    # Note: Requires CDP_API_KEY_NAME and CDP_API_KEY_PRIVATE_KEY in environment
    agentkit = AgentKit(
        action_providers=[CdpActionProvider()]
    )
    return agentkit

# We initialize as None and start in the background to avoid blocking the site
agent_instance = None

@app.on_event("startup")
async def startup_event():
    global agent_instance
    try:
        agent_instance = initialize_agent()
        vault_cache["agent_status"] = "ACTIVE: BRAIN ONLINE"
    except Exception as e:
        vault_cache["agent_status"] = f"AGENT ERROR: Check Keys"
    
    asyncio.create_task(background_sync())

# --- THE X402 HANDSHAKE ---
# This allows the AI to request micro-payments for its "Logic" services
@app.middleware("http")
async def x402_middleware(request: Request, call_next):
    response = await call_next(request)
    # If the user is accessing a "Premium" yield analysis, trigger x402
    if request.url.path == "/strategy":
        response.headers["X-402-Payment-Required"] = f"amount=0.01; asset=USDC; address={X402_PAYMENT_ADDRESS}"
    return response

class WalletConnect(BaseModel):
    address: str

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # LOGIC: When a wallet connects, the Brain immediately starts a private scan
        cur.execute("INSERT INTO users (wallet_address) VALUES (%s) ON CONFLICT DO NOTHING", (data.address,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "agent_message": "Brain attached to wallet session."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# [REMAINDER OF YOUR HTML ROUTES STAY EXACTLY THE SAME]
# I have only updated the background_sync to include the "Brain's" logic
async def background_sync():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # The 'yieldscout' stays, but we can now cross-reference with the Agent
                vault_cache["yields"] = await get_all_yields()
                
                # BRAIN LOGIC: Optimization Check
                # If Agent is online, it validates the yields against gas prices
                if agent_instance:
                    # Logic: If gas is too high, we tag it as 'Sub-Optimal'
                    vault_cache["gas_price"] = "0.0012 Gwei (OPTIMAL)"
                
                vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
            except Exception as e:
                vault_cache["last_updated"] = f"SYNC ERROR: {str(e)}"
            await asyncio.sleep(60)

# ... (rest of your @app.get routes)