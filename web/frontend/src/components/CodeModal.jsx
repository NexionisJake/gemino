import React, { useEffect, useState } from 'react';

const CodeModal = ({ file, onClose }) => {
    const [content, setContent] = useState('Loading...');
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchContent = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/file_content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: file })
                });
                if (!res.ok) throw new Error('Failed to load file');
                const data = await res.json();
                setContent(data.content);
            } catch (e) {
                setError(e.message);
                setContent('');
            }
        };
        if (file) fetchContent();
    }, [file]);

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="glass-panel w-full max-w-4xl max-h-[80vh] flex flex-col bg-bg-void/90 relative">
                <div className="flex justify-between items-center p-4 border-b border-white/10">
                    <h3 className="font-rajdhani font-bold text-lg text-primary-neon truncate">{file}</h3>
                    <button onClick={onClose} className="text-text-dim hover:text-white transition-colors">✕</button>
                </div>
                <div className="flex-1 overflow-auto p-4 custom-scrollbar bg-[#0d0e12]">
                    {error ? (
                        <div className="text-status-danger font-mono p-4">Error: {error}</div>
                    ) : (
                        <pre className="text-sm font-mono text-text-main">
                            <code>{content}</code>
                        </pre>
                    )}
                </div>
                <div className="p-4 border-t border-white/10 flex justify-end gap-2">
                    <button onClick={onClose} className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded text-sm text-text-main transition-colors">
                        CLOSE
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CodeModal;
