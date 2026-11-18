# Kürsü

The M0 scaffold connects an Expo Router app for web, iOS and Android to FastAPI and PostgreSQL 16. The start screen displays **Sunucuya bağlanıldı.** after the API successfully queries PostgreSQL.

## Run locally

Use Node 22.13+ on the Node 22 LTS line, pnpm 11.6.0, uv, and Docker with Compose v2.20+ or newer. Start Docker first. The commands below use a POSIX shell on macOS, Linux or WSL. uv can install Python 3.12 when needed.

```sh
pnpm setup
```

Setup creates a local `.env` from `.env.example` when needed and installs the versions recorded in `pnpm-lock.yaml` and `services/api/uv.lock`. It then waits for PostgreSQL, applies the Alembic baseline, generates the client and installs Playwright Chromium. Repeating setup preserves the environment file and database. On a minimal Linux machine, Chromium may also need system libraries installed with `pnpm --filter @kursu/app exec playwright install-deps chromium`.

Start the servers in separate terminals from the repository root.

```sh
pnpm dev:api
```

```sh
pnpm dev:app
```

Press **w** for web, **i** for the iOS Simulator on macOS, or **a** for an Android emulator. Use an Expo Go version compatible with SDK 58. Web opens at `http://localhost:8081`. Check the service directly with `curl -i http://localhost:8000/v1/health`. A working database returns HTTP 200 and `{"status":"ok"}`. If PostgreSQL is unavailable the API returns HTTP 503 and the app offers **Tekrar dene**.

| Target | API address |
| --- | --- |
| Web and iOS Simulator | The default `EXPO_PUBLIC_API_URL=http://localhost:8000` works. |
| Android Studio emulator | Start Metro with `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000 pnpm dev:app` and press **a**. |
| Physical phone | Connect it to the computer's Wi-Fi network, set `EXPO_PUBLIC_API_URL` in the root `.env` to `http://<computer-LAN-IP>:8000`, restart Metro and scan its QR code. |

`pnpm dev:api` listens on all interfaces for device testing. PostgreSQL is published on loopback. If port 5432 is occupied, set both `POSTGRES_PORT` and the port in `DATABASE_URL` before setup. When serving the web app from another origin, set `APP_ORIGIN` to its full origin and restart the API. Expo reads public variables at bundle time.

## Commands

| Command | Result |
| --- | --- |
| `pnpm setup` | Install the workspace and prepare the local database and browser. |
| `pnpm dev:api` | Start Uvicorn on port 8000 with reload. |
| `pnpm dev:app` | Start Metro and Expo Router on port 8081. |
| `pnpm gen:api` | Emit the typed API client from FastAPI's OpenAPI document. Both servers can be stopped. |
| `pnpm lint` | Check app code with ESLint, workspace formatting with Prettier, and Python with Ruff. |
| `pnpm typecheck` | Check both TypeScript projects and run strict mypy on the service. |
| `pnpm test` | Run Jest component tests and pytest API tests. Leave PostgreSQL running. |
| `pnpm check` | Run lint, type checks and unit/API tests together. |
| `pnpm test:e2e` | Build the web app, run the API on port 8100, serve the export on port 4173 and exercise the health check in Chromium at 390 and 1280 px. |

Run `docker compose stop` to stop PostgreSQL and keep its data. To start it again, run `docker compose up -d --wait postgres`.

## Repository

- `apps/app/app/` contains the Router layout and health screen. Turkish copy and style tokens live in `apps/app/src/`. TanStack Query handles the request state and retry.
- `services/api/app/` contains the FastAPI app, settings and async SQLAlchemy session factory. Psycopg connects to PostgreSQL. The live contract is at `/v1/openapi.json` and API documentation is at `/v1/docs`.
- `services/api/alembic/` contains the baseline. PostgreSQL holds only Alembic's revision table after a fresh setup. Content tables and seed import start in M2.
- `packages/api-client/src/index.ts` is generated from `app.openapi()`. feTS derives the typed operations and response bodies from that document. Change the API, run `pnpm gen:api` and include the generated file in the same commit.
- `.github/workflows/ci.yml` checks migration and client drift, runs the root checks and browser smoke test, exports both native bundles and starts the two development servers on pushes and pull requests.

Install Expo-aware packages from `apps/app` with `npx expo install <package> --pnpm`. The M0 decisions and verification record are in the [ExecPlan](.agent/plans/M0-scaffold.md).
