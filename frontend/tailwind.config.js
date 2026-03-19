/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  safelist: [
    { pattern: /.*/ }
  ],
  theme: {
    extend: {
      colors: {
        'surface': '#0a0a0f',
        'surface-1': '#111118',
        'surface-2': '#16161f',
        'surface-3': '#1c1c28',
        'surface-4': '#222233',
        'accent': '#6366f1',
        'accent-dim': '#4f46e5',
        'accent-glow': '#818cf8',
        'ember': '#f97316',
        'jade': '#10b981',
        'rose-custom': '#f43f5e',
        'amber-custom': '#f59e0b',
      },
    },
  },
  plugins: [],
}
