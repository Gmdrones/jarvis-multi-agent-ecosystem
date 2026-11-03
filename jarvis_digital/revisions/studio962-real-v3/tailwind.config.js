/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        espresso: {
          950: '#0E0C0A',
          900: '#12100E',
          800: '#1A1715',
          700: '#221E1B',
          600: '#2B2623'
        },
        gold: {
          DEFAULT: '#D4AF37',
          light: '#E5C158',
          dark: '#B08E28',
          amber: '#C68B59'
        },
        linen: {
          DEFAULT: '#D4CCC5',
          ivory: '#F8F5F0',
          muted: '#9E948B'
        }
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif']
      }
    },
  },
  plugins: [],
}