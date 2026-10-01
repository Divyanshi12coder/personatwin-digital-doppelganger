/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        mustard: { DEFAULT: "#D4A017", dark: "#B3860F" },
        gold: "#E7B84B",
        brown: { DEFAULT: "#4A2C1A", light: "#5C3A24" },
        chocolate: "#6B4226",
        cream: "#FFF9ED",
        paper: "#F7F1E3",
        ink: "#241A14",
        muted: "#806B5A",
        softgold: "#F8E8B0",
        line: "#E6D9BF",
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Inter"', "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        hand: ['"Caveat"', '"Segoe Print"', "cursive"],
      },
      boxShadow: {
        paper: "0 1px 0 rgba(74,44,26,0.06), 0 8px 24px -12px rgba(74,44,26,0.25)",
        lift: "0 2px 0 rgba(74,44,26,0.08), 0 18px 40px -18px rgba(74,44,26,0.45)",
        inset: "inset 0 1px 0 rgba(255,255,255,0.6)",
      },
      borderRadius: {
        note: "14px",
      },
      keyframes: {
        blink: { "0%, 80%, 100%": { opacity: "0.25" }, "40%": { opacity: "1" } },
      },
      animation: {
        blink: "blink 1.4s infinite ease-in-out both",
      },
    },
  },
  plugins: [],
};
