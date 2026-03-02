from fastapi import FastAPI, HTTPException
from yieldscout import DeFiYieldScout
import os

app = FastAPI(title="VaultLogic Yield API")

# Initialize the scout
# We do this globally so it stays 'warm' between requests
try:
    scout = DeFiYieldScout()
except Exception as e:
    print(f"Error starting Scout: {e}")
    scout = None

@app.get("/api/yield")
async def get_yield():
    """Endpoint that returns the best yield option as JSON"""
    if not scout:
        raise HTTPException(status_code=500, detail="Yield Scout not initialized")
    
    try:
        data = scout.get_best_yield()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "active", "version": "1.0.0"}