import os
from dotenv import load_dotenv

# Load the secret keys from your .env file
load_dotenv()

def initialize_vaultlogic():
    print("--- VAULTLOGIC AGENT INITIALIZING ---")
    llc_name = os.getenv("LLC_NAME")
    print(f"Identity: {llc_name}")
    
    # Check if we have the API Key (don't print the actual key for security!)
    if os.getenv("GOOGLE_API_KEY"):
        print("Status: AI Brain Connected.")
    else:
        print("Status: AI Brain Missing API Key.")

if __name__ == "__main__":
    initialize_vaultlogic()