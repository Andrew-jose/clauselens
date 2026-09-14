/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          500: '#0066cc',
          600: '#0052a3',
          700: '#003d7a',
          900: '#001f3f',
        },
        grounded: {
          green: '#10b981',
          amber: '#f59e0b',
          gray: '#6b7280',
          blue: '#3b82f6',
        }
      }
    },
  },
  plugins: [],
}
