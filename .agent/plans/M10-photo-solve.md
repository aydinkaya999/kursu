# M10 — Photo solve

## Purpose

Candidates can take or select a question photo on web, iOS and Android, see a private step-by-step result and open its related micro-lesson. The Today tile and season-pass comparison expose the server's allowance. Follow PHOTO-1–6, CNT-3, the photo screen and the Today and paywall references.

## Implementation sequence and progress

- [x] Read the milestone, screen references, product/privacy rules, account lifecycle and commerce counters.
- [x] Add the private file store, migration, solver boundary, quota, reporting and retention command.
- [x] Add capture, upload, outcomes, lesson navigation, reporting, Today and paywall views.
- [x] Cover the rules, ownership, failure recovery, native controls and browser journeys with tests.
- [x] Regenerate the API client and migrate existing databases.
- [x] Verify phone and desktop browser journeys and export both mobile bundles.
- [x] Finish the combined local checks before integrating on main.

## Decision log

- ASSUMPTION: A processed photo uses one allowance, including either refusal. Cancellation, invalid data, technical failures and retries of the same retained submission use no additional allowance.
- ASSUMPTION: Start the configurable confidence threshold at 0.75. Use an explicitly marked original demonstration solution in development/test. Keep production solving unavailable until a vision provider is configured.
- ASSUMPTION: Accept still JPEG, PNG and WebP input up to 10 MiB and 32 megapixels. Retain a metadata-free JPEG in a private shared directory. Expire its result and report with its image and remove photos on account deletion.

## Validation

- PHOTO-1–4 and CNT-3 passed in `tests/test_photos.py` and `apps/app/tests/photo.test.tsx`. The solver receives only normalized pixels. API responses suppress proposed answers below the threshold and outside AGS. UI tests open the published related lesson and submit a private report. Android activity recovery and native permission/cancellation are exercised with picker test doubles.
- PHOTO-5 passed with concurrent requests for the last free and paid slot, duplicate submissions, guest-to-account merge, remote changes and Istanbul midnight. An M9 upgrade test verifies that existing operator values survive.
- PHOTO-6 passed with two independent users, the original question bank, EXIF removal, account erasure and a simulated clock one second before and at the retention deadline. A cleanup interruption and an in-flight write were tested against real files and PostgreSQL.
- `pnpm setup`, `pnpm gen:api`, `pnpm jobs:delete-photos` and `alembic check` passed. The generated client and permission copy reproduce from their sources.
- `pnpm check` passed with 70 Jest tests and 95 pytest cases, including the ownership, quota, retention and upgrade tests.
- All 40 Playwright journeys passed across 390 and 1280 px. The photo tests use a generated question image and a simulated browser camera, verify camera release, reload the private link, report the result, navigate to the lesson and check the updated Today allowance. The photo screenshots were checked against the reference.
- Release exports completed for iOS and Android. Expo config introspection verified the native permission copy and microphone configuration.

## Outcomes

Run `pnpm setup`, then `pnpm dev:api` and `pnpm dev:app`. Open the photo tile on Today. Expo ImagePicker provides native capture and the file picker. Pillow decodes, validates, strips image metadata and creates private previews. These capabilities are new dependencies.

Production solving requires a vision provider, a private persistent volume shared by the API and the scheduled `pnpm jobs:delete-photos` command. The numbered milestone delivers the stub specified by the roadmap. The README documents the configuration and invocation.
