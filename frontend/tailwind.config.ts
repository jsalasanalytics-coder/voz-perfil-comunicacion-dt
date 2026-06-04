import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system", "BlinkMacSystemFont", "SF Pro Display", "SF Pro Text",
          "Helvetica Neue", "Arial", "sans-serif",
        ],
      },
      colors: {
        ink: "#1d1d1f",
        subtle: "#6e6e73",
        line: "#d2d2d7",
        accent: "#0071e3",
      },
      borderRadius: { xl2: "1.25rem", xl3: "1.75rem" },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.04), 0 8px 30px rgba(0,0,0,0.06)",
        glass: "0 8px 40px rgba(0,0,0,0.08)",
      },
      backdropBlur: { xs: "2px" },
    },
  },
  plugins: [],
};
export default config;
