# M1 design system and app shell

## Purpose

Developers can inspect and operate every shared primitive in a Turkish, development-only gallery on web, iOS and Android. The app shell provides the destinations in the route map. The thirteen HTML references determine component geometry, typography, colour and copy. [Milestone](../../docs/MILESTONES.md) · [Design system](../../docs/DESIGN_SYSTEM.md) · [Route map](../../docs/SCREENS.md)

## Implementation sequence and progress

- [x] Inspect the M0 scaffold, specifications, and all reference exports, including the original SVG paths.
- [x] Install the prescribed font and SVG packages. Define theme tokens, type-safe Turkish copy and formatting helpers.
- [x] Build the components and interactive states from the design table, including accessible web controls and tables.
- [x] Integrate the responsive Expo Router shell and development gallery. Keep the live M0 health check working.
- [x] Verify the suffix table, interactions, theme boundaries, route access and responsive layouts. Compare live renders with the references, export native bundles, run the root checks and update the README.

## Decision log

- ASSUMPTION: Until onboarding and the product screens arrive, the start route opens Today with the existing health check. Each other destination shows its specified title. The gallery is available at `/gallery` in development.
- ASSUMPTION: Gallery interactions use temporary local selections and original placeholder labels. They demonstrate controls without creating candidate or study records.
- The reference sidebar includes an exam-date chip. Its value depends on the future config endpoint. M1 implements the navigation items and wordmark using the configured app name.
- The suffix helper formats whole-number counts in the possessive and possessive-plus-accusative forms shown in the design guide. Date and timer helpers format supplied values. The server supplies dates and remaining durations.

## Validation

| Criterion | Result |
| --- | --- |
| Design gallery | At 390 × 844 and 1280 × 800, Playwright operated the gallery's controls and checked semantic buttons, links, headings, select and table elements. It compared the selected and unselected options, close button, field, mock option, flagged map cell, table header and navigation with their actual HTML references. The browser loaded all five local Jakarta weights. Visual inspection also covered the primary card, controls, task and list rows, question map, tables and pinned footer. The enlarged-text check passed at 1.3× at both widths. |
| Responsive shell | Production Chromium tests verified four links at phone width, a centred 560 px bar at 1023 px, a 224 px rail with five destinations at 1024 px, direct entry, reload, browser back and the live M0 health response. A direct visit to the protected release gallery returned to Today. The iOS and Android Hermes exports include all five font files. |
| Formatting | Jest verified every integer listed in the design table for both suffix forms, composite and large counts, safe-integer validation, locale numbers, currency, percentages, ranges and timers. Date cases cross midnight in Istanbul. |
| Theme boundaries and quality | A deliberate in-memory ESLint input containing a hex colour and a literal font size produced both expected errors. `pnpm check` passed, including 43 Jest and two PostgreSQL API cases. `pnpm test:e2e` passed all 14 Chromium cases. |

## Discoveries

- Expo Router's web link composes its child's style object. Flattening the active sidebar item's React Native styles before passing them to the link preserves the selected appearance on wide screens.
- The reference styles are embedded in the HTML files. Browser checks read them directly, with external font-service links removed. The app obtains its font files from the local Expo bundle.
- Another service held port 5432 on the development machine. Local verification used the isolated Compose project `kursu-m1-verify` on loopback port 55432.

## Outcomes

Start the API and Expo app as described in the [README](../../README.md). Select **Bileşen galerisi** on Today or open `/gallery` in development. The design components and responsive navigation are ready for the subsequent product milestones.
