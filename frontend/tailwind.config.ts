import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#16213E",
        mint: "#DDF7ED",
        coral: "#FA766F",
        amber: "#F4B942",
        teal: "#0E7C7B"
      },
      boxShadow: {
        soft: "0 18px 40px rgba(22, 33, 62, 0.10)"
      }
    }
  },
  plugins: []
} satisfies Config;
