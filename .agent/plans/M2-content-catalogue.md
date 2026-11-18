# M2 content model, import and catalogue

## Purpose

A developer can prepare a PostgreSQL question bank with one setup command, import a new offline content bundle, and read the catalogue through the generated client. The six subtests must match section 3 of the product spec. Catalogue reads enforce CNT-1 and protect unanswered questions under WHY-6. Sources stay attached to questions and lessons under CNT-6.

## Implementation sequence and progress

- [x] Inspect the M1 baseline, product rules, database design, sample bundle and setup workflow.
- [x] Add the reference and content tables with a new Alembic revision. Move the fixture to the seed directory and define the versioned JSON Schemas.
- [x] Implement transactional imports, development placeholder generation, the production guard and repeatable setup.
- [x] Expose the read-only catalogue with explicit public response shapes. Regenerate the TypeScript client.
- [x] Run the acceptance checks against PostgreSQL, run the repository checks, and document the commands and results.

## Decision log

- ASSUMPTION: The 31-topic curriculum is only partially supplied. Keep the six supplied topics and fill the development bank with explicitly marked synthetic topics. An unspecified topic weight remains null.
- ASSUMPTION: The unauthenticated catalogue shows published content. A lesson or mock containing an unavailable question is also unavailable, so readers only see complete items. Candidate selection for prerelease needs an authenticated identity.
- Read-only field and mock lists expose the imported reference and mock metadata. Completing a lesson, taking a test and recording progress belong to their respective milestones.
- The importer evaluates the checked-in Draft 2020-12 schema with `jsonschema`. Its development type stubs keep that integration under strict mypy. PostgreSQL foreign keys and transaction checks validate relationships across bundles.
- Use the documented exam order, source data and stable IDs from the sample. Generate mock question positions from the six subtest counts. Store example material in the content pipeline and keep the app UI untouched.

## Validation

| Acceptance or contract | Result |
| --- | --- |
| Setup is idempotent | Two consecutive `pnpm setup` runs produced identical contents and PostgreSQL row versions (`xmin`) in all 12 reference and content tables. Integration tests also verified concurrent retries, a reordered and shortened lesson, stable references to answered questions, and rollback after an invalid import. |
| Six subtests match section 3 | The API test checked all six IDs, display names, short names, order, question ranges and weights. The ranges cover questions 1–80 and the P1 weights in order are 20, 20, 15, 10, 25 and 10. |
| Catalogue enforces CNT-1 and WHY-6 | HTTP tests covered all six catalogue routes. Draft, prerelease, quarantined and retired lessons, mocks and linked questions were hidden from anonymous reads. Direct access to an unavailable lesson returned the same 404 as an unknown ID. Check questions returned exactly `id`, `stem` and `options`. |
| Production refuses placeholders | The production CLI rejected an input containing both genuine seed rows and placeholders, rolled back an earlier file in the invocation, rejected the generator, and accepted the original seed. Tests cover every generated entity type. |
| Content is usable | PostgreSQL tests looked up both questions and lessons by a law article, checked the stored feedback, verified the lesson links and ten questions per topic per difficulty, and checked all 800 mock positions for exam order and uniqueness. A generated JSON file containing 930 questions was imported successfully through the CLI. |
| Repository quality | `pnpm check` passed with 43 Jest and 14 pytest cases. All 14 Playwright cases passed. Alembic reported no drift and the migration upgraded, downgraded and reapplied in a disposable schema. Regenerating the API client reproduced the same file. The generated client read subtests, filtered lessons, a lesson by ID and mock metadata from a live Uvicorn server. |

## Outcomes

Run `pnpm setup` and `pnpm dev:api`, then visit `/v1/docs`. The development catalogue has 31 topics, 32 lessons, 935 questions and ten mocks. The outstanding content dependency for launch is the official curriculum and production content. [Content commands](../../README.md#content-and-catalogue)

Port 5432 on this workstation was in use by another service. The ignored local `.env` uses the isolated Compose project `kursu-m2-verify` on port 55432. Plain setup, API and test commands use that database in this checkout.
