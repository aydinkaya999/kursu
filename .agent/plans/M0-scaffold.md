# M0 scaffold

## Purpose

From a fresh checkout, a developer can start PostgreSQL 16, a FastAPI service and one Expo Router app for web, iOS and Android. Opening the app checks the API and displays the outcome in Turkish. The same OpenAPI contract drives the app and the tests.

## Progress

- [x] Read the kit and identify the M0 acceptance criteria.
- [x] Write this plan before implementation.
- [x] Set up the workspace, database, API and migrations.
- [x] Generate the TypeScript contract and connect the Expo screen.
- [x] Add the root commands, tests, CI and setup instructions.
- [x] Create a clean verification clone, exercise the commands, regenerate the client twice and record the results.
- [x] Document the plan format after the owner confirmed the original guide is unavailable.
- [x] Locate both lockfiles and the installed SDK, Python environment and matching Playwright browser in the workspace or host cache.
- [x] Repair the Metro startup failure, TypeScript declarations, health component tests and formatting. Run the locked installs and repeat the checks in a clean checkout.
- [x] Export all three platforms and exercise the web export's error, retry and success states with controlled HTTP responses.
- [x] Complete a clean setup against PostgreSQL 16, verify both development servers, and pass the full local check and Chromium smoke test.
- [x] Verify the same source on a hosted GitHub Actions runner.

## Decision log

- M0 began with a self-contained plan because the kit omitted the planning guide. The owner confirmed the original is unavailable. The replacement documents this plan's format and the kit's existing instructions. [ExecPlan guide](../PLANS.md)
- ASSUMPTION: Health means the API can query PostgreSQL. Return HTTP 200 and `{"status":"ok"}` on success and HTTP 503 with the API error envelope when the database is unavailable. Use short Turkish status and retry text for the undesigned diagnostic screen.
- ASSUMPTION: M0 setup applies an empty Alembic baseline. Seed import starts in M2, when the seed and its tables exist.
- ASSUMPTION: Use feTS to infer the client from the generated OpenAPI types and Chromium for the smoke test at 390 and 1280 px.
- Use feTS's public CommonJS entry in Metro. With the ESM entry, the SDK 58 production bundle evaluates a TypeBox export named `Object` before initialization and the health screen crashes before it can make its first request.

## Implementation sequence

1. Define the pnpm workspace and root scripts. Configure local environment variables, PostgreSQL 16 readiness and a Python 3.12+ project managed by uv.
2. Add async SQLAlchemy sessions, the Alembic baseline, the FastAPI health route and API tests against PostgreSQL. Export OpenAPI directly from the app factory so generation works with both servers stopped.
3. Generate the TypeScript client contract. Install the stable Expo SDK and its compatible packages with Expo CLI. Use Expo Router, strict TypeScript and TanStack Query to show the real health result through that client.
4. Exercise the rendered health states with Jest. Have Playwright serve a web export and a live API, observe the HTTP response and assert the visible status. Use these same commands in GitHub Actions.
5. Document prerequisites, platform-specific API addresses, environment overrides and all root commands. Run validation and record any environmental limits.

## Discoveries

- The starting directory contains `AGENTS.md`, product documentation and design references. It has no Git metadata. Initializing the repository here returned `Operation not permitted` for `.git`.
- Expo identifies SDK 58 as its current stable release. [Expo release](https://expo.dev/sdk/58)
- The initial verification lacked uv and could not reach package registries. During the follow-up, Node 22.14, pnpm 11.6, Python 3.12.4, uv 0.13.9, both lockfiles and the matching browser were available. Writable copies of the dependency caches let the clean install run offline.
- Jest resolved `../app` to `app.json`. The component tests now load the explicit route after installing a fetch spy and exercise the generated client through the HTTP boundary. Its type dependencies require the TypeScript disposable library declarations.
- The SDK 58 package is `expo@58.0.26`. The manifest follows Expo's published module map for React 19.3, React Native 0.88.1, Router and the Jest preset. [SDK dependency map](https://raw.githubusercontent.com/expo/expo/sdk-58/packages/expo/bundledNativeModules.json)
- pnpm 11 runs the project's `setup` script when called as `pnpm setup`. The workspace pins 11.6.0. [pnpm scripts](https://pnpm.io/scripts)

## Validation

| M0 criterion | Verification on 2026-11-18 |
| --- | --- |
| Clean setup and both development servers | Started from a local Git clone with both lockfiles, no `.env` and no installed dependencies. `pnpm setup` created `.env` from the example, installed dependencies, started PostgreSQL 16.15, applied the migration, generated the client and completed browser setup. A separate Compose project used host port 55432 to isolate its data. Playwright started `pnpm dev:api` on port 8000 and `pnpm dev:app --localhost` on port 8081 and ran the health screen smoke test against them at both widths. Both cases passed. |
| App displays the API response | `pnpm test:e2e` passed both Chromium cases on the production web export. At 390 × 844 and 1280 × 800 the browser observed a live `GET /v1/health`, HTTP 200 and `{"status":"ok"}`, then found the Turkish success message. The document language was `tr`. Screenshots from the separate development-server run showed the heading and status centered and visible at both sizes. Expo also produced an iOS and an Android Hermes bundle. |
| Local checks and CI | `pnpm check` passed ESLint, Prettier, Ruff, both TypeScript projects, strict mypy, two Jest tests and two pytest tests. The API cases exercised a healthy PostgreSQL service with CORS and an unreachable database returning HTTP 503. Pytest emitted one deprecation warning from Starlette's test client. The hosted runner also passed the locked setup, checks, web smoke tests and client regeneration. [GitHub Actions](https://github.com/aydinkaya999/kursu/actions/runs/44386439833) |
| Reproducible client | Ran `pnpm gen:api` twice again in the clean checkout with its locked Python environment. `git diff --exit-code -- packages/api-client pnpm-lock.yaml services/api/uv.lock` passed and the client directory had no untracked files. |
| Health-only scope | The application's `/v1/openapi.json` exposes only `GET /v1/health`. The Expo route uses the five diagnostic strings. A live PostgreSQL catalog query showed exactly one table in `public`, `alembic_version`, at revision `0001_baseline`. `uv run --directory services/api alembic check` found no schema drift. |

## Outcomes

With Docker running, use `pnpm setup` and start `pnpm dev:api` and `pnpm dev:app` in separate terminals. Run `pnpm check` and `pnpm test:e2e` with PostgreSQL up. All local acceptance checks passed. Both development servers stopped after the browser checks, and Compose removed the test container, network and volume. The owner supplied the empty GitHub repository `aydinkaya999/kursu`. The `github.com-orion` SSH alias authenticated as `aydinkaya999`. M0 was published on main. The workflow pins an available setup-uv release after its original major tag failed to resolve.
