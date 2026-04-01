/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Paleta inspirada nas cores da FAB (Força Aérea Brasileira)
        fab: {
          50:  '#eef3fb',
          100: '#d5e4f5',
          200: '#adc9ec',
          300: '#79a8de',
          400: '#4a86ce',
          500: '#2c6ab8',  // Azul FAB primário
          600: '#1f54a0',
          700: '#1a4383',
          800: '#16376a',
          900: '#112c56',
        },
        olive: {
          500: '#5a6e2c',
          600: '#4a5c22',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
