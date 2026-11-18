# Kürsü

Kürsü uses one Expo Router app for web, iOS and Android, backed by FastAPI and PostgreSQL 16. A guest can choose a teaching field, take the adaptive AGS placement test and see their estimated net range and first-week study plan.

## Run locally

Use Node 22.13+ on the Node 22 LTS line, pnpm 11.6.0, uv, and Docker with Compose v2.20+ or newer. Start Docker first. The commands below use a POSIX shell on macOS, Linux or WSL. uv can install Python 3.12 when needed.

```sh
pnpm setup
```

Setup creates a local `.env` from `.env.example` when needed, initializes a random JWT signing key for development and installs the versions recorded in `pnpm-lock.yaml` and `services/api/uv.lock`. It waits for PostgreSQL, applies the migrations, imports the seed and generates the development question bank. It also generates the API client and installs Playwright Chromium. You can repeat setup against the same database. On a minimal Linux machine, Chromium may also need system libraries installed with `pnpm --filter @kursu/app exec playwright install-deps chromium`.

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

## App shell and component gallery

Open `/` to start. A new guest chooses a teaching field, daily study time and first or repeat attempt. **Seviye testine başla** opens the untimed 30-question test. **Önce uygulamayı gez** saves the profile and opens Today. Each answer is saved on the server. Returning to Today on the same browser or installation offers the next unanswered question. The result shows a net range, the six subtests ordered by accuracy and a first-week preview. A ten-question retake opens 14 Istanbul calendar days after completion. From the result or Settings, sign up with an email code, Google or Apple. Registering keeps the guest history. Signing into an existing identity merges both histories.

The API renews guest sessions using an HttpOnly cookie on web and secure OS storage on mobile. Serve the web app and API over HTTPS on the same site in production, configure the web origin in `APP_ORIGIN` and supply a stable private `JWT_SECRET` of at least 32 bytes. Use the same hostname for both servers in local web development. The countdown and retake availability come from the server.

The phone shell links to Today, Lessons, Mock and Progress. On web at 1024 px or wider a side menu also links to the mistake notebook. The destination routes support direct links and browser history. Today opens the candidate’s plan, placement actions and Settings. In development, Today also shows the live API health check.

In development, select **Bileşen galerisi** on Today on any platform, or open `http://localhost:8081/gallery` on web. Try the selection controls, question map and navigation previews there. The pinned **Bugüne dön** button returns to Today. The sample state lasts for the current gallery visit. The app bundles the five Plus Jakarta Sans weights locally and renders the reference icons with SVG. Production builds protect the gallery route. A static web host should serve `index.html` for application routes so deep links can enter the shell.

## Accounts and settings

In local development, **E-posta ile devam et** sends the six-digit code to the API terminal. The code lasts ten minutes and permits five attempts. Production uses SMTP with STARTTLS. Set `EMAIL_SENDER`, `SMTP_HOST`, `SMTP_PORT` and, when required, `SMTP_USERNAME` and `SMTP_PASSWORD`. Deploy the shared Turkish email template from `apps/app/src/i18n/email.json` alongside the service.

