# M5 daily plan, Today and streak

## Purpose

A candidate opens Today for a server-calculated, budgeted plan, starts and completes tasks, and sees day's progress, their streak and five-day weekly goal. Implements PLAN-1–10, STRK-1–4 and defaults D-3, D-4 and D-6.

## Implementation sequence and progress

- [x] Read the scheduling rules and identify the M4 account and settings integration.
- [x] Implement day, task and streak persistence and lazy evaluation by Istanbul date.
- [x] Implement the Today layouts, real task start/completion, and the wide-web summary.
- [x] Check boundary, budget, missed day, recomputation and completion cases, exercise the screens, and run repository checks.

## Decision log

- ASSUMPTION: Rebuilding a plan preserves completed work and its earned streak credit. Redistribute missed topic work across future study days within the original daily budget. On near-exam study days use previously opened topics and due reviews. Sunday stays the full mock day. Completed activities beyond a reduced budget remain visible separately.
- ASSUMPTION: Before the activity-specific flows ship, opening a task shows its assignment and an explicit completion action. Detailed lesson, practice, notebook and mock flows belong to M6–M8.
- ASSUMPTION: Placement answers supply initial mastery and first due reviews. Use previously completed activities to identify opened topics. Show the four-week change when both 28-day windows have evidence.
- Match the phone and wide Today references. Omit the photo and nationwide tiles. Use actual server evidence for the net and mastery panel.

## Validation

| Acceptance | Verification |
| --- | --- |
| PLAN-1–10 and STRK-1–4 | `services/api/tests/test_plan.py` checks the 30-day boundary, due work from actual answers, topic order, immediate recomputation, concurrent completion, missed days, Istanbul midnight, the Monday week reset and five-day cap. The Today component tests cover the next action and completion copy. |
| Time budget | The unit tests cover 30, 60 and 90 minutes with no reviews, six reviews and an overloaded queue. They check the 40% review cap, lesson and question costs, the single 110-minute Sunday mock and preserving past work after downsizing. Combining two completed histories preserves one Sunday mock and at most two active daily lesson slots. |
| Missed assignments | Reproduced three missed assignments all returning the next day through normal topic selection. The scheduler now excludes reserved assignments until each one's turn. A PostgreSQL API test observes the three assignments on three different days, including after a same-day budget edit. |
| Today, progress and retention | Playwright changed the budget, opened and finished every assignment, verified each percentage and the streak and reloaded the page at both widths. API tests verify that overlapping guest/account tasks receive credit once and that withdrawn lessons are replaced. |
| Reference and scope | Compared the 390 × 844 phone and 1280 × 800 web screens with the Today references. The desktop adds the net and weakest-subtest panels. Playwright checks heading metrics and the absence of photo solve and nationwide mocks. |
| Native screens | On an iPhone 17 simulator and Android API 36.1 emulator, chose a field, completed the next lesson, returned to the updated plan and saved a 30-minute budget. On both platforms, registered with the test mailbox code, opened the signed-in settings, confirmed account deletion and returned to onboarding. |
| Repository | `pnpm setup`, `alembic check` and the M3→M5→M3→M5 migration check passed. Two client generations were byte-identical. `pnpm check` passed with 52 Jest and 47 pytest cases. All 22 Playwright cases passed. Expo exported both native bundles. |

## Outcomes

Run `pnpm setup`, then `pnpm dev:api` and `pnpm dev:app` in separate terminals. After choosing a field, open Today from onboarding or the placement result. Open an assignment, record completion and return to Today. Settings can change the budget for an existing plan on the same day. Scored lesson checks, topic practice, spaced repetition and timed mocks belong to M6–M8.
