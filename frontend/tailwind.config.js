/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'heading': ['Kalam', 'cursive'],
        'body': ['Patrick Hand', 'cursive'],
      },
      colors: {
        'paper': '#fdfbf7',
        'pencil': '#2d2d2d',
        'muted': '#e5e0d8',
        'accent': '#ff4d4d',
        'pen-blue': '#2d5da1',
        'sticky': '#fff9c4',
      },
      boxShadow: {
        'hard': '4px 4px 0px 0px #2d2d2d',
        'hard-lg': '8px 8px 0px 0px #2d2d2d',
        'hard-hover': '2px 2px 0px 0px #2d2d2d',
        'hard-sm': '3px 3px 0px 0px rgba(45, 45, 45, 0.1)',
      },
      animation: {
        'gentle-bounce': 'gentleBounce 3s ease-in-out infinite',
        'jiggle': 'jiggle 0.3s ease-in-out',
      },
      keyframes: {
        gentleBounce: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        jiggle: {
          '0%, 100%': { transform: 'rotate(0deg)' },
          '25%': { transform: 'rotate(-1deg)' },
          '75%': { transform: 'rotate(1deg)' },
        },
      },
    },
  },
  plugins: [],
}
