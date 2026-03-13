/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        midnight: '#07131f',
        abyss: '#0f2332',
        glow: '#4be2c5',
        ember: '#ff8a4c',
        mist: '#93b9d8',
      },
      boxShadow: {
        panel: '0 18px 40px rgba(3, 13, 22, 0.28)',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      backgroundImage: {
        'soc-grid': 'linear-gradient(rgba(75, 226, 197, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(75, 226, 197, 0.08) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
};
