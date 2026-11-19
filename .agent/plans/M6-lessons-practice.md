# M6 lessons, topic tests and feedback

## Purpose

A candidate can open a lesson or a topic test from Today or Lessons, submit a question, see its rationale and source and return with earned progress. Implements LES-1–4, TEST-1–4, WHY-1–6, CNT-3, CNT-5, D-2 and D-8.

## Implementation sequence and progress

- [x] Inspect content, daily tasks, placement answers, account merging and the three design references.
- [x] Migrate practice sessions, shared answers, mastery, lesson completions and reports. Integrate daily credit and account lifecycle.
- [x] Implement the lessons index, card reader, answering, feedback, remediation and report form.
- [x] Verify the four milestone criteria on PostgreSQL and in Playwright, compare the screens at 390 and 1280 px and document the maths spike.

## Decision log

- ASSUMPTION: A standalone topic test has ten questions. A planned test uses its assigned count. Choose about one third from a neighbouring level, prefer unseen questions and use the nearest available level for a sparse bank.
- ASSUMPTION: A submitted blank skips without revealing feedback or changing mastery. A wrong lesson check returns to its linked card, then advances without grading that answer twice. Reading a completed lesson again keeps its first completion.
- ASSUMPTION: Resume unfinished practice for the same assignment. Completion credits a matching task on the current Istanbul day. A report from the same account counts once per question.
- Preserve M5 completion history during migration. M7 owns the notebook entry and interval workflow. Show the notebook confirmation only when that workflow actually records an entry.
- Keep quarantine on routine offline publication imports, including after erasure of the reporters' data. Reopening an updated lesson starts its current checks and retains the previous answer history.
- Use the existing shared text renderer for the quantitative corpus. Its six-step percentage solution fits the reading column. [Maths notation spike](../../docs/MATH_NOTATION.md)

## Validation

| Acceptance | Verification |
| --- | --- |
| Lessons, remediation and mastery | The API tests read the four-card Law No. 1739 lesson, submit an incorrect check, verify its card position, complete the second check and compare the persisted mastery and completion. Concurrent duplicate submissions earn credit once. Component and browser tests open the article sheet and the linked card. |
| Feedback and topic tests | API tests verify pre-answer fields, five ordered rationales, cited articles, quantitative steps, unsure and blank answers, the third-occurrence suggestion and the D-2 and D-8 thresholds. Completing a test with ten correct answers changes the next test's difficulty mix to seven level-three and three level-two questions. The real seed equation renders at both browser widths. |
| Error reports | After duplicate and simultaneous reports from three distinct users, the open topic test replaces the withdrawn item. The dependent lesson, saved feedback and mock become unavailable. An ordinary re-import still preserves quarantine after reporter data is purged. |
| Today to feedback | At 390 × 844 and 1280 × 800, Playwright opens Today, reads the cards, submits a wrong answer, reloads the feedback, reports it, reopens the related card and finishes the lesson. Today shows earned progress. Further browser coverage completes a planned topic test and verifies the daily streak. Reader and feedback heading metrics match the HTML references. |
| Existing data | An isolated populated M5 database upgrades, downgrades and upgrades again. Two placement answers and a lesson completion replay chronologically to mastery 0.24. The account lifecycle test merges duplicate lesson/report histories, retains an unfinished topic test and checks account erasure. |
| Native journeys | On an iPhone 17 simulator (iOS 26.1) and an Android API 36.1 emulator, opened articles 4 and 8, submitted a wrong check, revisited its linked card, submitted the correct second check and returned to Lessons. Opened a quantitative test, scrolled to its final equation and submitted an error report on each device. An iOS check with the software keyboard exposed a covered submit button. The sheet now moves above the keyboard, and a component test simulates the keyboard frame. Both devices displayed the server receipt. |
| Tooling | `pnpm setup` and `alembic check` passed. Repeat API client generations were byte-identical. `pnpm check` passed with 55 Jest and 56 pytest cases. All 26 Playwright cases passed. Expo exported iOS and Android bundles. |

## Outcomes

Run `pnpm setup`, then `pnpm dev:api` and `pnpm dev:app` in separate terminals. Open Today or Lessons, finish a lesson or topic test and return to the updated plan or library. No new dependencies or environment variables are required.
