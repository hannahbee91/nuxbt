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
        lavender: {
          DEFAULT: '#E6E6FA',
          50: '#F8F8FC',
          100: '#F3F3FD',
          200: '#E6E6FA',
          300: '#D1D1F6',
          400: '#BDBDE8',
          500: '#A9A9D9',
          900: '#2D2D4A',
        },
        honey: {
          DEFAULT: '#FFC30B',
          50: '#FFFAEB',
          100: '#FFF2CC',
          200: '#FFE585',
          300: '#FFD447',
          400: '#FFC30B',
          500: '#E6A800',
          600: '#CC9200',
          900: '#664500',
        }
      }
    },
  },
  plugins: [],
}
