# Architecture — Kürsü

One Expo app (iOS, Android, web) talks to one FastAPI service over a versioned REST API. PostgreSQL is the only data store. Content is produced offline and imported. The server computes every rule; the client renders.

    apps/app (Expo, TypeScript)  ──HTTPS /v1──▶  services/api (FastAPI)  ──▶  PostgreSQL
                    ▲                                    ▲
       packages/api-client (generated)        content/ (JSON, imported by CLI)

## 1. Repository

    apps/app/
      app/                  Expo Router routes (see docs/SCREENS.md)
      src/components/       design-system components
      src/features/<name>/  screens' logic, hooks and feature components
      src/theme/            colours, typography, spacing, shadows
      src/i18n/tr.ts        every user-facing string
      src/lib/              api client setup, auth, storage, time, formatting
      e2e/                  Playwright tests (web)
    services/api/
      app/main.py, app/core/ (settings, db, security, errors, time)
      app/modules/<name>/   router.py, schemas.py, models.py, service.py
      app/cli.py            import-content, make-placeholders, jobs
      alembic/, tests/
    packages/api-client/    generated from the API's OpenAPI document
    content/schema/         JSON Schemas for content files
    content/seed/           hand-written sample content
    docker-compose.yml      PostgreSQL for development and tests
    .github/workflows/ci.yml

## 2. Client

- Expo Router with typed routes. Tabs on phones; side navigation on web from 1024 px.
- Server state with TanStack Query through the generated client. No hand-written fetch calls or response types.
- Small client state (session, selected options before submit) in Zustand. Nothing that the server owns is cached as truth.
- Styling with `StyleSheet` and the theme tokens. No CSS-in-JS library and no Tailwind.
- Strings from `src/i18n/tr.ts` with typed keys. Formatting helpers in `src/lib/format` (numbers, dates, suffixes).
- API base URL from `EXPO_PUBLIC_API_URL`.
- No offline mode in the first release: without a connection, screens show the offline state and retry.
- Time: the client keeps the offset between its clock and the server's (`server_now` in responses) and uses it for countdowns.
- Tests: Jest with `jest-expo` and React Native Testing Library; Playwright for web end-to-end.

## 3. API

- FastAPI with async SQLAlchemy 2 and Alembic. Settings through environment variables.
- All routes under `/v1`. JSON in and out, `snake_case` fields. Timestamps are UTC ISO 8601; dates are `YYYY-MM-DD` in Europe/Istanbul.
- Errors: `{ "code": "...", "message": "...", "details": {} }` with the matching HTTP status. Codes include `unauthenticated`, `forbidden`, `not_found`, `validation_error`, `conflict`, `free_limit_reached`, `entitlement_required`, `rate_limited`. On `free_limit_reached` the client opens the paywall.
- Answer submissions carry a client-generated id and are idempotent.
- Rules live in `service.py` files as pure functions where possible, each tested under its rule id.
- Scheduled work runs as idempotent CLI commands called by an external scheduler: submit expired mock attempts, delete expired photos. No queue or worker in the first release.
- The daily plan and the streak are evaluated lazily on the first request of the day.

## 4. Data model

Primary keys are UUIDs unless noted. Content rows use stable string ids (slugs) so imports are repeatable.

