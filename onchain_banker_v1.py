import os
import uvicorn
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3
from dotenv import load_dotenv

# 1. Load the "hidden" environment variables
load_dotenv()

app = FastAPI()

# Enable CORS so your website (ValueLogic.dev) can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configuration - Pulling from your .env file
W3_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(W3_RPC))

# This looks for BANKER_VAULT_ADDRESS in your .env or Railway settings
VAULT_ENV = os.getenv("BANKER_VAULT_ADDRESS")
if not VAULT_ENV:
    # Fallback to your address if .env is missing during local debug
    VAULT_ENV = "0x456Eb50604f0C240A1F0C9d661338561Cc601889"

BANKER_VAULT = Web3.to_checksum_address(VAULT_ENV)
REQUIRED_AMOUNT_ETH = "0.0001"

async def fetch_live_base_yields():
    """The Brains: Fetches real-time yields from Base Chain via DeFiLlama."""
    try:
        async with httpx.AsyncClient() as client:
            url = "https://yields.llama.fi/pools"
            response = await client.get(url, timeout=10.0)
            all_pools = response.json().get('data', [])
            
            # Filter for Base Chain and pools with decent liquidity ($100k+)
            base_pools = [p for p in all_pools if p.get('chain') == 'Base' and p.get('tvlUsd', 0) > 100000]
            
            # Sort by APY (highest first)
            base_pools.sort(key=lambda x: x.get('apy', 0), reverse=True)
            
            # Return top 3 results
            return [
                {
                    "protocol": p['project'],
                    "asset": p['symbol'],
                    "apy": f"{p['apy']:.2f}%",
                    "tvl": f"${p['tvlUsd']/1e6:.1f}M",
                    "risk_level": "High" if p.get('apy', 0) > 50 else "Standard"
                } for p in base_pools[:3]
            ]
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return [{"error": "Could not fetch live data. Using cached strategy: High-yield stables on Base."}]

@app.get("/consult")
async def consult(query: str, request: Request):
    # Check for the payment proof in the headers
    proof = request.headers.get("x402-payment-proof")
    
    # If no proof, issue the "Payment Required" challenge
    if not proof:
        return JSONResponse(
            status_code=402,
            content={
                "reason": "Vaultlogic Yield Scout Access",
                "amount_eth": REQUIRED_AMOUNT_ETH,
                "pay_to": BANKER_VAULT,
                "network": "Base Mainnet"
            }
        )

    # 3. VERIFICATION: The Guard checks the blockchain
    try:
        tx = w3.eth.get_transaction(proof)
        
        # Check if the money went to YOUR vault
        if tx['to'].lower() != BANKER_VAULT.lower():
            raise HTTPException(status_code=402, detail="Payment sent to wrong address.")
            
        # Check if they paid enough
        if tx['value'] < w3.to_wei(REQUIRED_AMOUNT_ETH, 'ether'):
            raise HTTPException(status_code=402, detail="Insufficient payment amount.")
            
    except Exception:
        # If transaction isn't found yet or is invalid
        raise HTTPException(status_code=402, detail="Transaction not confirmed or invalid.")

    # 4. SUCCESS: Release the "Alpha"
    print(f"💰 SUCCESS: Payment verified for TX {proof[:10]}... Releasing data.")
    live_data = await fetch_live_base_yields()
    
    return {
        "status": "PAID",
        "service": "Vaultlogic Yield Scout",
        "timestamp": "Real-Time",
        "top_opportunities": live_data,
        "vault_received_at": BANKER_VAULT,
        "disclaimer": "DeFi yields are volatile. Risk assessed by Vaultlogic AI."
    }

if __name__ == "__main__":
    # Use 0.0.0.0 for Railway/Cloud compatibility
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)