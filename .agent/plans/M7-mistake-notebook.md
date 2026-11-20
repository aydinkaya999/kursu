# M7 mistake notebook and spaced repetition

## Purpose

Preserve mistakes and uncertain answers from placement and practice, show them by topic or misconception, and review them with sibling questions from the notebook or Today. Implement NB-1–6 and D-5 using Istanbul dates, the server clock and the existing feedback flow.

## Implementation sequence and progress

- [x] Read the M7 requirements, notebook reference, content contract, practice sessions and M5 plan.
- [x] Migrate and backfill entries, integrate answer writes, scheduling and account lifecycle.
- [x] Add grouped notebook reads, sibling review sessions, notebook access and earned plan credit.
- [x] Implement the shared screen, feedback confirmation and entry points.
- [x] Verify the API, migration, layout, browser journeys and final repository checks.

## Decision log

- ASSUMPTION: An entry represents the same objective and recorded misconception. Answers without a recorded misconception share an unclassified group. A new mistake reopens a learned entry. A repeat mistake does not postpone work already due.
- ASSUMPTION: A correct review advances even when marked unsure. A blank review leaves the schedule unchanged and earns no review credit. Marking a blank unsure still records the uncertainty. An early review uses the same intervals as a due review. Reopening the same group or plan assignment resumes its unfinished review. Overlapping sessions skip entries already changed by another answer.
- Keep the reference row’s open-count badge and show each group’s learned count, including zero, after its next review date to meet the M7 acceptance criterion.
- NB-3 requires a different question. Keep an entry pending when the bank has no eligible sibling. Prefer unseen siblings and then the least recently seen. The notebook can start a review of a single group.
- The free notebook is view-only in the product and screen specs. Implement the server season-pass check and the review access screen here. Checkout, pricing and general limit enforcement belong to M9.
- Historical M5 manual review credit remains in the plan. Only an actual review answer counts towards a learned streak. Near the exam use the shortened schedule and cap open dates, including entries first scheduled outside the final fortnight.

## Validation

| Criterion | Verification |
| --- | --- |
| NB-1 and existing answers | The capture matrix covers wrong, correct, blank and unsure combinations. Authenticated placement and lesson submissions populate the notebook. A repeated answer ID keeps a single entry. The M5-to-head migration test exercises historical answers and repeated upgrades. Merged guests retain one combined notebook and the valid pass. Deletion removes both. |
| NB-2 and group dates | Unit and API cases group by topic and misconception, including unclassified answers. They check counts and earliest open dates. The shared component displays the server’s relative date, the open badge and the learned count. Learned-only groups have no pending review action. |
| NB-3 and earned plan credit | API cases verify ownership, pre-answer payloads, scoped resume, original-item exclusion, quarantine replacement and the absence of a fallback to the original. Overlapping notebook and Today sessions skip stale slots. Only a graded answer to each assigned entry earns credit. |
| NB-4, NB-5 and NB-6 / D-5 | Pure rules cover all interval values, three consecutive correct answers, resets, reopening and blank reviews. API cases cross Istanbul midnight and the pass expiry date. Changing the remote exam date brings an existing entry forward before the exam. |
| Shared screen | Playwright runs the lesson-to-notebook, grouped free access, paid Today and early-review journeys at 390 and 1280 px. It compares header, status panel and row styles to the notebook reference. |

`pnpm setup` applied the migration and seeded the development bank. `alembic check` found no schema drift. `pnpm gen:api` regenerated the shared contract. `pnpm check` passed with 59 Jest and 70 pytest cases. All 30 Playwright cases passed. Expo exported the production iOS and Android bundles.

## Outcomes

Run `pnpm setup`, then `pnpm dev:api` and `pnpm dev:app` in separate terminals. Open **Yanlış defteri** from Today or an answer’s feedback. The README includes the local season-pass fixture. The same generated client and shared screen serve web, iOS and Android. No new dependencies or environment variables are required.
