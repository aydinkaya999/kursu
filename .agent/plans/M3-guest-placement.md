# M3 guest onboarding and placement

## Purpose

A new candidate can choose a field and study time, take the adaptive placement test across visits and see a net range, six ranked subtests and a first-week preview without signing up. The server owns the exam countdown, placement decisions and retake dates. This milestone covers ONB-1–4, PLC-1–7, D-1 and the question disclosure boundary in WHY-6.

## Implementation sequence and progress

- [x] Inspect the M2 content bank, product rules, routes and the three HTML references.
- [x] Add guest credentials, profile, server config, placement attempts and answers with a new migration.
- [x] Implement atomic start, resume and answer operations, scoring, preview and retake eligibility. Generate the client.
- [x] Implement the three shared Expo screens, persistent guest identity and entry points from Today.
- [x] Exercise rule and API tests, interactive components, the complete web flow at both widths, and native verification. Record results and update setup documentation.

## Decision log

- ASSUMPTION: Cycle through the subtests while their quotas remain. The short test uses education 3, verbal 2, quantitative 2, and one each for legislation, history and geography. A blank preserves the current difficulty. A marked answer advances according to correctness.
- ASSUMPTION: Count the 14-day retake interval from the most recent completion using Istanbul calendar dates. Rank ties in exam order. The preview uses one weak topic from each of the three weakest subtests and the configured mock day.
- ASSUMPTION: Prefer previously unseen questions when retaking the test. For otherwise equal questions and focus topics, prefer seed content, then stable ID order. Round a half net up before clamping the estimate.
- The onboarding reference illustrates a selected field. The screen spec requires the candidate to choose it. The result reference links directly to the paywall, while the route spec sends the primary action to auth. M3 provides the auth destination and guest continuation. Account providers and purchases belong to M4 and M9.
- Guest persistence requires renewable credentials before M4. PyJWT signs and validates the 15-minute access token. Zustand keeps it in memory as specified by the architecture. Expo SecureStore persists the rotating native refresh token and Expo Crypto generates answer IDs on all three platforms. The browser uses an HttpOnly cookie.

## Validation

| Acceptance | Verification |
| --- | --- |
| Guest completes onboarding and a 30-question test | Playwright exercised both onboarding exits, persisted choices, browser reload, all 30 answers and the account or guest exit at 390 and 1280 px. Maestro ran the complete journey using Expo Go on an iPhone 17 simulator (iOS 26.1) and an Android API 36.1 emulator. Each reopened at question 2, reached the 27–33 result after 30 blanks, viewed the first-week preview and returned to Today. After terminating and relaunching the app, both recovered the same result. |
| Distribution, adaptivity and resume | PostgreSQL-backed tests checked all 30 full and 10 short positions, per-subtest level changes, blank and unsure submissions, duplicate concurrent requests, guest ownership and resume. Withdrawing or changing an assigned question preserved the position. When the next question was unavailable, restoring content and retrying saved exactly one answer. |
| Range, ranking, plan and retake | Rule tests covered the D-1 formula, rounding, clamping and subtest weights. API tests checked all six ranked rows, the two priorities, three plan topics, minutes, mock day, historical answer cutoff and the opening of the retake at Istanbul midnight. The countdown test checked the transition one second before and exactly at midnight. |
| Private question data | Every item on both tests was checked for exactly `id`, `stem` and the five `options`. Playwright independently checked the first response seen by the browser. |
| Design | Compared screenshots of all three screens against the supplied references at 390 px. Playwright checks the form action, question option and result heading against the HTML and saves screenshots at both widths. |
| Repository | `pnpm setup` succeeded on the existing M2 database. Alembic upgraded, downgraded to M2 and reapplied in a disposable schema, then reported no drift. Two generations of the typed client matched byte for byte. `pnpm check` passed with 47 Jest and 23 pytest cases. All 18 Playwright cases passed. Expo exported both native platforms. |

## Outcomes

Run `pnpm setup`, then start `pnpm dev:api` and `pnpm dev:app` in separate terminals. Open the root route. The onboarding choices, current question and estimated result belong to the guest on the server. An eligible guest can start the short retake from Today.

Product review still covers the P1 and P3 score explanations marked NEW in the screen spec, plus the field prompt, Today actions and temporary account-entry copy in the Turkish catalogue. Email, Google and Apple account registration are scheduled for M4.
