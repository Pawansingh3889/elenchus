// Tailwind v4 is a PostCSS plugin and nothing else: no tailwind.config.js, because the
// theme is declared in CSS (see app/tailwind.css).
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
