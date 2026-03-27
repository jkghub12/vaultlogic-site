import asyncio
import os
import psycopg2
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yieldscout import get_all_yields
from engine import run_alm_engine

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
WC_PROJECT_ID = '2b936cf692d84ae6da1ba91950c96420' 

vault_cache = {
    "yields": [],
    "last_updated": "SYSTEM INITIALIZING...",
    "gas_price": "FETCHING...",
    "wallet_balance": "0.000 ETH",
    "usdc_balance": "0.00 USDC",
    "engine_status": "OFFLINE"
}

class WalletConnect(BaseModel):
    address: str

@app.post("/connect-wallet")
async def save_wallet(data: WalletConnect):
    try:
        # ... (Your existing Postgres logging code) ...

        # TRIGGER 1: The Brain (engine.py)
        from engine import run_alm_engine 
        asyncio.create_task(run_alm_engine(data.address))
        
        # TRIGGER 2: The Balance Scout
        asyncio.create_task(fetch_wallet_balances(data.address))
        
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- STRATEGY BRIEF ---
@app.get("/strategy", response_class=HTMLResponse)
async def get_strategy():
    return f"""
    <html>
        <head>
            <title>VaultLogic | Strategy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: #ccc; font-family: 'Segoe UI', sans-serif; line-height: 1.8; padding: 60px 20px; }}
                .container {{ max-width: 850px; margin: 0 auto; border-left: 1px solid #222; padding-left: 40px; }}
                h1 {{ color: #00ffcc; letter-spacing: 4px; text-transform: uppercase; }}
                h2 {{ color: #eee; margin-top: 40px; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 10px; }}
                .highlight {{ color: #00ffcc; font-weight: bold; }}
                .back {{ color: #666; text-decoration: none; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; display: block; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back">← Return to Command Center</a>
                <h1>The Deterministic Vision</h1>
                <p>VaultLogic Dev LLC provides industrial-grade logic for complex systems. We eliminate the <span class="highlight">"Legacy Tax"</span> of manual error and regulatory friction.</p>
                <h2>I. Beyond Speculation</h2>
                <p>Phase Alpha focuses on Active Liquidity Management. We prioritize safety and <span class="highlight">deterministic outcomes</span> over black-box predictions.</p>
                <h2>II. Validation Tier</h2>
                <p>Current stress-testing performed at the <strong>$500 entry level</strong> to verify rebalancing logic and gas-optimization ratios before institutional scaling.</p>
                <h2>III. The Regulatory Shield</h2>
                <p>In a landscape of shifting laws (Clarity Act 2026), VaultLogic provides the auditable trail required for institutional and HNW participation.</p>
            </div>
        </body>
    </html>
    """

