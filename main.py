import React, { useState, useEffect, useRef } from 'react';
import { Shield, Lock, Activity, Terminal, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';

const App = () => {
  // --- CORE SYSTEM STATE ---
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [walletAddress, setWalletAddress] = useState(null);
  const [isEngaged, setIsEngaged] = useState(false);
  const [allocation, setAllocation] = useState(10000);
  const [netProfit, setNetProfit] = useState(0.0000);
  const [activeVenue, setActiveVenue] = useState("IDLE");
  const [isMidnight, setIsMidnight] = useState(false);
  const [bypassOn, setBypassOn] = useState(false); // DEFAULT: ENFORCE THE FLOOR
  
  // MOCK DATA FROM SCREENSHOTS
  const MOCK_WALLET_BALANCE = 3.42; 

  // --- AUDIT LOGGING SYSTEM ---
  const [logs, setLogs] = useState([
    { id: 0, type: 'AUDIT', text: 'VAULTLOGIC V3.4-STABLE: SYSTEM READY. WAITING FOR AUTHENTICATION...', color: 'text-cyan-500' }
  ]);

  const addLog = (type, text, color = 'text-gray-400') => {
    setLogs(prev => [{ id: Date.now(), type, text, color }, ...prev].slice(0, 50));
  };

  // --- ACTIONS ---
  const connectWallet = () => {
    const mockAddr = "0X31D82103E...";
    setWalletAddress(mockAddr);
    setIsAuthenticated(true);
    addLog('AUDIT', `SESSION_OPENED: SECURE HANDSHAKE ESTABLISHED FOR ${mockAddr}`, 'text-cyan-500');
  };

  const disconnectWallet = () => {
    // SECURITY PURGE: Explicitly kill the engine and clear state
    setIsAuthenticated(false);
    setWalletAddress(null);
    setIsEngaged(false); 
    setActiveVenue("IDLE");
    setNetProfit(0);
    addLog('AUDIT', 'SESSION_CLOSED: SECURITY PURGE COMPLETED. ALL ENGINES HALTED.', 'text-cyan-500');
  };

  const initializeKernel = () => {
    if (!isAuthenticated) return;

    // RULE: REJECT IF BELOW $10,000 FLOOR (Unless Bypass is Active)
    if (!bypassOn && MOCK_WALLET_BALANCE < 10000) {
      addLog('REJECTED', `INSUFFICIENT COLLATERAL. REQ: $10,000.00 | FOUND: $${MOCK_WALLET_BALANCE.toFixed(2)}`, 'text-red-500');
      setIsEngaged(false);
      return;
    }

    setIsEngaged(true);
    setActiveVenue("AERODROME LP");
    addLog('AUDIT', `SUCCESS: ASSET ALLOCATION OF $${allocation.toLocaleString()}.00 DEPLOYED VIA COMPOUND_V3.`, 'text-emerald-400');
  };

  // --- YIELD SIMULATION (GATED) ---
  useEffect(() => {
    let interval;
    if (isEngaged && isAuthenticated) {
      interval = setInterval(() => {
        setNetProfit(prev => prev + (Math.random() * 0.0008));
        if (Math.random() > 0.95) {
          const venues = ["AAVE V3 BASE", "MORPHO BLUE", "AERODROME LP"];
          const next = venues[Math.floor(Math.random() * venues.length)];
          setActiveVenue(next);
          addLog('AUDIT', `REBALANCING: MIGRATING LIQUIDITY TO ${next}...`, 'text-purple-400');
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isEngaged, isAuthenticated]);

  return (
    <div className="min-h-screen bg-[#020305] text-[#e2e8f0] font-sans p-6 md:p-10">
      
      {/* INDUSTRIAL HEADER */}
      <header className="max-w-7xl mx-auto flex justify-between items-center mb-16">
        <div className="flex items-center gap-5">
          <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-[0_0_30px_rgba(255,255,255,0.1)]">
            <div className="w-7 h-7 border-[5px] border-black rounded-sm"></div>
          </div>
          <div>
            <h1 className="text-2xl font-black italic tracking-tighter leading-none text-white uppercase">VAULTLOGIC</h1>
            <p className="text-[10px] tracking-[0.4em] text-gray-600 font-bold mt-1 uppercase">Industrial Yield Engine</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="px-5 py-2 rounded-full border border-white/5 flex items-center gap-3 bg-[#0a0c12]">
            <div className={`w-2 h-2 rounded-full ${isAuthenticated ? 'bg-emerald-500 animate-pulse' : 'bg-gray-700'}`}></div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-gray-500 uppercase">
              {isAuthenticated ? `AUTH: ${walletAddress}` : 'LOCKED'}
            </span>
          </div>
          <button 
            onClick={isAuthenticated ? disconnectWallet : connectWallet}
            className="px-8 py-2.5 rounded-lg font-black text-[10px] uppercase tracking-[0.2em] bg-white text-black hover:bg-gray-200 transition-all"
          >
            {isAuthenticated ? 'Disconnect' : 'Authenticate'}
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto space-y-8">
        
        {/* METRICS ROW */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#06080c] border-l-2 border-cyan-500 rounded-2xl p-8 shadow-2xl">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 mb-6">Active Principal</p>
            <p className="text-5xl font-black italic tracking-tighter text-white">
                ${isEngaged ? allocation.toLocaleString() : "0"}
            </p>
          </div>
          <div className="bg-[#06080c] border-l-2 border-emerald-500 rounded-2xl p-8 shadow-2xl">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 mb-6">Net Profit (80%)</p>
            <p className="text-5xl font-black italic tracking-tighter text-emerald-400">
                ${netProfit.toFixed(4)}
            </p>
          </div>
          <div className="bg-[#06080c] border-l-2 border-purple-500 rounded-2xl p-8 shadow-2xl">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 mb-6">
                {isEngaged ? "Active Venue" : "Privacy Status"}
            </p>
            <p className="text-4xl font-black italic tracking-tighter text-purple-400 uppercase">
                {isEngaged ? activeVenue : (isMidnight ? "MIDNIGHT" : "STANDARD")}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* CONTROLLER */}
          <div className="lg:col-span-4 bg-[#06080c] border border-white/5 rounded-[32px] p-10 flex flex-col">
            <h2 className="text-[11px] font-black tracking-[0.3em] text-cyan-500 uppercase mb-10">Strategy Controller</h2>
            
            <div className="space-y-12 flex-grow">
              <div className="space-y-5">
                <div className="flex justify-between items-end">
                  <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Allocation</label>
                  <span className="text-xs font-mono font-bold text-white">${allocation.toLocaleString()}</span>
                </div>
                <input 
                  type="range" min="1000" max="100000" step="1000" value={allocation}
                  onChange={(e) => setAllocation(parseInt(e.target.value))}
                  className="w-full h-1 bg-[#1a1f26] rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
              </div>

              <div className="space-y-6">
                <div onClick={() => setBypassOn(!bypassOn)} className="flex items-center gap-4 cursor-pointer">
                  <div className={`w-5 h-5 rounded flex items-center justify-center border transition-all ${bypassOn ? 'bg-cyan-600 border-cyan-600 shadow-[0_0_10px_rgba(8,145,178,0.4)]' : 'border-gray-800'}`}>
                    {bypassOn && <CheckCircle2 size={12} className="text-white" />}
                  </div>
                  <span className={`text-[10px] font-black uppercase tracking-widest ${bypassOn ? 'text-gray-300' : 'text-gray-600'}`}>Bypass On-Chain Check</span>
                </div>

                <div onClick={() => setIsMidnight(!isMidnight)} className="flex items-center gap-4 cursor-pointer">
                  <div className={`w-5 h-5 rounded flex items-center justify-center border transition-all ${isMidnight ? 'bg-purple-600 border-purple-600 shadow-[0_0_10px_rgba(147,51,234,0.4)]' : 'border-gray-800'}`}>
                    {isMidnight && <Lock size={12} className="text-white" />}
                  </div>
                  <span className={`text-[10px] font-black uppercase tracking-widest ${isMidnight ? 'text-gray-300' : 'text-gray-600'}`}>Enable Midnight Privacy</span>
                </div>
              </div>
            </div>

            <div className="mt-12 space-y-4">
              <button 
                onClick={initializeKernel}
                disabled={!isAuthenticated}
                className={`w-full py-5 rounded-2xl font-black text-xs uppercase tracking-[0.3em] transition-all duration-300 ${
                  !isAuthenticated ? 'bg-gray-900 text-gray-700' :
                  isEngaged ? 'bg-emerald-600 text-white shadow-[0_0_30px_rgba(16,185,129,0.3)]' : 'bg-cyan-700 text-white hover:bg-cyan-600'
                }`}
              >
                {isEngaged ? 'Active' : 'Initialize Kernel'}
              </button>
              
              {isEngaged && (
                <div className="w-full py-4 px-6 bg-emerald-500/5 border border-emerald-500/20 rounded-xl text-center animate-in fade-in zoom-in duration-300">
                  <span className="text-[9px] font-black italic tracking-widest text-emerald-500 uppercase">
                    Protocol Engaged Successfully.
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* AUDIT TERMINAL */}
          <div className="lg:col-span-8 bg-[#06080c] border border-white/5 rounded-[32px] flex flex-col overflow-hidden">
            <div className="px-10 py-6 border-b border-white/5 flex justify-between items-center bg-white/[0.01]">
              <div className="flex items-center gap-3">
                <Terminal size={14} className="text-gray-600" />
                <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Infrastructure Audit</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[9px] font-mono font-bold text-gray-600 uppercase tracking-widest">Base RPC Healthy</span>
                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
              </div>
            </div>

            <div className="flex-1 p-10 font-mono text-[11px] overflow-y-auto space-y-6 max-h-[550px]">
              {logs.map((log) => (
                <div key={log.id} className="flex gap-6 border-l border-white/5 pl-6 relative">
                  {log.type === 'REJECTED' && <div className="absolute left-[-1px] top-0 bottom-0 w-[2px] bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div>}
                  <span className={`font-black shrink-0 tracking-tighter ${log.color}`}>{log.type}:</span>
                  <span className="text-gray-400 leading-relaxed uppercase tracking-wider">{log.text}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </main>
      
      {/* BG DECOR */}
      <div className="fixed bottom-0 right-0 opacity-[0.02] pointer-events-none -mb-32 -mr-32">
        <Activity size={800} />
      </div>
    </div>
  );
};

export default App;