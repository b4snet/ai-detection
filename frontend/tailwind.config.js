/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        sentinel: {
          bg: '#04070a',
          panel: '#0a0f14',
          panel2: '#0d141c',
          border: '#12352a',
          neon: '#00ff88',
          dim: '#0aff9d',
          amber: '#ffc857',
          red: '#ff3355',
          cyan: '#35e0ff',
          text: '#c8f5d9',
          muted: '#5d8a70',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
      },
      boxShadow: {
        neon: '0 0 8px rgba(0,255,136,0.35), 0 0 24px rgba(0,255,136,0.12)',
        'neon-lg': '0 0 12px rgba(0,255,136,0.5), 0 0 48px rgba(0,255,136,0.2)',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        blink: { '0%,49%': { opacity: '1' }, '50%,100%': { opacity: '0' } },
        pulseglow: {
          '0%,100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
        spinSlow: { to: { transform: 'rotate(360deg)' } },
        flicker: {
          '0%,100%': { opacity: '1' },
          '92%': { opacity: '1' },
          '93%': { opacity: '0.4' },
          '94%': { opacity: '1' },
        },
      },
      animation: {
        scan: 'scan 3.2s linear infinite',
        blink: 'blink 1.1s step-end infinite',
        pulseglow: 'pulseglow 2.4s ease-in-out infinite',
        spinSlow: 'spinSlow 2.5s linear infinite',
        flicker: 'flicker 6s linear infinite',
      },
    },
  },
  plugins: [],
}
