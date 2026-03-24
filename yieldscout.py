import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_all_yields():
    """
    Fetches yield data from the Postgres 'yields' table 
    and formats it for the VaultLogic Command Center.
    """
    conn = None
    try:
        # Connect to your existing Railway Postgres
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Query your existing yields table
        # Adjust 'protocol', 'apy', and 'asset' names if your columns are named differently
        cur.execute("SELECT protocol, apy, asset FROM yields ORDER BY apy DESC LIMIT 5;")
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Return the list of dictionaries to main.py
        return rows

    except Exception as e:
        print(f"Scout Error: {e}")
        if conn:
            conn.close()
        # Fallback to empty list so main.py doesn't crash
        return []

# Optional: Mock data for testing if the table is currently empty
# def get_all_yields():
#     return [
#         {"protocol": "AAVE V3", "apy": "12.45", "asset": "USDC"},
#         {"protocol": "MORPHO", "apy": "9.10", "asset": "ETH"}
#     ]