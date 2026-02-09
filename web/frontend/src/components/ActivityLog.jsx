import React, { useEffect, useRef } from 'react';

const ActivityLog = ({ logs }) => {
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="glass-panel p-4 h-96 flex flex-col font-mono text-sm relative overflow-hidden">
            {/* Header */}
            <div className="flex justify-between items-center mb-2 border-b border-white/10 pb-2">
                <span className="text-primary-neon font-rajdhani tracking-wider">/// SYSTEM LOGS</span>
                <div className="flex gap-2">
                    <div className="w-2 h-2 rounded-full bg-status-danger"></div>
                    <div className="w-2 h-2 rounded-full bg-status-warning"></div>
                    <div className="w-2 h-2 rounded-full bg-status-success"></div>
                </div>
            </div>

            {/* Scanlines Overlay */}
            <div className="absolute inset-0 pointer-events-none bg-[url('https://media.giphy.com/media/xT9IgkKL1SJVxzJSEg/giphy.gif')] opacity-[0.02] mix-blend-overlay"></div>

            {/* Logs */}
            <div className="flex-1 overflow-y-auto space-y-1 z-10 custom-scrollbar" ref={scrollRef}>
                {logs.length === 0 && <span className="text-text-dim opacity-50">Waiting for system activity...</span>}

                {logs.map((log, index) => (
                    <div key={index} className="flex gap-2 animate-fade-in">
                        <span className="text-text-dim">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                        <span className={`${log.type === 'error' ? 'text-status-danger' :
                                log.type === 'warning' ? 'text-status-warning' :
                                    'text-primary-neon'
                            }`}>
                            {log.message}
                        </span>
                    </div>
                ))}
                <div className="animate-pulse text-primary-neon">_</div>
            </div>
        </div>
    );
};

export default ActivityLog;
