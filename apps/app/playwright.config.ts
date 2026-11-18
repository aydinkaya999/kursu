import type { PlaywrightTestConfig } from "@playwright/test";

const web = "http://127.0.0.1:4173";
const api = "http://127.0.0.1:8100";

const config: PlaywrightTestConfig = {
  testDir: "./e2e",
  forbidOnly: !!process.env.CI,
  use: { baseURL: web, browserName: "chromium", trace: "retain-on-failure" },
  projects: [
    { name: "phone-width", use: { viewport: { width: 390, height: 844 } } },
    { name: "desktop", use: { viewport: { width: 1280, height: 800 } } },
  ],
  webServer: [
    {
      command:
        "uv run --directory ../../services/api uvicorn app.main:app --host 127.0.0.1 --port 8100",
      url: api + "/v1/health",
      env: { APP_ORIGIN: web },
      timeout: 60_000,
    },
    {
      command:
        "pnpm exec expo export --platform web && uv run --project ../../services/api python -m http.server 4173 --bind 127.0.0.1 --directory dist",
      url: web,
      env: { EXPO_PUBLIC_API_URL: api, CI: "1" },
      timeout: 180_000,
    },
  ],
};

export default config;
