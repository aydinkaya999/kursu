import type { PlaywrightTestConfig } from "@playwright/test";
const web = "http://127.0.0.1:4173";
const api = "http://127.0.0.1:8100";
const gallery = "http://127.0.0.1:4181";
const widths = [
  { name: "phone-width", viewport: { width: 390, height: 844 } },
  { name: "desktop", viewport: { width: 1280, height: 800 } },
];
const config: PlaywrightTestConfig = {
  testDir: "./e2e",
  forbidOnly: !!process.env.CI,
  workers: 2,
  use: { baseURL: web, browserName: "chromium", trace: "retain-on-failure" },
  projects: widths.flatMap(({ name, viewport }) => [
    { name, testIgnore: /gallery\.spec\.ts/, use: { viewport } },
    {
      name: name + "-gallery",
      testMatch: /gallery\.spec\.ts/,
      use: { viewport, baseURL: gallery },
    },
  ]),
  webServer: [
    {
      command:
        "PYTHONPATH=. uv run --directory ../../services/api python tests/serve_e2e.py --port 8100",
      url: api + "/v1/health",
      env: { APP_ORIGIN: web },
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
      timeout: 60000,
    },
    {
      command:
        "pnpm exec expo export --platform web && uv run --project ../../services/api python e2e/serve_spa.py",
      url: web,
      env: { EXPO_PUBLIC_API_URL: api, CI: "1" },
      timeout: 180000,
    },
    {
      command: "pnpm exec expo start --web --localhost --port 4181",
      url: gallery + "/status",
      env: { EXPO_PUBLIC_API_URL: api, CI: "1", EXPO_OFFLINE: "1" },
      timeout: 120000,
    },
  ],
};
export default config;
