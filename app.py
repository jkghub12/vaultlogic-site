import os
import time
import threading
from fastapi import FastAPI
import uvicorn
from yieldscout import get_all_yields

app = FastAPI()

# Shared variable to hold latest data
current_yields = []

def active_banking_loop():
    """Runs every 60 seconds to refresh yields and save to DB"""
    global current_yields
    print("Banker Engine Started...")
    while True:
        try:
            current_yields = get_all_yields()
            print(f"Updated Yields: {current_yields}")
        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(60)

# Start the background thread
thread = threading.Thread(target=active_banking_loop, daemon=True)
thread.start()

@app.get("/")
def home():
    return {"status": "Banker is Active", "loop": "Running"}

@app.get("/api/yield")
def get_yield():
    return current_yields

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)