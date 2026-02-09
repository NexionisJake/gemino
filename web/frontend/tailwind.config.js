/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                bg: {
                    void: "#020204", // Deep Abyssal Black
                    glass: "rgba(10, 10, 15, 0.4)", // Ultra-clear dark glass
                    panel: "#0A0A0F",
                },
                primary: {
                    neon: "#3B82F6", // Bioluminescent Blue
                    violet: "#8B5CF6", // Electric Purple
                    accent: "#F97316", // Sunset Orange
                },
                status: {
                    success: "#10B981", // Emerald
                    warning: "#F59E0B", // Amber
                    danger: "#EF4444", // Red-500
                },
                text: {
                    main: "#F3F4F6", // Gray-100
                    dim: "#9CA3AF", // Gray-400
                },
            },
            fontFamily: {
                rajdhani: ['"Rajdhani"', 'sans-serif'],
                inter: ['"Inter"', 'sans-serif'],
                mono: ['"JetBrains Mono"', 'monospace'],
            },
            boxShadow: {
                'glow-neon': '0 0 10px rgba(0, 240, 255, 0.5)',
                'glow-danger': '0 0 10px rgba(255, 0, 60, 0.5)',
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }
        },
    },
    plugins: [],
}
