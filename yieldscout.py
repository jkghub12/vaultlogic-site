import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_all_yields():
    """
    Fetches yield data from Postgres. 
    Automatically creates the table if it was deleted.
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # 1. Ensure the yields table exists so we don't get the "Relation does not exist" error
        cur.execute("""
            CREATE TABLE IF NOT EXISTS yields (
                id SERIAL PRIMARY KEY,
                protocol TEXT,
                apy TEXT,
                asset TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

        # 2. Check if the table is empty. If it is, insert a few "Starter" rows for your demo.
        cur.execute("SELECT COUNT(*) FROM yields;")
        if cur.fetchone()['count'] == 0:
            cur.execute("""
                INSERT INTO yields (protocol, apy, asset) VALUES 
                ('AAVE V3 (Base)', '12.4', 'USDC'),
                ('UNISWAP V3', '18.2', 'ETH/USDC'),
                ('MORPHO BLUE', '9.5', 'WETH');
            """)
            conn.commit()

        # 3. Now pull the data for main.py
        cur.execute("SELECT protocol, apy, asset FROM yields ORDER BY apy DESC LIMIT 5;")
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        return rows

    except Exception as e:
        print(f"Scout Error: {e}")
        if conn:
            conn.close()
        return []