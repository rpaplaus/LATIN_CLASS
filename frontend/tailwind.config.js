/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        roman: {
          50: '#fdfbf7',
          100: '#f8f4eb',
          200: '#eee5d4',
          300: '#e1d0b7',
          400: '#cca882',
          500: '#bc8b5c',
          600: '#a47047',
          700: '#84563a',
          800: '#6d4633',
          900: '#5b3b2d',
        },
        imperial: {
          gold: '#c99a2c',
          lightgold: '#fdf5df',
          crimson: '#881337',
          slate: '#0f172a',
        },
      },
      fontFamily: {
        serif: ['"Cinzel"', '"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
