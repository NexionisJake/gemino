import React from 'react';

const StatusOrb = ({ status = 'active' }) => {
    const getStatusColor = () => {
        switch (status) {
            case 'danger': return 'bg-status-danger shadow-glow-danger';
            case 'warning': return 'bg-status-warning shadow-glow-warning';
            case 'active':
            default: return 'bg-start-success shadow-glow-neon'; // Using neon for active/safe
        }
    };

    const getStatusRing = () => {
        switch (status) {
            case 'danger': return 'border-status-danger';
            case 'warning': return 'border-status-warning';
            case 'active':
            default: return 'border-primary-neon';
        }
    };

    return (
        <div className="relative flex items-center justify-center w-64 h-64 mx-auto my-8">
            {/* Outer Pulse Ring */}
            <div className={`absolute w-full h-full rounded-full border-2 opacity-20 animate-ping ${getStatusRing()}`}></div>

            {/* Inner Rotating Ring */}
            <div className={`absolute w-48 h-48 rounded-full border border-dashed animate-spin-slow opacity-40 ${getStatusRing()}`}></div>

            {/* Core Orb */}
            <div className={`relative w-32 h-32 rounded-full ${getStatusColor()} backdrop-blur-xl bg-opacity-20 flex items-center justify-center animate-pulse-slow transition-all duration-1000`}>
                <div className={`w-20 h-20 rounded-full ${status === 'danger' ? 'bg-status-danger' : 'bg-primary-neon'} blur-xl opacity-50`}></div>
                <span className="absolute text-xl font-rajdhani font-bold tracking-widest text-white text-glow">
                    {status.toUpperCase()}
                </span>
            </div>
        </div>
    );
};

export default StatusOrb;
