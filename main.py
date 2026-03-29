import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from web3 import Web3

app = FastAPI()

# Configuration
BASE_RPC_URL = "https://mainnet.base.org"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

vault_cache = {
    "yields": [], 
    "metrics": {"tvl": "$142.8M", "health": "99.8%", "active_nodes": 12, "last_rebalance": "14m ago"}
}
system_logs = ["VaultLogic Kernel v2.5.8 Online", "Status: Ready for Capital Allocation."]

class WalletConnect(BaseModel):
    address: str

class EngineInit(BaseModel):
    address: str
    amount: float

def add_log(msg):
    global system_logs
    system_logs.append(msg)
    if len(system_logs) > 50: system_logs.pop(0)

@app.post("/verify-balance")
async def verify_balance(data: EngineInit):
    """Hard Gate: Check on-chain balance before allowing initiation."""
    try:
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        raw_balance = contract.functions.balanceOf(Web3.to_checksum_address(data.address)).call()
        actual_balance = raw_balance / 10**6
        
        if data.amount > actual_balance:
            return {"status": "error", "message": f"Insufficient Funds. Found {actual_balance:,.2f} USDC.", "balance": actual_balance}
        return {"status": "success", "balance": actual_balance}
    except Exception as e:
        return {"status": "error", "message": "Network Timeout. Try again."}

@app.post("/start-engine")
async def start_engine(data: EngineInit):
    from engine import run_alm_engine
    add_log(f"INIT: Spawning ALM Kernel for {data.address[:10]} with ${data.amount:,.2f} USDC...")
    asyncio.create_task(run_alm_engine(data.address, log_callback=add_log))
    return {"status": "running"}

