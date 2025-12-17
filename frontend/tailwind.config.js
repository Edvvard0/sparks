/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'sparks-bg': '#1A1A1A',
        'sparks-text': '#E7E7E7',
        'sparks-button': '#2E2E2E',
        'sparks-button-active': '#282828',
        'sparks-primary': '#6049EC',
        'sparks-selected': '#FFC700',
        'sparks-intimate': '#EB454E',
        'sparks-card-bg': '#2E2E2E',
      },
      fontFamily: {
        'sf-pro': ['SF Pro', 'system-ui', 'sans-serif'],
        'sf-pro-display': ['SF Pro Display', 'system-ui', 'sans-serif'],
        'sf-pro-rounded': ['SF Pro Rounded', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
