export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: { bg: "#0B0E14", panel: "#12161F", panel2: "#171C27", border: "#242B38", text: "#E6E9EF", muted: "#8891A3" },
        signal: { teal: "#4FD1C5", amber: "#F5A623", red: "#E5484D", violet: "#8B7FD1", blue: "#5B8DEF" },
      },
      fontFamily: { display: ["'Space Grotesk'", "sans-serif"], body: ["Inter", "sans-serif"], mono: ["'JetBrains Mono'", "monospace"] },
    },
  },
  plugins: [],
}
