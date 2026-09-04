/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F4F6F7",
        surface: "#FFFFFF",
        ink: {
          DEFAULT: "#0C1D2E",
          soft: "#4E5F70",
          faint: "#8B96A3",
        },
        line: "#DCE3E6",
        brand: {
          DEFAULT: "#005C83",
          dark: "#00435F",
          light: "#E3EEF4",
          accent: "#005C83",
        },
        status: {
          matched: "#1E7A5F",
          matchedBg: "#E1F1EA",
          review: "#B07A20",
          reviewBg: "#FBF0DC",
          conflict: "#B23A2E",
          conflictBg: "#FAE6E2",
          neutral: "#7A8A91",
          neutralBg: "#EBEFF0",
        },
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
        sans: ["Inter", "sans-serif"],
        mono: ['"IBM Plex Mono"', "monospace"],
      },
      borderRadius: {
        sm: "3px",
        DEFAULT: "4px",
        md: "6px",
        lg: "8px",
      },
    },
  },
  plugins: [],
};
