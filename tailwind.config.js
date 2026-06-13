/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        softform: {
          mist: {
            50: '#f4faf7',
            100: '#e8f4f1',
          },
          ice: {
            100: '#e7f0f4',
          },
          cream: '#f8f2df',
          sage: '#c9ddd7',
          navy: {
            950: '#08111f',
            900: '#0d1726',
            800: '#132337',
            700: '#1c324b',
          },
          text: {
            primary: '#111827',
            secondary: '#475569',
            muted: '#5c6e80',
          },
          aqua: {
            300: '#85d9ce',
          },
          teal: {
            300: '#85d9ce',
            500: '#20a99a',
            deep: '#0e615b',
          },
          emerald: {
            soft: '#38b883',
          },
          amber: {
            200: '#f6df9d',
            300: '#f1cf78',
            500: '#d9a83f',
          },
        },
        'fintech': {
          'navy': '#0d1726',
          'navy-light': '#1c324b',
          'blue': '#132337',
          'cyan': '#85d9ce',
          'teal': '#20a99a',
          'emerald': '#38b883',
          'amber': '#d9a83f',
          'warm-white': '#f4faf7',
          'warm-gray': '#e8f4f1',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft-inner': 'inset 0 2px 8px rgba(8, 17, 31, 0.06), inset 0 1px 2px rgba(8, 17, 31, 0.04)',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite',
        'slide-up': 'slideUp 0.6s ease-out',
        'shimmer': 'shimmer 1.8s infinite linear',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-14px)' },
        },
        glow: {
          '0%, 100%': { opacity: '0.45' },
          '50%': { opacity: '0.82' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
    },
  },
  plugins: [],
}
