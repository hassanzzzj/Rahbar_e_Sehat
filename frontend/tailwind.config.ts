import type { Config } from "tailwindcss";

/**
 * Rahbar-e-Sehat design system — market-ready revision.
 *
 * Palette philosophy:
 *  - Primary surface:  warm off-white / light stone (60 %)
 *  - Primary brand:    forest green / deep teal-green (30 %)
 *  - Accent:           warm amber / terracotta (10 %)
 *  - Semantic:         clinical red/amber/green/grey for urgency states
 *
 * NO purple, NO cyan, NO blue.
 * Healthcare-appropriate, calm, approachable for rural Pakistan users.
 */
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    spacing: {
      0: "0px",
      0.5: "4px",
      1: "8px",
      1.5: "12px",
      2: "16px",
      2.5: "20px",
      3: "24px",
      4: "32px",
      5: "40px",
      6: "48px",
      7: "56px",
      8: "64px",
      10: "80px",
      12: "96px",
      14: "112px",
      16: "128px",
    },
    borderRadius: {
      none: "0px",
      sm: "4px",
      md: "8px",
      lg: "12px",
      xl: "16px",
      "2xl": "20px",
      full: "9999px",
    },
    extend: {
      fontFamily: {
        sans: ['"Inter Variable"', "Inter", "system-ui", "sans-serif"],
        urdu: ['"Noto Nastaliq Urdu"', "serif"],
      },
      letterSpacing: {
        tight: "-0.02em",
        tighter: "-0.03em",
        wide: "0.05em",
        wider: "0.06em",
      },
      colors: {
        // Warm neutral — off-white to near-black with warm undertone
        neutral: {
          50: "#F9F8F6",
          100: "#F2F0EC",
          200: "#E5E1DA",
          300: "#CCC7BC",
          400: "#A8A098",
          500: "#857D75",
          600: "#66605A",
          700: "#4D4842",
          800: "#333028",
          900: "#1A1815",
        },
        // Forest / sage green — primary brand
        secondary: {
          50: "#EEF4F0",
          100: "#D7E9DC",
          200: "#B0D2BC",
          300: "#81B495",
          400: "#55956E",
          500: "#357A53",
          600: "#276142",
          700: "#1E4D34",
          800: "#163A27",
          900: "#0D2418",
        },
        // Warm amber / terracotta — accent
        accent: {
          50: "#FDF6EE",
          100: "#F9E8D2",
          200: "#F3CDA1",
          300: "#ECAF69",
          400: "#E29040",
          500: "#C97528",
          600: "#A05C1E",
          700: "#784415",
          800: "#512D0D",
          900: "#2A1706",
        },
        // Clinical semantic colours
        semantic: {
          emergency: "#B52D24",
          "emergency-bg": "#FDF2F1",
          "emergency-border": "#F4C1BE",
          urgent: "#C47A18",
          "urgent-bg": "#FDF8EE",
          "urgent-border": "#F5DFA0",
          routine: "#357A53",
          "routine-bg": "#EEF4F0",
          "routine-border": "#B0D2BC",
          selfcare: "#66605A",
          "selfcare-bg": "#F9F8F6",
          "selfcare-border": "#E5E1DA",
        },
        border: "#E5E1DA",
        surface: "#F9F8F6",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.04)",
        "card-hover": "0 4px 12px 0 rgba(0,0,0,0.10), 0 2px 6px -2px rgba(0,0,0,0.06)",
        "card-emergency": "0 0 0 2px #F4C1BE, 0 1px 3px 0 rgba(181,45,36,0.10)",
      },
      transitionDuration: {
        fast: "120ms",
        normal: "200ms",
        slow: "350ms",
      },
      animation: {
        "fade-in": "fadeIn 0.25s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-dot": "pulseDot 1.4s ease-in-out infinite",
        "spin-slow": "spin 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseDot: {
          "0%, 100%": { transform: "scale(1)", opacity: "1" },
          "50%": { transform: "scale(1.4)", opacity: "0.7" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
