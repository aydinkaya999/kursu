# Milestones — Kürsü

Run one milestone per Codex task, in order. Each milestone ends with working software, passing checks and an updated ExecPlan. Rule ids refer to `docs/PRODUCT_SPEC.md`.

| # | Milestone | Priority |
|---|---|---|
| M0 | Repository scaffold and tooling | P0 |
| M1 | Design system and app shell | P0 |
| M2 | Content model, import and placeholders | P0 |
| M3 | Guest, onboarding, placement test and result | P0 |
| M4 | Accounts and settings | P0 |
| M5 | Daily plan, Today, streak | P0 |
| M6 | Lessons, topic tests, feedback, error reports | P0 |
| M7 | Mistake notebook and spaced repetition | P0 |
| M8 | Mock exam, result, progress | P0 |
| M9 | Free-tier limits, paywall, entitlements | P0 |
| M10 | Photo solve | P1 |
| later | Nationwide mock, badges and league, real payment providers, push notifications | P2 and operations |

## M0 — Repository scaffold and tooling

Scope: pnpm workspace; Expo app in `apps/app` (TypeScript strict, Expo Router) that runs on web, iOS and Android; FastAPI service in `services/api` with settings, database session, Alembic and `GET /v1/health`; Docker Compose for PostgreSQL; OpenAPI → `packages/api-client` generation; every root command in `AGENTS.md`; lint, format, type and test configuration for both sides; one Playwright smoke test; GitHub Actions workflow; `README.md` and `.env.example`.

Acceptance:
- From a clean clone, `pnpm setup` then `pnpm dev:api` and `pnpm dev:app` start without errors.
- The app's start screen calls `GET /v1/health` through the generated client and shows the result on web.
- `pnpm check` and `pnpm test:e2e` pass locally and in CI.
- `pnpm gen:api` produces no diff when the API has not changed.
- No product tables, screens or copy beyond the health check.

## M1 — Design system and app shell

Reference: `docs/DESIGN_SYSTEM.md`, all files in `docs/design/reference/`.

Scope: theme tokens; Plus Jakarta Sans loading; icon set; every component in the design system table; `src/i18n/tr.ts` with typed keys; formatting helpers including the Turkish number suffix helper; navigation shell with four tabs on phones and side navigation on wide web; a development-only gallery route that shows every component in every state.

Acceptance:
- The gallery shows each component and state; side by side with the reference files the components match in size, colour, radius and type.
- Tab bar below 1024 px, side navigation from 1024 px, on web.
- Suffix helper tests cover every row of the table in `DESIGN_SYSTEM.md`.
- No raw hex values or font sizes outside `src/theme`; a lint rule or test enforces it.

## M2 — Content model, import and placeholders

Scope includes reference and content tables, JSON Schemas, the `import-content` and `make-placeholders` commands, the sample seed in `content/seed/sample-content.json`, and catalogue endpoints.

Acceptance:
- `pnpm setup` imports the seed and generates placeholders; running it twice changes nothing.
- The six subtests match the table in `PRODUCT_SPEC.md` section 3.
- Catalogue endpoints never return `quarantined`, `retired` or `draft` content (CNT-1).
- The importer refuses placeholders when `APP_ENV=production`.

## M3 — Guest, onboarding, placement test and result

Reference: `onboarding.html`, `placement-test.html`, `placement-result.html`. Rules: ONB-1 to ONB-4, PLC-1 to PLC-7, D-1.

Scope: guest auth; profile; fields; placement engine (distribution, three levels, resume, short retake); net estimate range; first-week plan preview; the three screens; countdown from server time.

Acceptance:
- A new visitor completes onboarding and the 30-question test and sees the result without an account, on web, iOS and Android.
- Distribution and adaptivity follow PLC-1 and PLC-2; an interrupted test resumes at the same question.
- The result shows a range, the six subtests weakest first, and a first-week plan.
- Question payloads contain no correct option (WHY-6).
- Playwright covers onboarding → placement → result.

## M4 — Accounts and settings

Rules: ONB-5, ONB-6, privacy section. Screens: sign up / sign in, settings (not designed).

