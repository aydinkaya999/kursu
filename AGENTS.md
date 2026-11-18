# AGENTS.md — Kürsü

Kürsü is a paid exam-prep app for Türkiye's MEB-AGS teacher-entry exam (exam day: Saturday 8 May 2027). It tells each candidate what to study every day. One codebase ships to **web, iOS and Android**. Questions, lessons and feedback are AI-generated **offline** and imported as content. The app itself never calls an AI model; the only runtime AI feature (photo solve) goes through our API.

This file is the standing guide for coding agents. Keep it short. Detailed specs live in `docs/`.

## Read before you work

| If the task touches… | Read |
|---|---|
| anything | this file and your milestone in `docs/MILESTONES.md` |
| behaviour, rules, limits, priorities | `docs/PRODUCT_SPEC.md` |
| UI | `docs/DESIGN_SYSTEM.md`, `docs/SCREENS.md`, `docs/design/reference/*.html` |
| structure, data model, API, auth | `docs/ARCHITECTURE.md` |
| work longer than about an hour | `.agent/PLANS.md` |

When documents disagree: `PRODUCT_SPEC.md` wins on behaviour, the reference HTML wins on visual detail, `ARCHITECTURE.md` wins on structure. Note the conflict in your plan's Decision Log and continue.

## Stack

- **Client:** TypeScript (strict), React Native + Expo (latest stable SDK, 58 or newer), Expo Router. A single app in `apps/app` serves iOS, Android and web.
- **API:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, PostgreSQL 16.
- **Contract:** the API's OpenAPI document. `packages/api-client` is generated from it. Never edit generated files by hand.
- **Tooling:** pnpm workspaces (Node 22.13 or newer), uv for Python, Docker Compose for local PostgreSQL.

Changing any of these needs a Decision Log entry that says why.

## Repository layout

    apps/app/              Expo app: routes in app/, code in src/
    services/api/          FastAPI service: app/, alembic/, tests/
    packages/api-client/   generated TypeScript client and types
    content/               content JSON Schemas, seed and placeholder content
    docs/                  specs (source of truth)
    .agent/                PLANS.md and plans/

## Commands

These root scripts are created in milestone M0. From then on they must exist and pass.

    pnpm setup         install JS and Python dependencies, start Postgres, run migrations, import seed content
    pnpm dev:api       run the API on http://localhost:8000
    pnpm dev:app       run Expo (press w for web)
    pnpm gen:api       regenerate packages/api-client from the API's OpenAPI document
    pnpm lint          ESLint + Prettier check (app), ruff check + ruff format --check (api)
    pnpm typecheck     tsc --noEmit (app, packages), mypy (api)
    pnpm test          Jest (app), pytest (api)
    pnpm test:e2e      Playwright smoke tests against the web build
    pnpm check         lint + typecheck + test (run this before you finish)

## Working agreements

- Work on one milestone at a time. Do not start the next one unless asked.
- Never invent product behaviour. If the spec is silent, pick the simplest option and mark it `ASSUMPTION:` in your plan's Decision Log and in your final summary.
- Everything the user reads is Turkish and comes from `apps/app/src/i18n/tr.ts`. No user-facing string literals in components. Code, comments, commits and docs are English.
- Use the exact Turkish copy from `docs/SCREENS.md` and the reference HTML. Do not translate, shorten or "improve" it.
- Every screen must work on web, iOS and Android. Prefer shared code; use `.web.tsx` / `.native.tsx` only when a platform API forces it.
- Use theme tokens from `apps/app/src/theme`. No raw hex values, font sizes or radii in screens.
- All business rules (scoring, scheduling, limits, entitlements) are computed on the server. The client displays results.
- The server clock is the only clock for exam timers, due dates and daily limits. Day boundaries use `Europe/Istanbul`.
- Prices, free-tier limits and exam dates come from remote config, never from constants in the client.
- Install Expo-aware packages with `npx expo install`. Add any other dependency only when the platform or an existing dependency cannot do the job, and say why in your summary.
- Write tests with the change: unit tests for every rule in `PRODUCT_SPEC.md` you implement, API tests for every endpoint, component tests for interactive components.
- Database changes go through Alembic migrations. Never edit an applied migration.
- After changing the API, run `pnpm gen:api` and commit the result in the same change.

## Do not

- Do not use, copy or paraphrase real ÖSYM exam questions or publisher material anywhere, including tests and fixtures. Development content is either `content/seed` or generated placeholders marked `is_placeholder: true`.
- Do not build P1 or P2 features unless the milestone says so. They appear in some reference screens; `docs/SCREENS.md` says what to leave out.
- Do not call AI providers from the client. Do not send personal data to an AI provider from the server.
- Do not commit secrets. Configuration comes from environment variables; keep `.env.example` current.
- Do not add analytics, ads or third-party SDKs that are not in the spec.
- Do not use emoji in the UI. Icons are stroke SVGs from the design system.
- Do not weaken lint, type or test settings to make a check pass.

## Definition of done

A milestone is done when:

1. Every acceptance criterion in `docs/MILESTONES.md` is met and you have shown how you verified each one.
2. `pnpm check` passes. `pnpm test:e2e` passes when the milestone has UI.
3. New behaviour has tests. New screens match the reference at 390 px width and stay usable at 1280 px.
4. `README.md`, `.env.example` and any docs you made stale are updated.
5. Your final message lists what changed, how to run it, every `ASSUMPTION:`, and anything left open.

## ExecPlans

For a milestone, or any task that will take more than about an hour, write an ExecPlan first (as described in `.agent/PLANS.md`), save it as `.agent/plans/<milestone>-<slug>.md`, and keep it current while you work.

## Code Review Rules

- Flag business rules computed on the client instead of the server.
- Flag user-facing strings outside `src/i18n/tr.ts` and raw style values outside `src/theme`.
- Flag any endpoint that returns the correct option, rationales or solution steps before the user has answered that question.
- Flag timers or day boundaries that use the device clock.
- Flag content that is neither seed content nor marked as placeholder.
