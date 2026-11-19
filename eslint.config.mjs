import js from "@eslint/js";
import globals from "globals";

const appGlobals = {
  MYSUGYA_MANIFEST: "readonly",
  TRACTATE_META: "readonly",
  PERAKIM: "readonly",
  DAF_INDEX: "readonly",
  DAF_CONTENT: "readonly",
  DATA_VERSION: "readonly",
  // Cross-file globals: defined in tweaks-panel.jsx and shared/rashi_association.js,
  // concatenated into one scope by the build / dev shell.
  useTweaks: "readonly",
  groupRashiByLinkedId: "readonly",
};

export default [
  {
    ignores: [
      "modules/**",
      "dist/**",
      "node_modules/**",
      "tests/fixtures/**",
      "playwright-report/**",
      "test-results/**",
      // Function-body source (top-level await + return) stored by OpenClaw;
      // unparseable as a standalone file.
      "scripts/rabbi_cron_trigger.js",
    ],
  },
  js.configs.recommended,
  {
    files: [
      "app.jsx",
      "tweaks-panel.jsx",
      "manifest.js",
      "shared/**/*.js",
      "scripts/**/*.mjs",
      "scripts/**/*.js",
      "scripts/**/*.jsx",
      "tests/**/*.js",
      "tests/**/*.mjs",
      "playwright.config.js",
    ],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: { ...globals.browser, ...globals.node, React: "readonly", ReactDOM: "readonly" },
    },
    rules: {
      "no-undef": "error",
      "no-unreachable": "error",
      "no-dupe-keys": "error",
      "no-unused-vars": "warn",
      // Turned off: existing code uses intentionally empty catch blocks.
      "no-empty": "off",
    },
  },
  {
    // Plain browser scripts sharing one global scope, not ES modules.
    files: ["app.jsx", "tweaks-panel.jsx", "manifest.js"],
    languageOptions: { sourceType: "script" },
  },
  {
    // Only app.jsx reads these; declaring them elsewhere would clash with
    // their definitions (no-redeclare).
    files: ["app.jsx"],
    languageOptions: { globals: appGlobals },
  },
];