For Google, configure the web client ID first in `GOOGLE_CLIENT_IDS` and set `GOOGLE_CLIENT_SECRET`. For Apple, put the Services ID first in `APPLE_AUDIENCES` and supply its signed, unexpired `APPLE_CLIENT_SECRET`. Set `API_PUBLIC_ORIGIN` to the external HTTPS API origin. Register its `/v1/auth/callback/google` and `/v1/auth/callback/apple` paths with their respective providers. The system browser uses the same registered HTTPS callback on all platforms. Native releases return through the registered `kursu://auth` app scheme. Test that return on a development or release build with the app scheme installed. Only the API holds provider secrets. [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect) · [Sign in with Apple](https://developer.apple.com/documentation/signinwithapplerestapi)

Settings supports daily minutes, an optional Istanbul notification time, the AI-content disclosure, legal-text slots, logout on the current device and confirmed account deletion. The privacy, consent, terms and refund texts await counsel.

## Daily study plan

Today opens a personal plan on the first visit of each Istanbul day. The server schedules due reviews, up to two five-minute lessons and a 10–15 question topic test within the selected budget. The configured mock day has one 110-minute exam. In the final 30 days, study days use due reviews and previously opened topics. Changing the daily minutes in Settings rebuilds the current plan and preserves completed work. An unfinished assignment from an earlier day can occupy a later study slot within that day's budget.

Open a row or choose **Başla** to see the assignment. Lesson tasks include the published lesson cards. **Görevi tamamla** records completion and updates Today, the current streak and the weekly goal. Activity-specific scored sessions are scheduled for M6–M8. The first missed day in a Monday–Sunday week uses a freeze. Five completed days meet the weekly goal. The wide layout adds the net estimate and three weakest subtests. The scheduling inputs at this milestone come from placement responses and completed plan tasks.

For the API, use `GET /v1/plan/today`, `GET /v1/plan/tasks/{id}` and the task's `POST /start` and `POST /complete` operations. The server owns all dates, task estimates, state transitions, progress and streaks. Browser tests run against isolated schemas and a local test mailbox. The API's development email log and test mailbox require no mail service.

## Commands

| Command | Result |
| --- | --- |
| `pnpm setup` | Install the workspace and prepare the local database and browser. |
| `pnpm dev:api` | Start Uvicorn on port 8000 with reload. |
| `pnpm dev:app` | Start Metro and Expo Router on port 8081. |
| `pnpm gen:api` | Emit the typed API client from FastAPI's OpenAPI document. Both servers can be stopped. |
| `pnpm import-content FILE [FILE ...]` | Validate and upsert offline JSON bundles in one PostgreSQL transaction. Paths are relative to the repository root or absolute. |
| `pnpm make-placeholders` | Generate and import deterministic development content after the seed. Use `--output PATH` to write the importable JSON to a file. |
| `pnpm lint` | Check app code with ESLint, workspace formatting with Prettier, and Python with Ruff. |
| `pnpm typecheck` | Check both TypeScript projects and run strict mypy on the service. |
| `pnpm test` | Run Jest component tests and pytest API tests. Leave PostgreSQL running. |
| `pnpm check` | Run lint, type checks and unit/API tests together. |
| `pnpm test:e2e` | Run Chromium against the web export on port 4173, an API with a temporary seeded PostgreSQL schema on 8100 and the development gallery on 4181. Covers guest placement, email registration, settings, account deletion, daily planning, streaks, reference styles and navigation at 390 and 1280 px. |

Run `docker compose stop` to stop PostgreSQL and keep its data. To start it again, run `docker compose up -d --wait postgres`.

## Content and catalogue

The seed supplies four teaching fields, all six AGS subtests, six topics, one lesson and five original development questions. Local setup expands this to 31 topics, 32 lessons, 935 questions and ten 80-question mocks. Generated material carries `is_placeholder: true`. Its question stems and lesson and mock titles start with `[ÖRNEK]`. [Sample bundle](content/seed/sample-content.json) · [Server configuration data](content/seed/config.json)

An offline bundle has `schema_version: 1` and the collections it wants to import. Each supplied entity has a stable ID. A supplied lesson includes its complete ordered cards and two check questions. A mock supplies 80 distinct `question_ids` in exam order. References can point to rows in the same bundle or to previously imported rows. Pass multiple files in dependency order. A schema violation, an invalid reference, or a failed database write rolls back the whole invocation. Importing an edited row updates it under its original ID. Omitted questions remain available to historical answers. Set `APP_ENV=production` on production imports to reject any bundle containing placeholders. [Bundle JSON Schema](content/schema/bundle-v1.schema.json)

Start the API and open `http://localhost:8000/v1/docs` to try the catalogue. It lists fields, subtests in exam order, topics (optional `subtest_id`), lessons (optional `topic_id`) and mocks. `GET /v1/lessons/{id}` includes the source, ordered cards, and the stem and five options for each check question. The anonymous catalogue requires a published parent and published questions. An unavailable lesson ID returns HTTP 404.

## Repository

- `apps/app/app/` contains the Router layouts and routes. Shared UI is in `apps/app/src/components/`, tokens and bundled fonts are in `src/theme/`, Turkish copy is in `src/i18n/tr.ts` and locale formatting is in `src/lib/format.ts`. TanStack Query handles server state and the placement screens are in `src/features/placement/`.
- `services/api/app/` contains the FastAPI app, settings and async SQLAlchemy session factory. Psycopg connects to PostgreSQL. The live contract is at `/v1/openapi.json` and API documentation is at `/v1/docs`.
- `services/api/alembic/` contains the database migrations. The content module stores reference data, question feedback, sources, lesson cards and mock positions. The API tests exercise the migrations and imports in isolated PostgreSQL schemas.
- `packages/api-client/src/index.ts` is generated from `app.openapi()`. feTS derives the typed operations and response bodies from that document. Change the API, run `pnpm gen:api` and include the generated file in the same commit.
- `.github/workflows/ci.yml` checks migration and client drift, runs the root checks and browser smoke test, exports both native bundles and starts the two development servers on pushes and pull requests.

Install Expo-aware packages from `apps/app` with `npx expo install <package> --pnpm`. See the milestone plans for decisions and verification. [M0 scaffold](.agent/plans/M0-scaffold.md) · [M1 design system](.agent/plans/M1-design-system.md) · [M2 content catalogue](.agent/plans/M2-content-catalogue.md) · [M3 guest placement](.agent/plans/M3-guest-placement.md) · [M4 accounts and settings](.agent/plans/M4-accounts-settings.md) · [M5 daily plan](.agent/plans/M5-daily-plan.md)
