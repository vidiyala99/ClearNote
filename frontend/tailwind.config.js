/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        heading: ['Figtree', 'system-ui', 'sans-serif'],
        body: ['Noto Sans', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