Scope: email one-time code, Google and Apple sign-in; token refresh; guest-to-account upgrade and merge; logout; account deletion; settings for daily time and notification time; the AI-content disclosure (CNT-5).

Acceptance:
- A guest with placement results signs up by each of the three methods and keeps all data.
- Signing in with an identity that already has an account merges once and leaves no duplicate data.
- Refresh rotation works; a reused refresh token is rejected.
- Account deletion removes personal data and signs the user out.

## M5 — Daily plan, Today, streak

Reference: `today.html`, `web-today.html`. Rules: PLAN-1 to PLAN-10, STRK-1 to STRK-4, D-3, D-4, D-6.

Scope: plan builder; plan and task endpoints; Today on phone and wide web; streak and weekly goal.

Acceptance:
- Unit tests prove each PLAN and STRK rule, including recomputation on a changed daily time, redistribution after a missed day, and the last-30-days rule.
- Total task time never exceeds the daily time except on mock day.
- Today lists the server's tasks, highlights the next one, and updates when a task is finished.
- P1 and P2 elements of the references are absent.

## M6 — Lessons, topic tests, feedback, error reports

Reference: `micro-lesson.html`, `placement-test.html`, `question-review.html`. Rules: LES-1 to LES-4, TEST-1 to TEST-4, WHY-1 to WHY-6, CNT-3, CNT-5, D-2, D-8.

Scope: lessons index; lesson reader with check questions; practice sessions; answer endpoint with feedback; mastery updates; misconception counter; error report form and automatic quarantine. Includes a short spike on maths notation with a written recommendation.

Acceptance:
- A lesson can be read to the end; a wrong check answer shows the related card again; finishing updates mastery.
- After answering, the chosen option's rationale is first, the source is shown, and quantitative questions list steps.
- Three reports from different users quarantine a question and it stops being served.
- Playwright covers Today → lesson → question → feedback.

## M7 — Mistake notebook and spaced repetition

Reference: `mistake-notebook.html`. Rules: NB-1 to NB-6, D-5.

Scope: notebook entries from answers; grouping by topic and misconception; review sessions with sibling questions; scheduling; notebook screen; review task in the plan.

Acceptance:
- Unit tests prove each NB rule, including the near-exam schedule.
- A review never repeats the question that created the entry while a sibling exists.
- The notebook shows open and learned counts and the next review date per group.

## M8 — Mock exam, result, progress

Reference: `mock-exam.html`, `nationwide-result.html`, `progress.html`. Rules: MOCK-1 to MOCK-7, PROG-1 to PROG-4.

Scope: mock index; attempts in timed and practice mode; answer saving; question map; server deadline and automatic submission; result with net, subtest breakdown, time used and topic distribution of wrong answers; review after submission; progress screen.

Acceptance:
- The deadline holds across app restarts and device clock changes; an expired attempt is submitted by the job.
- `net` equals correct minus a quarter of wrong, per subtest and in total, shown with a decimal comma.
- No rationale is available before submission.
- Progress shows the net range, four-week change, subtest mastery, topic map and mock history; P2 tiles are absent.

## M9 — Free-tier limits, paywall, entitlements

Reference: `paywall.html`. Rules: PAY-1 to PAY-7, D-7.

Scope: usage counters and limit enforcement; `free_limit_reached` handling; paywall with server-driven values; price group assignment; entitlement checks; purchase interfaces with fake providers; the three paywall entry points.

Acceptance:
- Each free-tier limit in `PRODUCT_SPEC.md` section 5 is enforced by the server and covered by a test.
- A candidate always sees the same web price; the three groups are assigned evenly.
- A fake purchase grants the season pass until results day on all platforms for that account.
- No price, limit or date is a client constant.

## M10 — Photo solve (P1)

Reference: `photo-solve.html`. Rules: PHOTO-1 to PHOTO-6.

Scope: image capture and upload on all three platforms; `VisionSolver` interface with a stub; limits; label; refusal paths; deletion job; the photo tile on Today and the paywall row.

Acceptance:
- Limits, the low-confidence path and the out-of-scope path are covered by tests.
- Images are stored outside the database and deleted by the job after 30 days.
- Nothing from a photo reaches the question bank or another user.
