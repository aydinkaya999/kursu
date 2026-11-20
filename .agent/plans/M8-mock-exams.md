# M8 mock exams and progress

## Purpose

Deliver timed and practice mocks, editable answers, post-submission review and candidate progress on all three clients. Implement MOCK-1–7 and PROG-1–4 against the mock, result and progress references.

## Implementation sequence and progress

- [x] Read the rules, architecture and reference screens.
- [x] Persist attempts and answers, grade on submission and implement the expiry job.
- [x] Integrate mastery, notebook, plan credit and progress.
- [x] Build the shared screens, generate the client and verify the milestone.

## Decision log

- ASSUMPTION: Starting the same mock in the same mode resumes an unfinished attempt. Submitting freezes its score and credits the matching task for its submission day. Practice time uses actual elapsed time.
- ASSUMPTION: A question withdrawn during an attempt stays in its numbered slot, with its content hidden and excluded from grading. The remaining questions can still be submitted.
- ASSUMPTION: The four-week trend uses weekly estimates on weeks with answers. Empty periods have no data point.

## Validation

Test expiry across reloads and clock changes, job replay, exact net and withheld rationales. Exercise free navigation, flagging, mock completion, progress and the reference layouts at 390 and 1280 px. Run setup, migration drift, client generation, root checks and browser tests.

## Outcomes

All four acceptance criteria passed. The PostgreSQL integration tests cover the official distribution, resumable state, eligibility changes, idempotent deadline submission, quarter-net grading, notebook/plan credit and multi-week progress. The browser journey changes the device clock, reloads, reviews a submitted question and opens progress at 390 and 1280 px. The checked phone screenshot and reference assertions cover the map, timer and result typography.

`pnpm setup`, `alembic check`, `pnpm gen:api`, `pnpm jobs:submit-mocks`, `pnpm check` (61 Jest, 73 pytest) and `pnpm test:e2e` (32) passed. Run the two development servers after setup. Operations must schedule the documented expiry command.
