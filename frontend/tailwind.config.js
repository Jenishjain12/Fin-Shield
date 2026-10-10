/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#08090B",
        panel: "#111318",
        line: "#1E232C",
        mute: "#8B929E",
        paper: "#F5F5F5",
        accent: "#3EE0FF",
        high: "#F43F5E",
        mid: "#F59E0B",
        low: "#6EE7B7",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