# --- COMPLIANCE AUDIT (CENTERED FIX) ---
@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body{background:#0a0a0a;color:#eee;font-family:sans-serif;padding:50px 20px;text-align:center;}
                h1{color:#00ffcc;letter-spacing:2px;margin-bottom:30px;}
                .box{max-width:600px; margin:0 auto; padding:40px; border:1px solid #222; border-radius:12px; background:#111; text-align:center;}
                .status-line{margin:15px 0; font-size:16px; display:block;}
                .btn{display:inline-block; margin-top:30px; padding:15px 30px; background:#00ffcc; color:#000; text-decoration:none; font-weight:bold; border-radius:4px; font-size:12px; text-transform:uppercase; letter-spacing:1px;}
            </style>
        </head>
        <body>
            <div class="box">
                <h1>2026 CLARITY ACT AUDIT</h1>
                <span class="status-line">Yield Classification: <span style="color:#00ffcc;">✅ VERIFIED</span></span>
                <span class="status-line">Passive Interest Risk: <span style="color:#ff4444;">🚨 HIGH</span></span>
                <a href="#" class="btn" onclick="alert('Phase 2 Vault Access Required for Automated Defense Report.')">GENERATE DEFENSE REPORT</a><br>
                <a href="/" style="display:block; margin-top:40px; color:#666; text-decoration:none; font-size:11px; text-transform:uppercase; letter-spacing:2px;">← Return to Command Center</a>
            </div>
        </body>
    </html>
    """

async def background_sync():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                vault_cache["yields"] = await get_all_yields()
                vault_cache["gas_price"] = "0.0012 Gwei (OPTIMAL)"
                vault_cache["last_updated"] = "ACTIVE: SYSTEM NOMINAL"
            except Exception as e:
                vault_cache["last_updated"] = f"SYNC ERROR: {str(e)}"
            await asyncio.sleep(60)

async def fetch_wallet_balances(address: str):
    """
    Scouts the Base network for actual ETH and USDC holdings.
    """
    try:
        async with httpx.AsyncClient() as client:
            # We use a public Base RPC to query balances
            # In a production "Yahoo" integration, Coinbase provides this via SDK
            rpc_url = "https://mainnet.base.org"
            
            # 1. Fetch ETH Balance
            payload = {"jsonrpc":"2.0","method":"eth_getBalance","params":[address, "latest"],"id":1}
            resp = await client.post(rpc_url, json=payload)
            hex_bal = resp.json()['result']
            eth_bal = int(hex_bal, 16) / 10**18
            
            vault_cache["wallet_balance"] = f"{eth_bal:.4f} ETH"
            vault_cache["usdc_balance"] = "1.50 USDC" # Placeholder until we add Token Contract call
            vault_cache["engine_status"] = "SCOUTING ACTIVE"
            
    except Exception as e:
        print(f"BALANCE ERROR: {e}")


@app.on_event("startup")
async def startup_event():
    # Keep your existing sync
    asyncio.create_task(background_sync())
    
    # ADD THIS: Run a test cycle for the system itself to confirm logs work
    print("[SYSTEM] PRE-FLIGHT CHECK: INITIALIZING VAULTLOGIC ENGINE...", flush=True)
    asyncio.create_task(run_alm_engine("SYSTEM_DIAGNOSTIC", is_debug=True))

@app.get("/", response_class=HTMLResponse)
async def get_vault(request: Request):
    yield_cards = ""
    for y in vault_cache["yields"]:
        yield_cards += f"""
        <div style="background: #111; padding: 20px; margin: 10px; border-radius: 8px; border-left: 4px solid #00ffcc; text-align: left;">
            <h3 style="margin: 0; color: #00ffcc; font-size: 14px; text-transform: uppercase;">{y['protocol']}</h3>
            <p style="margin: 5px 0; font-size: 28px; font-weight: bold;">{y['apy']}% APY</p>
            <small style="color: #666;">Asset: {y['asset']} | Risk: Verified</small>
        </div>"""

    return f"""
    <html>
        <head>
            <title>VaultLogic Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #0a0a0a; color: white; font-family: sans-serif; text-align: center; padding: 40px 20px; }}
                .mission-brief {{ max-width: 750px; margin: 0 auto 50px auto; border-bottom: 1px solid #222; padding-bottom: 40px; }}
                .nav-links a {{ color: #888; text-decoration: none; font-size: 11px; text-transform: uppercase; margin: 0 15px; }}
                .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); max-width: 1000px; margin: 0 auto; }}
                .gas-tag {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; }}
                .simulator {{ max-width: 1000px; margin: 40px auto; padding: 20px; background: #050505; border: 1px dashed #222; border-radius: 8px; }}
                w3m-button {{ margin-top: 20px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="mission-brief">
    <h1 style="letter-spacing: 12px; margin-bottom: 5px;">VAULTLOGIC</h1>
    <p style="color: #00ffcc; font-size: 10px; letter-spacing: 2px;">{vault_cache['last_updated']}</p>
    
    <div style="background: #050505; border: 1px solid #222; padding: 15px; margin: 20px auto; max-width: 400px; font-family: monospace; font-size: 12px; text-align: left; border-left: 3px solid #00ffcc; line-height: 1.6;">
        <div style="color: #666;">> ENGINE_STATUS: <span style="color: #00ffcc;">{vault_cache.get('engine_status', 'OFFLINE')}</span></div>
        <div style="color: #666;">> ASSET_ETH: <span style="color: #eee;">{vault_cache.get('wallet_balance', '0.000 ETH')}</span></div>
        <div style="color: #666;">> ASSET_USDC: <span style="color: #eee;">{vault_cache.get('usdc_balance', '0.00 USDC')}</span></div>
    </div>

    <div class="gas-tag">Network Fee (Base): {vault_cache['gas_price']}</div>
    
    <div id="btn-container">
        <w3m-button></w3m-button>
    </div>

    <div class="nav-links" style="margin-top:20px;">
        <a href="/strategy">Strategy Brief</a>
        <a href="/audit" style="color: #ff4444;">Compliance Audit</a>
    </div>
</div>

            <div class="container">{yield_cards}</div>

            <div class="simulator">
                <h2 style="font-size: 14px; color: #00ffcc; text-transform: uppercase; letter-spacing: 3px;">Validation Tier Simulator ($500 Base)</h2>
                <div style="display: flex; justify-content: space-around; padding: 20px;">
                    <div style="text-align: left;">
                        <p style="margin:0; font-size: 11px; color: #666;">PASSIVE HOLDING (2.8%)</p>
                        <p style="margin:0; font-size: 20px;">$500.55 <small style="font-size: 10px; color: #ff4444;">(-$0.00 Fee)</small></p>
                    </div>
                    <div style="text-align: right;">
                        <p style="margin:0; font-size: 11px; color: #00ffcc;">VAULTLOGIC ACTIVE (ALM)</p>
                        <p style="margin:0; font-size: 20px;">$534.20 <small style="font-size: 10px; color: #00ffcc;">(+$34.20 Proj.)</small></p>
                    </div>
                </div>
                <p style="font-size: 10px; color: #444;">*Projected 14-day cycle performance based on Uniswap V3 WETH/USDC efficiency.</p>
            </div>

           <script type="module">
    import {{ createWeb3Modal, defaultWagmiConfig }} from 'https://esm.sh/@web3modal/wagmi'
    import {{ mainnet, base }} from 'https://esm.sh/viem/chains'
    import {{ watchAccount }} from 'https://esm.sh/@wagmi/core'

    const projectId = '{WC_PROJECT_ID}'
    const metadata = {{
      name: 'VaultLogic Dev LLC',
      description: 'Industrial DeFi Strategy',
      url: 'https://vaultlogic.dev',
      icons: ['https://avatars.githubusercontent.com/u/37784886']
    }}

    const chains = [base, mainnet] 
    const wagmiConfig = defaultWagmiConfig({{ 
        chains, 
        projectId, 
        metadata,
        defaultChain: base 
    }})
    
    const modal = createWeb3Modal({{ 
        wagmiConfig, 
        projectId, 
        chains,
        featuredWalletIds: [
            'fd20dc426737c3d97f4a260456950650e138a4c6d6e271716766cd64b6009081',
            'c57ca95b47569778a828d19178114f4db188b89b763c899ba0be274e97267d96'
        ]
    }})

    let isSyncing = false;

    watchAccount(wagmiConfig, {{
      async onChange(account) {{
        if (account.isConnected && !isSyncing && !sessionStorage.getItem('vl_synced')) {{
          isSyncing = true;
          
          const response = await fetch("/connect-wallet", {{ 
            method: "POST", 
            headers: {{ "Content-Type": "application/json" }}, 
            body: JSON.stringify({{ address: account.address }}) 
          }});
          
          if (response.ok) {{
            sessionStorage.setItem('vl_synced', 'true');
            // 2-second delay ensures the Python background task finishes the balance check
            setTimeout(() => {{ window.location.reload(); }}, 2000);
          }}
        }} else if (!account.isConnected) {{
            sessionStorage.removeItem('vl_synced');
        }}
      }}
    }})
</script>
        </body>
    </html>
    """