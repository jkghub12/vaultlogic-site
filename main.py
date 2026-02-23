import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

print("--- VAULTLOGIC AGENT HEARTBEAT (v6.0 - Stable Edition) ---")

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY missing from .env")
else:
    try:
        client = genai.Client(api_key=api_key)
        
        # Switching to the 2.5 series, which has much higher availability than the 3.0 preview
        target_model = "gemini-2.5-flash"
        
        response = client.models.generate_content(
            model=target_model, 
            contents="State 'VaultLogic Agent System: Active' and give a 1-sentence business tip for a new LLC founder."
        )
        
        print(f"Agent Response: {response.text}")
        print(f"Status: SUCCESS - Connected via {target_model}")
        
    except Exception as e:
        print(f"Status: FAILED - {e}")