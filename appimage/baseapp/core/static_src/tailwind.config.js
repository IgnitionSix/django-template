module.exports = {
  content: [
    "../templates/**/*.html",
    "../../core/templates/**/*.html",
    "./src/**/*.{css,js}",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
};
