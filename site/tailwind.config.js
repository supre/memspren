/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#83d5c6',
        'on-primary': '#00201c',
        surface: '#0a0c10',
        'on-surface': '#e1e3e1',
        'accent-cyan': '#00f5ff',
        'accent-teal': '#005147',
        'glass-bg': 'rgba(10, 12, 16, 0.7)',
        'glass-border': 'rgba(131, 213, 198, 0.1)',
      },
      fontFamily: {
        headline: ['Newsreader', 'serif'],
        body: ['Manrope', 'sans-serif'],
        label: ['Manrope', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.125rem',
        lg: '0.25rem',
        xl: '0.5rem',
        full: '0.75rem',
      },
    },
  },
  plugins: [],
}
