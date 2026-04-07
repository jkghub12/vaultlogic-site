import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# The Terminal UI embedded as a single-file HTML/JS/Tailwind solution
# This ensures it runs perfectly on a Python server without complex build steps
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Alpha Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'JetBrains Mono', monospace; }
        @keyframes marquee {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
        }
        .animate-marquee {
            display: inline-flex;
            animation: marquee 30s linear infinite;
        }
        .scanline {
            width: 100%;
            height: 2px;
            background: rgba(255, 176, 0, 0.1);
            position: absolute;
            animation: scan 4s linear infinite;
        }
        @keyframes scan {
            0% { top: 0%; }
            100% { top: 100%; }
        }
    </style>
</head>
<body class="bg-[#020305] text-[#e2e8f0] overflow-x-hidden">

    <!-- TICKER BAR -->
    <div class="w-full bg-[#FFB000]/10 border-b border-[#FFB000]/30 py-2 overflow-hidden whitespace-nowrap">
        <div class="animate-marquee">
            <div class="flex items-center space-x-12 px-4">
                <span class="text-[#FFB000] text-[10px] font-bold">GAP_DETECTED: PATEK 5711 [+$12.4K]</span>
                <span class="text-[#00FF41] text-[10px] font-bold">ALPHA: NVIDIA H100 [+$4.3K]</span>
                <span class="text-[#FFB000] text-[10px] font-bold">GAP_DETECTED: CAT 3512 [+$15.2K]</span>
                <span class="text-[#00FF41] text-[10px] font-bold">ALPHA: BIRKIN 30 [+$8.9K]</span>
                <!-- Duplicate for seamless loop -->
                <span class="text-[#FFB000] text-[10px] font-bold">GAP_DETECTED: PATEK 5711 [+$12.4K]</span>
                <span class="text-[#00FF41] text-[10px] font-bold">ALPHA: NVIDIA H100 [+$4.3K]</span>
                <span class="text-[#FFB000] text-[10px] font-bold">GAP_DETECTED: CAT 3512 [+$15.2K]</span>
                <span class="text-[#00FF41] text-[10px] font-bold">ALPHA: BIRKIN 30 [+$8.9K]</span>
            </div>
        </div>
    </div>

    <!-- HEADER -->
    <header class="max-w-[1400px] mx-auto p-6 flex justify-between items-center border-b border-white/5">
        <div class="flex items-center space-x-4">
            <div class="w-8 h-8 bg-white rounded flex items-center justify-center">
                <div class="w-5 h-5 border-[3px] border-black"></div>
            </div>
            <div>
                <h1 class="text-xl font-black italic tracking-tighter text-white">VAULTLOGIC</h1>
                <p class="text-[8px] tracking-[0.3em] text-gray-500 uppercase">Information Superiority Terminal</p>
            </div>
        </div>
        <div class="flex items-center space-x-6 text-[10px] font-bold">
            <span class="text-[#00FF41] animate-pulse">● SYSTEM_OPTIMAL</span>
            <button class="px-4 py-2 border border-[#FFB000] text-[#FFB000] hover:bg-[#FFB000] hover:text-black transition-all">CONNECT WALLET</button>
        </div>
    </header>

    <!-- MAIN CONTENT -->
    <main class="max-w-[1400px] mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        <!-- LEFT: METRICS -->
        <div class="lg:col-span-3 space-y-6">
            <div class="bg-white/[0.02] border border-white/5 p-6">
                <p class="text-[9px] text-gray-500 font-bold mb-2">SCANNED VOLUME</p>
                <p id="counter" class="text-3xl font-black italic text-white">1,284,920</p>
                <div class="mt-4 h-1 bg-white/5">
                    <div class="h-full bg-[#FFB000] w-2/3"></div>
                </div>
            </div>

            <div class="bg-white/[0.02] border border-white/5 p-6">
                <p class="text-[9px] text-gray-500 font-bold mb-4 uppercase">Node Health</p>
                <div class="space-y-3">
                    <div class="flex justify-between text-[10px]"><span class="text-gray-400">Tokyo-1</span><span class="text-[#00FF41]">4ms</span></div>
                    <div class="flex justify-between text-[10px]"><span class="text-gray-400">London-4</span><span class="text-[#00FF41]">12ms</span></div>
                    <div class="flex justify-between text-[10px]"><span class="text-gray-400">NYC-Main</span><span class="text-[#FFB000]">28ms</span></div>
                </div>
            </div>
        </div>

        <!-- CENTER: VISUALIZER -->
        <div class="lg:col-span-6">
            <div class="aspect-video bg-[#06080c] border border-white/10 relative overflow-hidden flex items-center justify-center">
                <div class="scanline"></div>
                <div class="text-center">
                    <div class="w-48 h-48 border border-[#FFB000]/20 rounded-full flex items-center justify-center animate-[spin_20s_linear_infinite]">
                        <div class="w-32 h-32 border border-[#FFB000]/40 rounded-full"></div>
                    </div>
                    <div class="mt-8">
                        <h2 class="text-2xl font-black italic text-white">GLOBAL SCAN ACTIVE</h2>
                        <p class="text-[10px] text-gray-500 mt-2">MAPPING PRICE DISCREPANCIES IN REAL-TIME</p>
                    </div>
                </div>
            </div>
            
            <div class="mt-8 bg-white/[0.02] border border-white/5 p-4 overflow-hidden h-40 font-mono text-[10px] text-gray-400" id="log-feed">
                <div>[SYSTEM] INITIALIZING LOGISTICS_ENGINE...</div>
                <div>[SCAN] DETECTED INEFFICIENCY: SINGAPORE -> SFO [ELECTRONICS]</div>
            </div>
        </div>

        <!-- RIGHT: CALL TO ACTION -->
        <div class="lg:col-span-3 space-y-6">
            <div class="bg-[#FFB000] text-black p-6">
                <h3 class="font-black italic text-lg mb-2 uppercase">Locked Alpha</h3>
                <p class="text-[10px] font-bold leading-relaxed mb-6">Access requires institutional verification or WL spot.</p>
                <button class="w-full bg-black text-white py-3 text-[10px] font-black uppercase tracking-widest hover:bg-gray-900">
                    Apply for Access
                </button>
            </div>
            
            <div class="p-6 border border-white/5 bg-white/[0.02]">
                <p class="text-[9px] text-gray-500 font-bold mb-2 uppercase">Active Gaps</p>
                <p class="text-xl font-black text-white">$42,840.12</p>
                <p class="text-[9px] text-[#00FF41] font-bold mt-1">+12.4% TODAY</p>
            </div>
        </div>
    </main>

    <script>
        // Counter simulation
        let count = 1284920;
        setInterval(() => {
            count += Math.floor(Math.random() * 5);
            document.getElementById('counter').innerText = count.toLocaleString();
        }, 1000);

        // Log feed simulation
        const logs = [
            "[INFO] FETCHING WAREHOUSE DATA: ROTTERDAM",
            "[SCAN] LUXURY_WATCH SPREAD: +4.2%",
            "[EXEC] SIMULATING ROUTE: DXB -> HKG",
            "[ALERT] VOLATILITY SPIKE DETECTED",
            "[INFO] NODE_SYNC_COMPLETE"
        ];
        const logContainer = document.getElementById('log-feed');
        setInterval(() => {
            const newLog = document.createElement('div');
            newLog.innerText = logs[Math.floor(Math.random() * logs.length)];
            logContainer.prepend(newLog);
            if(logContainer.children.length > 8) logContainer.lastChild.remove();
        }, 2000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_CONTENT

if __name__ == "__main__":
    import os
    # Railway sets the PORT environment variable automatically
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)