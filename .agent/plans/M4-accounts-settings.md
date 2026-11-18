# M4 accounts and settings

## Purpose

A candidate can attach an email, Google or Apple identity to their guest, recover an existing account with their work, manage preferences, log out or erase the account. Implements ONB-5, ONB-6, CNT-5 and the privacy section.

## Implementation sequence and progress

- [x] Inspect the M3 sessions, profile, placement data and screen specifications.
- [x] Add identity and one-time challenge storage, email and provider verification, upgrade/merge, logout and deletion.
- [x] Implement sign-in and settings across Expo platforms, regenerate the contract, and document configuration.
- [x] Exercise each provider, concurrent/repeated operations, privacy and settings through API, component and browser tests.

## Decision log

- ASSUMPTION: When both profiles exist the established account's preferences win. Keep both placement histories. If both have unfinished attempts, keep the account attempt active and retain the guest attempt as paused so it can resume afterwards.
- ASSUMPTION: Notification time is unset until chosen. Account deletion asks for confirmation. Legal pages display clearly marked slots until counsel provides the texts.
- Use development email logging and production SMTP behind the same sender. Use configured Google and Apple credentials with signed ID tokens, an expiring nonce and a browser handoff bound to the initiating guest. Provider test credentials stay in the test process.
- Account providers and legal content require operator setup before public release. Account success opens Today until the paywall milestone.

## Validation

Exercise all three sign-up methods with a completed placement, merge into an existing account, retry an upgrade, rotate and revoke credentials, and delete all personal rows. Verify daily minutes, notification settings, disclosure and legal slots on the client. Run the root checks and the shared browser journey at both supported widths.

## Outcomes

The email, Google and Apple API journeys each retained a completed 30-question placement, merged a second guest, rotated credentials, logged out one device and deleted the account. Negative cases cover expiration, attempt limits, signature claims and challenge ownership. Browser signup, preferences, legal slots and deletion passed at both widths. The local checks passed with 49 Jest and 28 pytest cases. Real provider registration, SMTP credentials and counsel-supplied text are deployment inputs. See the Accounts and settings section in README.md.