@app.get("/logs")
async def get_logs():
    return {"logs": system_logs}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Fixed Logo URL: Using raw.githubusercontent.com for direct image rendering
    logo_url = "https://raw.githubusercontent.com/VaultLogic/vaultlogic-site/main/VLlogo.png"
    
    return f"""
    <html>
        <head>
            <title>VaultLogic | Institutional ALM</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <script type="module">
                import {{ createAppKit }} from 'https://esm.sh/@reown/appkit'
                import {{ Ethers5Adapter }} from 'https://esm.sh/@reown/appkit-adapter-ethers5'
                import {{ base }} from 'https://esm.sh/@reown/appkit/networks'

                const modal = createAppKit({{
                    adapters: [new Ethers5Adapter()],
                    networks: [base],
                    projectId: '2b936cf692d84ae6da1ba91950c96420',
                    themeMode: 'light',
                    themeVariables: {{ '--w3m-accent': '#0f172a', '--w3m-z-index': '10001' }}
                }});
                window.modal = modal;
                modal.subscribeAccount(state => {{ 
                    if(state.isConnected) {{ window.userAddress = state.address; setupWalletUI(state.address); }}
                    else {{ resetUI(); }}
                }});
            </script>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700;800&family=JetBrains+Mono&display=swap');
                :root {{ --primary: #0f172a; --accent: #2563eb; --border: #e2e8f0; --danger: #ef4444; --success: #22c55e; }}
                body {{ background:#f1f5f9; color:var(--primary); font-family: 'Public Sans', sans-serif; margin:0; overflow-x: hidden; }}
                
                .top-nav {{ background: white; border-bottom: 1px solid var(--border); padding: 0 40px; height: 70px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
                .logo {{ display: flex; align-items: center; gap: 10px; text-decoration: none; font-weight: 800; color: var(--primary); font-size: 18px; }}
                .logo img {{ height: 32px; width: auto; display: block; }}
                
                .btn-connect {{ background: var(--primary); color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; }}
                #control-panel {{ max-width: 1200px; margin: 20px auto; padding: 25px; background: white; border: 1px solid var(--border); border-radius: 12px; display: none; justify-content: space-between; align-items: center; }}
                
                .btn-start {{ background: var(--success); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 800; cursor: pointer; }}
                
                .modal-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.9); z-index:10000; justify-content:center; align-items:center; backdrop-filter: blur(4px); }}
                .modal-content {{ background: white; padding: 30px; border-radius: 16px; width: 90%; max-width: 400px; position: relative; }}
                
                #log-stream {{ padding: 15px; height: 180px; overflow-y: auto; font-family: 'JetBrains Mono'; font-size: 11px; color: #34d399; background: #0f172a; border-radius: 8px; }}
                .log-entry {{ margin-bottom: 4px; border-bottom: 1px solid #1e293b; padding-bottom: 2px; }}
                .error-msg {{ color: var(--danger); font-size: 11px; font-weight: 700; margin-top: 8px; display: none; }}
            </style>
        </head>
        <body>
            <nav class="top-nav">
                <a href="/" class="logo">
                    <img src="{logo_url}" alt="VaultLogic Logo" onerror="this.src='https://via.placeholder.com/32?text=VL'">
                    <span>VAULTLOGIC</span>
                </a>
                <div id="walletDisplay" style="display:none; text-align:right;">
                    <span id="addrText" style="font-family:'JetBrains Mono'; font-size:12px; font-weight:800;"></span>
                    <br><a onclick="window.modal.disconnect()" style="color:var(--danger); font-size:10px; cursor:pointer;">DISCONNECT</a>
                </div>
                <button id="connectBtn" class="btn-connect" onclick="window.modal.open()">CONNECT WALLET</button>
            </nav>

            <div id="control-panel">
                <div>
                    <div style="font-size: 14px; font-weight: 800;">ALM KERNEL: <span id="engine-status-text" style="color:#64748b">STANDBY</span></div>
                    <div id="session-info" style="font-size: 11px; color: #64748b;">Ready for deployment on Base.</div>
                </div>
                <button id="btnInitiate" class="btn-start" onclick="toggleModal('allocationModal', true)">INITIATE ENGINE</button>
            </div>

            <div id="allocationModal" class="modal-overlay">
                <div class="modal-content">
                    <h2 style="margin:0 0 10px 0;">Allocation</h2>
                    <p style="font-size:12px; color:#64748b;">Enter USDC amount to manage. System will verify your on-chain balance.</p>
                    <input type="number" id="usdcAmount" placeholder="0.00" style="width:100%; padding:15px; font-size:24px; font-weight:800; border:2px solid #e2e8f0; border-radius:12px; outline:none;">
                    <div id="allocError" class="error-msg"></div>
                    <button id="confirmBtn" onclick="confirmInitiate()" class="btn-start" style="width:100%; margin-top:20px;">VERIFY & DEPLOY</button>
                </div>
            </div>

            <div style="max-width:1200px; margin:20px auto; padding:0 20px;">
                <div style="background:#0f172a; border-radius:12px; overflow:hidden;">
                    <div style="padding:10px 15px; color:#64748b; font-size:10px; font-weight:800; border-bottom:1px solid #1e293b;">EXECUTION LOG</div>
                    <div id="log-stream"></div>
                </div>
            </div>

            <script>
                function toggleModal(id, show) {{ document.getElementById(id).style.display = show ? 'flex' : 'none'; }}

                function setupWalletUI(address) {{
                    document.getElementById('connectBtn').style.display = 'none';
                    document.getElementById('walletDisplay').style.display = 'block';
                    document.getElementById('control-panel').style.display = 'flex';
                    document.getElementById('addrText').innerText = address.substring(0,6) + "..." + address.substring(38);
                }}

                function resetUI() {{
                    document.getElementById('connectBtn').style.display = 'block';
                    document.getElementById('walletDisplay').style.display = 'none';
                    document.getElementById('control-panel').style.display = 'none';
                }}

                async function confirmInitiate() {{
                    const amt = document.getElementById('usdcAmount').value;
                    const errDiv = document.getElementById('allocError');
                    const cBtn = document.getElementById('confirmBtn');
                    
                    errDiv.style.display = 'none';
                    cBtn.innerText = "AUDITING ON-CHAIN...";
                    cBtn.disabled = true;

                    // Step 1: Verification Gate
                    const vRes = await fetch("/verify-balance", {{
                        method: "POST",
                        headers: {{"Content-Type": "application/json"}},
                        body: JSON.stringify({{ address: window.userAddress, amount: parseFloat(amt) }})
                    }});
                    const vData = await vRes.json();

                    if(vData.status === "error") {{
                        errDiv.innerText = vData.message;
                        errDiv.style.display = 'block';
                        cBtn.innerText = "VERIFY & DEPLOY";
                        cBtn.disabled = false;
                        return;
                    }}

                    // Step 2: Start Engine
                    await fetch("/start-engine", {{
                        method: "POST",
                        headers: {{"Content-Type": "application/json"}},
                        body: JSON.stringify({{ address: window.userAddress, amount: parseFloat(amt) }})
                    }});
                    
                    toggleModal('allocationModal', false);
                    document.getElementById('engine-status-text').innerText = "RUNNING";
                    document.getElementById('engine-status-text').style.color = "#22c55e";
                    document.getElementById('btnInitiate').style.display = 'none';
                }}

                setInterval(async () => {{
                    try {{
                        const res = await fetch('/logs');
                        const data = await res.json();
                        const stream = document.getElementById('log-stream');
                        // Clean logs: No redundant browser timestamps
                        stream.innerHTML = data.logs.map(l => `<div class="log-entry"><span style="color:#10b981;">></span> ${{l}}</div>`).reverse().join('');
                    }} catch(e) {{}}
                }}, 2000);
            </script>
        </body>
    </html>
    """