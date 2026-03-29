<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultLogic | Institutional ALM Kernel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
        
        body {
            background-color: #05070a;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }

        .mono { font-family: 'JetBrains Mono', monospace; }

        .glass-panel {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .kernel-glow {
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.15);
        }

        .log-entry {
            border-left: 2px solid #334155;
            transition: all 0.2s;
        }

        .log-entry:hover {
            border-left-color: #38bdf8;
            background: rgba(56, 189, 248, 0.05);
        }

        @keyframes pulse-slow {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .status-pulse {
            animation: pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: #0f172a;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 10px;
        }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    <!-- Header Navigation -->
    <nav class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-12 gap-6">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-sky-500 rounded-lg flex items-center justify-center kernel-glow">
                <i class="fas fa-microchip text-black text-xl"></i>
            </div>
            <div>
                <h1 class="text-2xl font-bold tracking-tight">VAULTLOGIC <span class="text-sky-500 text-xs align-top ml-1 mono font-normal">v2.1-AUDIT</span></h1>
                <p class="text-xs text-slate-500 uppercase tracking-widest">Autonomous ALM Kernel</p>
            </div>
        </div>

        <div class="flex items-center gap-4">
            <div id="connectionStatus" class="glass-panel px-4 py-2 rounded-full flex items-center gap-3 border-sky-500/30">
                <span class="w-2 h-2 bg-sky-500 rounded-full status-pulse"></span>
                <span class="text-sm font-medium text-sky-400">CONNECTING TO BASE...</span>
            </div>
            <button onclick="simulateConnection()" id="connectBtn" class="bg-sky-600 hover:bg-sky-500 text-white px-6 py-2 rounded-lg font-semibold transition-all shadow-lg shadow-sky-900/20">
                AUTHENTICATE
            </button>
        </div>
    </nav>

    <!-- Main Content -->
    <main id="dashboard" class="max-w-7xl mx-auto opacity-40 transition-opacity duration-700 pointer-events-none">
        
        <!-- Top Stats Row -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="glass-panel p-6 rounded-2xl">
                <p class="text-slate-500 text-xs font-semibold mb-2 uppercase tracking-tighter">System TVL</p>
                <h2 class="text-3xl font-bold">$142.8M</h2>
                <div class="text-emerald-400 text-[10px] mt-2 flex items-center gap-1">
                    <i class="fas fa-chart-line"></i> +12.4% PERFORMANCE
                </div>
            </div>
            <div class="glass-panel p-6 rounded-2xl border-l-4 border-l-sky-500">
                <p class="text-slate-500 text-xs font-semibold mb-2 uppercase tracking-tighter">Target Yield (APY)</p>
                <h2 class="text-3xl font-bold text-sky-400">5.82%</h2>
                <p class="text-[10px] text-slate-500 mt-2 uppercase">Delta-Neutral Strategy</p>
            </div>
            <div class="glass-panel p-6 rounded-2xl">
                <p class="text-slate-500 text-xs font-semibold mb-2 uppercase tracking-tighter">Active Nodes</p>
                <div class="flex items-center gap-3">
                    <h2 class="text-3xl font-bold">12</h2>
                    <span class="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-[10px] rounded border border-emerald-500/20">OPERATIONAL</span>
                </div>
                <p class="text-[10px] text-slate-500 mt-2 uppercase tracking-tight">Distributed Execution Cluster</p>
            </div>
            <div class="glass-panel p-6 rounded-2xl">
                <p class="text-slate-500 text-xs font-semibold mb-2 uppercase tracking-tighter">Kernel Health</p>
                <h2 class="text-3xl font-bold text-emerald-400" id="kernelHealth">99.8%</h2>
                <div class="w-full bg-slate-800 h-1 mt-3 rounded-full overflow-hidden">
                    <div class="bg-emerald-500 h-full w-[99.8%] transition-all duration-1000" id="healthBar"></div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            <!-- Left Column: Controls & Allocation -->
            <div class="lg:col-span-1 space-y-6">
                <div class="glass-panel p-8 rounded-3xl relative overflow-hidden">
                    <div class="absolute top-0 right-0 p-4 opacity-10">
                        <i class="fas fa-shield-halved text-6xl"></i>
                    </div>
                    <h3 class="text-xl font-bold mb-4">Allocate Capital</h3>
                    <p class="text-sm text-slate-400 mb-8 leading-relaxed">
                        Authorize the Kernel to deploy USDC into institutional-grade liquidity ranges on the Base network.
                    </p>
                    
                    <div class="space-y-4 mb-8">
                        <div class="flex justify-between text-xs mb-1">
                            <span class="text-slate-500">Deployment Amount (USDC)</span>
                            <span class="text-sky-500 font-bold" id="amountDisplay">$500,000</span>
                        </div>
                        <input type="range" min="10000" max="5000000" step="10000" value="500000" 
                               oninput="document.getElementById('amountDisplay').innerText = '$' + parseInt(this.value).toLocaleString()"
                               class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500">
                    </div>

                    <button onclick="startAllocation()" class="w-full py-4 bg-white text-black font-bold rounded-xl hover:bg-sky-400 hover:text-white transition-all transform active:scale-95 shadow-xl shadow-white/5">
                        CONFIRM ALLOCATION
                    </button>
                    
                    <div class="mt-6 pt-6 border-t border-white/5 flex items-center justify-between">
                        <span class="text-xs text-slate-500">Vault Protocol</span>
                        <span class="text-xs font-bold text-sky-400">VL-BASE-KERNEL-01</span>
                    </div>
                </div>

                <!-- Audit/CFO Block -->
                <div class="glass-panel p-6 rounded-3xl border border-sky-500/20 bg-sky-500/5">
                    <div class="flex items-center gap-3 mb-4">
                        <i class="fas fa-file-invoice-dollar text-sky-400"></i>
                        <h4 class="font-bold">CFO Audit Trail</h4>
                    </div>
                    <p class="text-[11px] text-slate-400 mb-4 leading-snug">Generate and download an encrypted execution report containing cryptographic proofs of all ALM rebalancing events.</p>
                    <button onclick="generateReport()" class="w-full py-3 bg-slate-800 text-[11px] font-bold rounded-lg border border-slate-700 hover:bg-slate-700 hover:border-sky-500/50 transition-all flex items-center justify-center gap-2">
                        <i class="fas fa-download"></i> EXPORT AUDIT REPORT (.PDF)
                    </button>
                </div>
            </div>

            <!-- Right Column: Live Audit Logs -->
            <div class="lg:col-span-2">
                <div class="glass-panel rounded-3xl p-6 min-h-[620px] flex flex-col">
                    <div class="flex justify-between items-center mb-6">
                        <div class="flex items-center gap-3">
                            <div class="w-2 h-2 bg-emerald-500 rounded-full status-pulse"></div>
                            <h3 class="font-bold uppercase tracking-widest text-sm">Kernel Execution Logs</h3>
                        </div>
                        <div class="flex gap-2">
                            <span class="px-2 py-1 bg-slate-800/50 text-[10px] text-slate-400 rounded-md border border-white/5 mono">BASE_SEQ: #142291</span>
                            <span class="px-2 py-1 bg-slate-800/50 text-[10px] text-sky-400 rounded-md border border-sky-500/20 mono">LATENCY: 12ms</span>
                        </div>
                    </div>

                    <!-- Log Output Container -->
                    <div id="logOutput" class="flex-grow mono text-[11px] space-y-3 overflow-y-auto max-h-[480px] pr-2 custom-scrollbar">
                        <div class="log-entry p-3 rounded bg-slate-900/30">
                            <span class="text-slate-500">[SYSTEM]</span> <span class="text-sky-400">INIT:</span> VaultLogic Kernel handshaking with Base Network...
                        </div>
                        <div class="log-entry p-3 rounded bg-slate-900/30">
                            <span class="text-slate-500">[AUTH]</span> <span class="text-emerald-400">READY:</span> Waiting for wallet authentication signature...
                        </div>
                    </div>

                    <div class="mt-6 pt-4 border-t border-white/5 text-[10px] text-slate-600 flex flex-col md:flex-row justify-between items-center gap-4">
                        <p>© 2026 VaultLogic ALM • Industrial-Grade Asset-Liability Management</p>
                        <div class="flex gap-4">
                            <span class="hover:text-sky-400 cursor-pointer">DOCS</span>
                            <span class="hover:text-sky-400 cursor-pointer">WHITEPAPER</span>
                            <span class="hover:text-sky-400 cursor-pointer text-emerald-500">BASE SCAN</span>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </main>

    <!-- Success Modal -->
    <div id="successModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-sm hidden">
        <div class="glass-panel max-w-md w-full p-10 rounded-[2.5rem] text-center border-emerald-500/30 shadow-2xl shadow-emerald-500/10">
            <div class="w-20 h-20 bg-emerald-500/10 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-8 border border-emerald-500/20">
                <i class="fas fa-check text-3xl"></i>
            </div>
            <h3 class="text-2xl font-bold mb-3 text-white">Report Exported</h3>
            <p class="text-slate-400 text-sm mb-10 leading-relaxed">
                VaultLogic_Audit_Q1_2026.pdf has been encrypted and generated. All rebalancing events are cryptographically signed.
            </p>
            <button onclick="document.getElementById('successModal').classList.add('hidden')" class="w-full py-4 bg-emerald-600 text-white font-bold rounded-2xl hover:bg-emerald-500 transition-all shadow-lg shadow-emerald-900/20">
                RETURN TO TERMINAL
            </button>
        </div>
    </div>

    <script>
        const logOutput = document.getElementById('logOutput');
        const dashboard = document.getElementById('dashboard');
        const connectBtn = document.getElementById('connectBtn');
        const connectionStatus = document.getElementById('connectionStatus');

        function addLog(message, type = 'info') {
            const time = new Date().toLocaleTimeString([], { hour12: false });
            let colorClass = 'text-sky-400';
            if (type === 'warn') colorClass = 'text-amber-400';
            if (type === 'success') colorClass = 'text-emerald-400';
            if (type === 'risk') colorClass = 'text-rose-400';

            const div = document.createElement('div');
            div.className = 'log-entry p-3 rounded bg-slate-900/40 opacity-0 transform translate-y-2 transition-all duration-300';
            div.innerHTML = `<span class="text-slate-500">[${time}]</span> <span class="${colorClass} uppercase font-bold">${type}:</span> ${message}`;
            
            logOutput.prepend(div);
            // Limit logs for performance
            if (logOutput.children.length > 50) logOutput.removeChild(logOutput.lastChild);
            
            setTimeout(() => div.classList.remove('opacity-0', 'translate-y-2'), 50);
        }

        function simulateConnection() {
            connectBtn.innerText = "AUTHENTICATING...";
            connectBtn.classList.add('opacity-50', 'pointer-events-none');
            
            setTimeout(() => {
                dashboard.classList.remove('opacity-40', 'pointer-events-none');
                connectBtn.classList.add('hidden');
                connectionStatus.innerHTML = `
                    <span class="w-2 h-2 bg-emerald-500 rounded-full status-pulse"></span>
                    <span class="text-sm font-medium text-emerald-400">AUTH: 0x71...F2E</span>
                `;
                addLog('Institutional Authentication Success. Kernel handoff initiated.', 'success');
                addLog('Checking Base Protocol health: Aave V3, Morpho Blue, Aerodrome...', 'info');
                startKernelLoop();
            }, 1500);
        }

        function startKernelLoop() {
            const messages = [
                { msg: "Polling Morpho Blue pool utilization rates...", type: "info" },
                { msg: "Detected yield spread anomaly (+0.42%) on Aerodrome v3.", type: "warn" },
                { msg: "Rebalancing $1.2M USDC from Aave V3 -> Aerodrome LP.", type: "info" },
                { msg: "Verification: Delta-Neutral parameters maintained.", type: "success" },
                { msg: "Base Sequencer Batch #142295 confirmed.", type: "info" },
                { msg: "Executing Tick-Range Optimization for concentrated liquidity.", type: "info" },
                { msg: "Volatility Buffer alert: 0.12% move detected. Position safe.", type: "risk" },
                { msg: "Compounding generated fees to founder vault.", type: "success" },
                { msg: "Fetching real-time gas prices (Base: 0.001 Gwei).", type: "info" }
            ];

            // Random log generation to simulate real "Autopilot" activity
            setInterval(() => {
                if(Math.random() > 0.45) {
                    const pick = messages[Math.floor(Math.random() * messages.length)];
                    addLog(pick.msg, pick.type);
                }
            }, 4000);
        }

        function startAllocation() {
            const amount = document.getElementById('amountDisplay').innerText;
            addLog(`Requesting Capital Allocation: ${amount} USDC...`, 'info');
            setTimeout(() => {
                addLog(`Smart Contract Signature verified for ${amount}.`, 'success');
                addLog(`Kernel deploying capital into Aave-Morpho Hybrid Strategy.`, 'info');
            }, 1200);
        }

        function generateReport() {
            const modal = document.getElementById('successModal');
            modal.classList.remove('hidden');
            addLog('Exporting Full Audit Trail: VaultLogic_Audit_Q1_2026.pdf', 'success');
        }

        // Initialize Health & Stats Fluctuation
        setInterval(() => {
            const health = document.getElementById('kernelHealth');
            const hBar = document.getElementById('healthBar');
            const newVal = (99.7 + Math.random() * 0.2).toFixed(1);
            health.innerText = newVal + '%';
            hBar.style.width = newVal + '%';
        }, 5000);
    </script>
</body>
</html>