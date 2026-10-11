/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          deep: '#0b0c10',
          elevated: '#121318',
          hover: '#1a1c23',
        },
        surface: {
          1: '#121318',
          2: '#1a1c23',
          3: '#222530',
        },
        border: {
          neutral: '#272932',
          subtle: '#1f2129',
          focus: '#14b8a6',
        },
        text: {
          primary: '#f1f3f9',
          secondary: '#9498a8',
          muted: '#626677',
        },
        teal: {
          DEFAULT: '#14b8a6',
          glow: '#0d9488',
          dark: '#0f766e',
          light: '#2dd4bf',
        },
        // Universal Qualitative Reactions
        reaction: {
          peak: {
            DEFAULT: '#f59e0b',
            bg: 'rgba(245, 158, 11, 0.12)',
            border: 'rgba(245, 158, 11, 0.35)',
          },
          'loved-it': {
            DEFAULT: '#fb7185',
            bg: 'rgba(251, 113, 133, 0.12)',
            border: 'rgba(251, 113, 133, 0.35)',
          },
          'good-time': {
            DEFAULT: '#14b8a6',
            bg: 'rgba(20, 184, 166, 0.12)',
            border: 'rgba(20, 184, 166, 0.35)',
          },
          'not-my-thing': {
            DEFAULT: '#a78bfa',
            bg: 'rgba(167, 139, 250, 0.12)',
            border: 'rgba(167, 139, 250, 0.35)',
          },
          skip: {
            DEFAULT: '#e11d48',
            bg: 'rgba(225, 29, 72, 0.12)',
            border: 'rgba(225, 29, 72, 0.35)',
          },
        },
        // Tracking Status
        status: {
          watching: '#38bdf8',
          completed: '#34d399',
          plan: '#818cf8',
          paused: '#fbbf24',
          dropped: '#94a3b8',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        display: [
          'Outfit',
          'Inter',
          '-apple-system',
          'sans-serif',
        ],
      },
      aspectRatio: {
        poster: '2 / 3',
        game: '16 / 9',
        cover: '3 / 4',
      },
      boxShadow: {
        card: '0 4px 20px -2px rgba(0, 0, 0, 0.5)',
        'card-hover': '0 8px 30px -4px rgba(0, 0, 0, 0.7)',
        glow: '0 0 20px -5px rgba(20, 184, 166, 0.25)',
      },
    },
  },
  plugins: [],
};