| Group | Tables and key columns |
|---|---|
| Accounts | `users` (is_guest, created_at, deleted_at) · `identities` (user_id, provider email/google/apple, subject) · `refresh_tokens` (user_id, token_hash, expires_at, revoked_at) · `email_codes` (email, code_hash, expires_at, attempts) · `profiles` (user_id, field_id, score_type, daily_minutes, attempt_kind first/repeat, notification_time) |
| Reference | `fields` (id, name, score_type) · `subtests` (id, name, short_name, question_count, exam_order, weight_p1) · `remote_config` (key, value jsonb) |
| Content | `topics` (id, subtest_id, name, exam_weight) · `objectives` (id, topic_id, text) · `misconceptions` (id, topic_id, text) · `lessons` (id, topic_id, title, minutes, source jsonb, status) · `lesson_cards` (lesson_id, position, kind, title, blocks jsonb, tip) · `questions` (id, subtest_id, topic_id, objective_id, difficulty 1–3, stem, options jsonb A–E, correct_option, rationales jsonb per option with misconception_id, solution_steps jsonb, source jsonb, status, is_placeholder) · `lesson_check_questions` (lesson_id, question_id, card_position) · `mock_exams` (id, title, status, published_at) · `mock_exam_questions` (mock_exam_id, position 1–80, question_id) |
| Study | `placement_attempts` (user_id, kind full/short, state, level per subtest jsonb, result jsonb) · `practice_sessions` (user_id, type topic_test/review/lesson_check, topic_id, state) · `answers` (user_id, question_id, session ref, selected_option nullable, is_correct, not_sure, client_answer_id unique, answered_at) · `mastery` (user_id, topic_id, value, answers_count, state) · `mistake_entries` (user_id, objective_id, misconception_id nullable, first_question_id, interval_index, due_on, correct_streak, status open/learned) · `lesson_completions` (user_id, lesson_id, completed_at) |
| Plan | `daily_plans` (user_id, plan_date, daily_minutes, completed_at) · `plan_tasks` (plan_id, position, type review/lesson/topic_test/mock, ref jsonb, est_minutes, state) · `streaks` (user_id, current, longest, last_completed_on, freeze_used_week) |
| Mock | `mock_attempts` (user_id, mock_exam_id, mode timed/practice, started_at, deadline_at, submitted_at, result jsonb) · `mock_answers` (attempt_id, question_id, selected_option nullable, flagged, updated_at) |
| Commerce | `entitlements` (user_id, kind season_pass, valid_until, source web/ios/android, provider_ref) · `purchases` (user_id, provider, provider_ref, amount, currency, state) · `price_assignments` (user_id, price_group) · `usage_counters` (user_id, counter, period, count) |
| Operations | `content_reports` (user_id, question_id or photo_solution_id, text, created_at) · `analytics_events` (user_id, name, props jsonb, occurred_at) · `photo_solutions` (P1) |

## 5. Endpoints

| Area | Endpoints |
|---|---|
| System | `GET /v1/health` · `GET /v1/config` (app name, exam date, results date, server_now) |
| Auth | `POST /v1/auth/guest` · `POST /v1/auth/email/start` · `POST /v1/auth/email/verify` · `POST /v1/auth/google` · `POST /v1/auth/apple` · `POST /v1/auth/refresh` · `POST /v1/auth/logout` · `DELETE /v1/me` |
| Profile | `GET /v1/me` · `PATCH /v1/me/profile` · `GET /v1/fields` |
| Placement | `POST /v1/placement` (start or resume; returns the next question) · `POST /v1/placement/{id}/answers` · `GET /v1/placement/{id}/result` |
| Plan | `GET /v1/plan/today` · `GET /v1/plan/first-week` · `POST /v1/plan/tasks/{id}/start` |
| Catalogue | `GET /v1/subtests` · `GET /v1/topics` · `GET /v1/lessons` · `GET /v1/lessons/{id}` · `POST /v1/lessons/{id}/complete` |
| Practice | `POST /v1/practice-sessions` · `GET /v1/practice-sessions/{id}` · `POST /v1/practice-sessions/{id}/answers` (returns the feedback) · `POST /v1/practice-sessions/{id}/finish` |
| Notebook | `GET /v1/notebook?group_by=topic\|misconception` · `GET /v1/notebook/summary` |
| Mock | `GET /v1/mocks` · `POST /v1/mocks/{id}/attempts` · `GET /v1/mock-attempts/{id}` · `PUT /v1/mock-attempts/{id}/answers/{question_id}` · `POST /v1/mock-attempts/{id}/submit` · `GET /v1/mock-attempts/{id}/result` · `GET /v1/mock-attempts/{id}/review` |
| Progress | `GET /v1/progress` |
| Commerce | `GET /v1/paywall` · `GET /v1/entitlements` · `POST /v1/purchases/web/checkout` · `POST /v1/purchases/native/verify` · `POST /v1/webhooks/{provider}` |
| Operations | `POST /v1/content-reports` · `POST /v1/events` |
| Photo (P1) | `POST /v1/photo-solutions` · `GET /v1/photo-solutions/{id}` |

Question payloads sent before an answer contain the stem and options only. The correct option, rationales, steps and source are returned by the answer endpoint, and by the mock review endpoint after submission (WHY-6, MOCK-7).

## 6. Authentication

