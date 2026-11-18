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
  {
    files: ["app/**/*.{ts,tsx}", "src/**/*.{ts,tsx}"],
    ignores: ["src/theme/**"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector:
            "Literal[value=/#[0-9a-fA-F]{3,8}\\b/], TemplateElement[value.raw=/#[0-9a-fA-F]{3,8}\\b/]",
          message: "Use a colour from src/theme.",
        },
        {
          selector:
            "Property[key.name='fontSize'] > Literal.value, Property[key.value='fontSize'] > Literal.value, JSXAttribute[name.name='fontSize'] Literal",
          message: "Use a typography role from src/theme.",
        },
      ],
    },
  },
]);
