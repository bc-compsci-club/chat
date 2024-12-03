import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      keyframes: {
        typing: {
          "0%": {
            width: "0%",
            visibility: "hidden"
          },
          // "100%": {
          //   width: "100%",
          // },
        },
      },
      animation: {
        typing: "typing 2s",
      },
      colors: {
        "bc-red": "#882346",
        "bc-yellow": "#f3bd48",
      },
    }
  },
  plugins: [],
};
export default config;