- First launch calls `POST /v1/auth/guest`. A guest is a real user row with `is_guest = true`.
- Sign-up attaches an identity to the same user row and clears `is_guest` (ONB-6). If the identity already belongs to another account, the guest's study data is merged into that account once, then the guest row is deleted.
- Email uses a 6-digit one-time code: valid 10 minutes, 5 attempts. Sending goes through an `EmailSender` interface; the development implementation logs the code.
- Google and Apple: the client obtains an ID token; the server verifies it and issues a session.
- Access token: JWT, 15 minutes, sent as `Authorization: Bearer`. Refresh token: opaque, 30 days, rotated on use, stored hashed.
- Native keeps the refresh token in secure storage. Web receives it as an `HttpOnly`, `Secure`, `SameSite=Lax` cookie and keeps the access token in memory only. CORS allows the app origin with credentials.
- `DELETE /v1/me` deletes the account and its personal data.

## 7. Content

- Offline bundles use the versioned JSON Schema in `content/schema/`. The canonical example is `content/seed/sample-content.json`. The seed configuration is in `content/seed/config.json`.
- `import-content` is idempotent: it upserts by id and never deletes rows that have answers.
- `make-placeholders` generates enough clearly fake questions, lessons and mocks to exercise every flow (placement needs every subtest at all three difficulty levels; a mock needs 80). Placeholders carry `is_placeholder = true`, start with "[ÖRNEK]" in the stem, and are refused by the importer when `APP_ENV=production`.
- Text is plain text with line breaks. Fractions are written `a/b`. Whether maths needs a richer notation is decided by a spike in M6.
- Status values: `draft`, `prerelease`, `published`, `quarantined`, `retired` (CNT-1, CNT-2).

## 8. Entitlements, limits and remote config

- `entitlements` is the only source of access. The client asks the server; it never decides locally.
- Free-tier limits are enforced on the server with `usage_counters` and returned in `GET /v1/paywall` for display.
- `remote_config` holds: app name, exam date, results date, free-tier limits, web price groups, mock day, review intervals.
- Web price group (PAY-5) is assigned once per user, at random with equal weights, and stored in `price_assignments`.
- Payments are not chosen yet. Define two interfaces, `WebCheckoutProvider` and `NativePurchaseVerifier`, with fake implementations for development and tests. The fake web provider completes a purchase immediately in development only.

## 9. Analytics

First-party only. The client posts batches to `POST /v1/events`; the server also writes events it knows about. Names: `signup_completed`, `placement_started`, `placement_completed`, `paywall_viewed` (with `source`: placement, limit, mock_result), `purchase_completed`, `plan_task_started`, `plan_task_completed`, `day_completed`, `mock_started`, `mock_submitted`, `content_report_created`.

## 10. Photo solve (P1)

`POST /v1/photo-solutions` accepts an image. A `VisionSolver` interface returns extracted text, steps, answer, confidence and the related topic. The stub returns a canned result. The service enforces PHOTO-3 to PHOTO-6: confidence threshold, scope check, limits, no reuse, deletion after 30 days. The request to the provider contains no user identifiers.

## 11. Configuration

`.env.example` lists every variable with a safe default: `APP_ENV`, `DATABASE_URL`, `JWT_SECRET`, `APP_ORIGIN`, `EMAIL_SENDER`, `GOOGLE_CLIENT_IDS`, `APPLE_AUDIENCES`, `BUSINESS_TIMEZONE` (`Europe/Istanbul`), `EXPO_PUBLIC_API_URL`.

## 12. Testing

- API: pytest against a real PostgreSQL database from Docker Compose. One test at least per rule id, named `test_<rule id>_<what>`, for example `test_nb_4_wrong_answer_resets_interval`.
- App: unit tests for formatting helpers (including Turkish suffixes) and component tests for interactive components.
- Web end-to-end with Playwright: onboarding → placement → result; Today → lesson → question → notebook; mock start → answer → submit → result.
- CI runs `pnpm check` and `pnpm test:e2e` on every push.

## 13. Assumptions to confirm

These were decided to unblock the build. The product owner may change them.

1. Email sign-up uses a one-time code, not a password.
2. Web keeps the refresh token in an `HttpOnly` cookie.
3. No offline mode in the first release.
4. Mock day is Sunday and ignores the daily time limit (D-4).
5. Scheduled work runs as CLI jobs, with no queue.
6. Payment providers for web and for in-app purchase are not chosen.
7. The AI provider for photo solve is not chosen.
8. Maths is plain text until the M6 spike.
9. Hosting, regions and data residency are not decided.
