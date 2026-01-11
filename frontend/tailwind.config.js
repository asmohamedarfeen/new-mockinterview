/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'meet-dark': '#202124',
        'meet-gray': '#3c4043',
        'meet-blue': '#1a73e8',
      },
    },
  },
  plugins: [],
}
