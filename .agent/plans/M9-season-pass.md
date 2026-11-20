# M9 season pass and free access

## Purpose

Apply PAY-1–7 and D-7 across all clients. Guests can use the free allowance and an account can unlock the season through a development checkout. Show the paywall after placement, at a limit and on a mock result.

## Implementation sequence and progress

- [x] Read the product limits, commerce interfaces and paywall reference.
- [x] Persist balanced price allocation, usage and verified purchases. Preserve existing study history across upgrades and account merges.
- [x] Enforce limits at the API and connect contextual paywall, sign-in and checkout.
- [x] Verify concurrent requests, rollover, expiry, purchases on each platform and the three UI entry points.

## Decision log

- ASSUMPTION: A lesson or topic-test position counts on first access that Istanbul day. Reopening the same one is free. Starting either mock mode uses one allowance for this exam season, and resuming it uses none.
- ASSUMPTION: Free progress includes estimated net, its change, subtest percentages and streak. The topic map, trend chart and progress history require the pass. A candidate can always reopen their own mock results from the mock index.
- ASSUMPTION: Preserve the first quoted web amount. Allocate new accounts randomly among the least populated groups. An existing account's quote wins on guest merge. Native fake storefronts use separately configurable TRY prices.
- Real providers and production webhooks are deferred by the milestone. The fake providers are enabled only in development and test. Native test receipts are signed for the account, platform and season.

## Validation

| Acceptance criterion | Verification |
| --- | --- |
| Free-tier limits and D-7 | Authenticated API tests cover the first three calendar days, concurrent lessons, five questions, the last allowed answer and its rationale, repeat reads, the midnight reset and both mock modes. They also check free notebook viewing, the gated review, summary progress, streak and reporting. A migration test replays existing topic positions, completed or opened lessons and mock starts. |
| Stable and balanced web prices | Nine concurrent candidates fill the three groups evenly. Changing the configured prices preserves their quotes. Guest upgrade and merge preserve the account quote and usage. |
| One pass across web, iOS and Android | Each provider path is tested through checkout, duplicate requests, shared access and the midnight after results day. Invalid native receipts, cross-account or platform replay and production fake purchases are rejected. |
| Server-driven offer and three entry points | React Native tests render alternative prices, dates and limits. Playwright covers placement to signup to offer, a lesson limit and mock-result checkout, followed by a second mock. Screens are exercised at 390 and 1280 px and the paywall heading is compared with the reference. |

## Outcomes

`pnpm setup`, `alembic check`, client generation, `pnpm check` (62 Jest and 81 pytest cases), all 36 Playwright cases and the iOS and Android production exports passed. Run the development servers after setup and use the test checkout on the season-pass screen. Production payment adapters and provider webhooks remain deployment work. No new dependencies or environment variables were added.
