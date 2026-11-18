const { defineConfig } = require("eslint/config");
const expo = require("eslint-config-expo/flat");

module.exports = defineConfig([
  {
    ignores: [
      ".expo/**",
      "expo-env.d.ts",
      "dist/**",
      "test-results/**",
      "playwright-report/**",
    ],
  },
  ...expo,
]);
