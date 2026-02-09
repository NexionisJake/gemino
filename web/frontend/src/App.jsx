import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import StatusOrb from './components/StatusOrb';
import ActivityLog from './components/ActivityLog';
import VulnerabilityReport from './components/VulnerabilityReport';

// Initialize Socket.IO connection
const socket = io('http://localhost:8000', {
  transports: ['websocket', 'polling'], // Fallback options
});

function App() {
  const [status, setStatus] = useState('active'); // active, warning, danger
  const [logs, setLogs] = useState([]);
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [isWatching, setIsWatching] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  useEffect(() => {
    // Socket Event Listeners
    socket.on('connect', () => {
      addLog('System connected to Argus Neural Core.', 'success');
    });

    socket.on('disconnect', () => {
      addLog('Connection lost. Neural Link severed.', 'error');
      setStatus('warning');
    });

    socket.on('log', (data) => {
      addLog(data.message, data.type || 'info');
    });

    socket.on('vulnerability_update', (data) => {
      setVulnerabilities(prev => {
        // Remove existing vulnerabilities for this file to avoid duplicates
        const filtered = prev.filter(v => v.file !== data.file);
        return [...filtered, ...data.vulnerabilities.map(v => ({ ...v, file: data.file }))];
      });
      if (data.vulnerabilities.length > 0) {
        setStatus('danger');
      } else {
        // Check if any other files have vulnerabilities
        setStatus(prev => {
          // simple logic: if we just cleared a file, maybe we are safe? 
          // In reality, we'd need to track all files. For now, reset to active if clean.
          return 'active';
        });
      }
    });

    // Cleanup
    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('log');
      socket.off('vulnerability_update');
    };
  }, []);

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, { timestamp: Date.now(), message, type }].slice(-50)); // Keep last 50 logs
  };

  const toggleWatch = async () => {
    try {
      const endpoint = isWatching ? '/api/stop_watch' : '/api/start_watch';
      const res = await fetch(`http://localhost:8000${endpoint}`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'started') {
        setIsWatching(true);
        setStatus('active');
        addLog(`Started watching ${data.target}`, 'success');
      } else if (data.status === 'stopped') {
        setIsWatching(false);
        setStatus('warning'); // Idle
        setVulnerabilities([]); // Clear vulnerabilities when stopping watch
        addLog('Stopped watching.', 'warning');
      }
    } catch (e) {
      addLog(`Error toggling watch: ${e.message}`, 'error');
    }
  };

  const handleVibeCheck = async () => {
    addLog('Initiating Vibe Check...', 'info');
    try {
      await fetch('http://localhost:8000/api/vibe_check', { method: 'POST' });
    } catch (e) {
      addLog(`Vibe Check failed: ${e.message}`, 'error');
    }
  };

  const toggleConfig = () => {
    setShowConfig(!showConfig);
    addLog(showConfig ? 'Config panel closed.' : 'Config panel opened.', 'info');
  };

  // Mock Data for Visualization (Remove in production integration)
  const loadMockData = () => {
    setStatus('danger');
    setVulnerabilities([
      { type: 'SQL Injection', file: 'auth/login.py', line: 42, description: 'Unsanitized input detected in query builder.' },
      { type: 'Hardcoded Secret', file: 'config/aws.py', line: 12, description: 'AWS Secret Key found in plaintext.' },
    ]);
    addLog('CRITICAL THREAT DETECTED via manual sweep.', 'error');
  };

  return (
    <div className="min-h-screen text-text-main font-inter p-8 flex flex-col gap-8 selection:bg-primary-neon selection:text-white relative overflow-hidden">
      {/* Mesh Gradient Overlay - reinforcing the CSS background */}
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary-violet/20 via-bg-void/0 to-bg-void/0 opacity-50 z-0"></div>

      {/* Config Overlay */}
      {showConfig && (
        <div className="absolute inset-0 bg-bg-void/80 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="glass-panel p-8 w-[28rem] flex flex-col gap-6 shadow-2xl shadow-primary-violet/20 border-primary-violet/20">
            <h3 className="font-rajdhani font-bold text-2xl text-white tracking-wide border-b border-white/5 pb-4 flex items-center gap-3">
              <span className="text-primary-neon">⚙</span> SYSTEM CONFIGURATION
            </h3>
            <div className="space-y-3">
              <label className="text-xs font-semibold text-text-dim tracking-wider uppercase">Active Persona</label>
              <div className="relative">
                <select className="w-full bg-bg-panel/50 border border-white/10 rounded-lg p-3 text-sm text-white outline-none focus:border-primary-neon focus:ring-1 focus:ring-primary-neon transition-all appearance-none cursor-pointer hover:bg-white/5">
                  <option>Standard Protocol</option>
                  <option>Cyber-Pirate Mode</option>
                  <option>Corporate Executive</option>
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-dim pointer-events-none">▼</div>
              </div>
            </div>
            <div className="space-y-3">
              <label className="text-xs font-semibold text-text-dim tracking-wider uppercase">Target Directory</label>
              <input type="text" value="target_code" disabled className="w-full bg-bg-panel/50 border border-white/10 rounded-lg p-3 text-sm text-text-dim cursor-not-allowed opacity-70" />
            </div>
            <button onClick={toggleConfig} className="mt-4 w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-all font-medium tracking-wide hover:border-white/20 hover:shadow-lg hover:shadow-white/5 active:scale-[0.98]">
              DISMISS
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="flex justify-between items-center z-10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-transparent flex items-center justify-center">
            <img src="/logo.png" alt="Argus Logo" className="w-full h-full object-contain filter drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
          </div>
          <div>
            <h1 className="text-3xl font-rajdhani font-bold tracking-tight text-white">
              ARGUS
            </h1>
            <p className="text-[10px] font-mono text-primary-neon tracking-[0.4em] uppercase opacity-90">
              Neural Security Interface
            </p>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          <button onClick={loadMockData} className="px-5 py-2 border border-primary-violet/30 text-primary-violet hover:bg-primary-violet hover:text-white transition-all font-mono text-xs font-medium tracking-wider rounded-lg hover:shadow-lg hover:shadow-primary-violet/20 active:scale-95">
            [MOCK_DATA]
          </button>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${socket.connected ? 'border-status-success/30 bg-status-success/5' : 'border-status-danger/30 bg-status-danger/5'}`}>
            <span className={`w-2 h-2 rounded-full ${socket.connected ? 'bg-status-success shadow-[0_0_8px_currentColor]' : 'bg-status-danger shadow-[0_0_8px_currentColor]'}`}></span>
            <span className={`text-[10px] font-mono font-bold tracking-wider ${socket.connected ? 'text-status-success' : 'text-status-danger'}`}>
              {socket.connected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 z-10 h-[650px]">
        {/* Left Panel: System Status */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <div className="glass-panel p-8 flex-1 flex flex-col items-center justify-center relative overflow-hidden group border-white/5">
            <div className="absolute inset-0 bg-gradient-to-b from-primary-neon/5 to-transparent opacity-0 group-hover:opacity-100 transition-duration-700"></div>
            <h3 className="text-text-dim font-rajdhani font-bold tracking-[0.2em] text-xs mb-8 absolute top-6">SYSTEM ENTROPY</h3>
            <StatusOrb status={status} />
            <div className="grid grid-cols-2 gap-8 mt-12 w-full">
              <div className="text-center p-4 rounded-2xl bg-white/5 border border-white/5 group-hover:border-primary-neon/20 transition-colors">
                <div className={`text-2xl font-rajdhani font-bold ${isWatching ? 'text-status-success drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'text-text-dim'}`}>{isWatching ? 'ACTIVE' : 'IDLE'}</div>
                <div className="text-[10px] font-mono text-text-dim mt-1 uppercase tracking-wider">Monitor</div>
              </div>
              <div className="text-center p-4 rounded-2xl bg-white/5 border border-white/5 group-hover:border-primary-violet/20 transition-colors">
                <div className="text-2xl font-rajdhani font-bold text-primary-neon drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]">12ms</div>
                <div className="text-[10px] font-mono text-text-dim mt-1 uppercase tracking-wider">Latency</div>
              </div>
            </div>
          </div>
        </div>

        {/* Center Panel: Vulnerabilities */}
        <div className="lg:col-span-6 glass-panel p-1 relative overflow-hidden flex flex-col shadow-2xl shadow-black/50 border-white/10">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary-neon/50 to-transparent opacity-50"></div>
          <VulnerabilityReport vulnerabilities={vulnerabilities} />
        </div>

        {/* Right Panel: Controls / Quick Actions */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <div className="glass-panel p-8 flex-1 flex flex-col">
            <h3 className="text-white font-rajdhani font-bold tracking-wider mb-6 flex items-center gap-2">
              <span className="w-1 h-4 bg-primary-accent rounded-full"></span>
              COMMAND CENTER
            </h3>
            <div className="space-y-4 flex-1">
              <button
                onClick={toggleWatch}
                className={`w-full py-4 px-6 border-2 rounded-xl transition-all flex items-center justify-between group active:scale-[0.98] ${isWatching ? 'bg-status-danger/10 border-status-danger/50 text-status-danger hover:bg-status-danger/20 shadow-lg shadow-status-danger/10' : 'bg-primary-neon/10 border-primary-neon/50 text-primary-neon hover:bg-primary-neon/20 shadow-lg shadow-primary-neon/10'}`}
              >
                <div className="flex flex-col items-start">
                  <span className="font-bold text-sm tracking-wide">{isWatching ? 'TERMINATE WATCH' : 'INITIALIZE WATCH'}</span>
                  <span className="text-[10px] opacity-70 font-mono">{isWatching ? 'Stop monitoring target' : 'Begin file surveillance'}</span>
                </div>
                <span className={`text-xl transition-transform group-hover:scale-110 ${isWatching ? 'animate-pulse' : ''}`}>
                  {isWatching ? '■' : '▶'}
                </span>
              </button>

              <button
                onClick={handleVibeCheck}
                className="w-full py-4 px-6 bg-primary-violet/10 hover:bg-primary-violet/20 border border-primary-violet/30 text-primary-violet rounded-xl transition-all flex items-center justify-between group hover:shadow-lg hover:shadow-primary-violet/10 active:scale-[0.98]">
                <div className="flex flex-col items-start">
                  <span className="font-bold text-sm tracking-wide">VIBE CHECK</span>
                  <span className="text-[10px] opacity-70 font-mono">Run system diagnostics</span>
                </div>
                <span className="text-xl group-hover:rotate-12 transition-transform">⚡</span>
              </button>

              <button
                onClick={toggleConfig}
                className="w-full py-4 px-6 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-xl transition-all flex items-center justify-between group hover:shadow-lg hover:shadow-white/5 active:scale-[0.98]">
                <div className="flex flex-col items-start">
                  <span className="font-bold text-sm tracking-wide">SYSTEM CONFIG</span>
                  <span className="text-[10px] opacity-70 font-mono text-text-dim">Advanced parameters</span>
                </div>
                <span className="text-xl group-hover:rotate-90 transition-transform duration-500">⚙</span>
              </button>
            </div>

            <div className="mt-8 pt-6 border-t border-white/5">
              <div className="flex items-center gap-3 opacity-50 hover:opacity-100 transition-opacity cursor-help">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs">?</div>
                <div className="text-xs text-text-dim">Need help? Access documentation</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Bottom Panel: Activity Log */}
      <footer className="h-48 z-10 glass-panel p-1 overflow-hidden">
        <ActivityLog logs={logs} />
      </footer>
    </div>
  );
}

export default App;
