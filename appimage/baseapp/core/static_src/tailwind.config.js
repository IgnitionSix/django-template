module.exports = {
  content: [
    "../templates/**/*.html",
    "../../core/templates/**/*.html",
    "../../core/**/*.py",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
};
