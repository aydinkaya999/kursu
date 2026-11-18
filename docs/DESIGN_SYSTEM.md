# Design system — Kürsü

The visual source of truth is `docs/design/reference/*.html`: static HTML exports of the 13 designed screens, with every style inline. Open them in a browser at 390 px width (`web-today.html` at 1280 px). Screenshots of the same screens at 2× scale are in `docs/design/reference/png/`. This document names the tokens and components those files use, so the app is built from a theme and not from copied values.

## Principles

- Lively and encouraging, never childish. One bright blue, white cards on a cool pale ground, pastel tiles that mark task types.
- Rounded: pill buttons, large radii, soft shadows. No gradients, no decorative borders, no emoji, no mascots.
- Each screen has one big number or one clear next action.
- The mock exam is calm: fewer colours, nothing celebratory.

## Colour tokens

Create these in `apps/app/src/theme/colors.ts`. Use only the listed text/background pairs; they meet 4.5:1 contrast.

| Token | Hex | Use |
|---|---|---|
| `ground` | `#F2F5FC` | screen background |
| `surface` | `#FFFFFF` | cards, rows, tab bar |
| `ink` | `#151B2E` | primary text; timer pill background |
| `inkMuted` | `#55607A` | secondary text (on `surface`, `ground`, tints) |
| `line` | `#E1E7F3` | hairlines, quiet borders, segmented-control container |
| `borderControl` | `#C9D2E6` | border of unselected options and outline buttons |
| `borderField` | `#8A94AD` | form fields, dashed placeholders |
| `neutralTint` | `#EDF1FA` | neutral chips, unselected pill buttons, letter badges |
| `track` | `#DCE3F5` | progress track on `ground`, unfilled segments, "not started" |
| `primary` | `#2957E8` | primary buttons, progress fill, selected state, links |
| `primaryStrong` | `#1E3FA8` | text on `primaryTint`, link hover, "solid" segment |
| `primaryMid` | `#7C9BF2` | "in progress" segment |
| `primaryTint` | `#E7EDFF` | selected backgrounds, lesson tiles, count pills, tracks on white |
| `primaryTrack` | `#1E44C2` | progress track on a `primary` card |
| `onPrimary` | `#FFFFFF` | text on `primary` |
| `onPrimaryMuted` | `#E3EAFF` | secondary text on `primary` or `ink` |
| `butter` / `butterInk` | `#FFF1CC` / `#7A5200` | time and duration, streak, tips, "look later", season-pass chip |
| `peach` / `peachInk` | `#FFE9DF` / `#A23A12` | needs attention: priority, misconception count, notebook counts |
| `rose` / `roseInk` | `#FFE4EC` / `#A3234F` | photo solve, badges |
| `aqua` / `aquaInk` | `#DDF3F5` / `#0C5F6B` | sources and law references, league, nationwide mock |
| `mint` / `mintInk` | `#DDF5E8` / `#0B6B45` | done, correct, success |
| `success` | `#0E7A50` | border of the correct answer row |
| `dangerTint` / `dangerInk` / `danger` | `#FDE7E4` / `#B3261E` / `#C2331F` | the candidate's wrong answer: background / text / border |

Shadows (colour, y-offset, blur): card `rgba(21,27,46,0.06)` 8/24; primary button and primary card `rgba(41,87,232,0.25)` 10/24; small control `rgba(21,27,46,0.08)` 4/12; tab bar `rgba(21,27,46,0.06)` −6/20; selected segment `rgba(21,27,46,0.08)` 2/6.

## Typography

Family: **Plus Jakarta Sans**, weights 400, 500, 600, 700, 800. Load it with `expo-font` and the Expo Google Fonts package. Fallback: system UI font. Minimum size 12. Use tabular figures for timers, scores and table numbers.

| Role | Size / line height | Weight |
|---|---|---|
| `display` (net, price) | 40–44 / 44–50, letter-spacing −0.02em | 800 |
| `h1` | 26 / 32 (28 / 34 on onboarding), letter-spacing −0.01em | 800 |
| `lessonTitle` | 21 / 27 | 800 |
| `screenTitle` | 22 / 28, or 19 / 26 next to a back button | 800 |
| `navTitle` (centred header) | 15 | 800 |
| `h2` (card title) | 15 / 20; 14 / 20 inside tiles | 800 |
| `question` | 17 / 26 (placement), 15.5 / 23 (practice, mock) | 600 |
| `body` | 14 / 21; 15 / 22 for intro paragraphs | 400 |
| `rowTitle` | 15 / 20 | 700 |
| `meta` | 13 / 18 | 400–700, `inkMuted` |
| `caption` | 12 / 16, 12.5 / 18 | 600–800 |
| `button` | 16 primary, 15 secondary, 14 text link | 800 / 800 / 700 |

## Shape and spacing

- Radius: pill 999; primary cards 22–24; cards 20; list rows 16–18; icon tiles 14 (44 px), 12 (36 px), 10 (32 px); info boxes 14–16; options 16; compact rows 14; map cells 12; fields 14.
- Screen padding: 20 horizontal; 14–24 top. Gaps between blocks: 10, 12 or 14. Card padding: 14–18.
- Use a 2-pt spacing scale: 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24.

## Components

Build these in `apps/app/src/components` during M1 and show each in a gallery route. Names are suggestions.

| Component | Spec |
|---|---|
| `Screen` | `ground` background, safe-area aware, vertical scroll, optional pinned bottom action area |
| `Card` | `surface`, radius 20, card shadow, padding 14–18 |
| `PrimaryCard` | `primary` background, `onPrimary` text, radius 22, primary shadow. Used for the day's progress and for net estimates |
| `Button` primary | min height 52–56, pill, `primary`, label 16/800 `onPrimary`, primary shadow |
| `Button` secondary | min height 52–54, pill, `primaryTint`, label 15/800 `primaryStrong` |
| `Button` text | min height 44, label 14/700 `primary`; quiet variant 13/600 `inkMuted`, underlined |
| `IconButton` | 44×44 circle, `surface`, small-control shadow, 20 px icon. Always has an accessibility label |
| `Pill` | padding 8×12 or 8×14, label 13/800. Count: `primaryStrong` on `primaryTint`. Tinted: ink colour on its tint |
| `Chip` | padding 4×10 or 6×12, label 12/800. Neutral: `primaryStrong` on `surface` with small shadow. Tinted variants as `Pill` |
| `IconTile` | square with tint background and matching ink icon. 44/36/32 px |
| `ProgressBar` | height 8 (10 on `PrimaryCard`, 6 in the mock exam), pill; track `primaryTint` on white, `track` on ground, `primaryTrack` on primary; fill `primary` or `onPrimary` |
| `SegmentedProgress` | equal segments, height 6, gap 6; done `primary`, rest `track` |
| `TaskRow` | `Card` radius 18, padding 12×14: `IconTile` 44, title `rowTitle`, meta, duration 13/700 `inkMuted`. Next task: 2 px `primary` border and a full-width primary `Button` "Başla" (min height 46) under the row |
| `OptionButton` | min height 54, radius 16, `surface`, border 1.5 `borderControl`; letter badge 32 circle `neutralTint` 14/800; label 15/600. Selected: border 2 `primary`, background `primaryTint`, badge `primary`/`onPrimary`, label 800 |
| `OptionCell` | compact option for the mock exam when every option is 4 characters or fewer: five equal columns, min height 60, radius 16. Selected: `primary` background, `onPrimary` text |
| `AnswerRow` | after answering. Candidate's wrong choice: border 2 `danger`, `dangerTint`, `dangerInk`, cross icon, label "Senin yanıtın". Correct: border 2 `success`, `mint`, `mintInk`, check icon, label "Doğru yanıt". Others: border 1.5 `line`, `surface`, `inkMuted`, min height 36 |
| `SegmentedControl` | container `line`, pill, padding 4; segment min height 44; selected `surface` + shadow, 14/800; unselected 14/700 `inkMuted` |
| `ChoicePills` | equal-width pill buttons, min height 48; selected `primary`/`onPrimary` 800; unselected `neutralTint`/`ink` 700 |
| `SelectField` | min height 52, radius 14, border 1.5 `borderField`, 15/600 |
| `InfoBox` | tint background, radius 14–16, padding 10–14, optional leading icon |
| `ListRow` | `Card` radius 16, min height 60: title, meta, optional count badge (36 px circle, `peach`/`peachInk`, 15/800), chevron |
| `DataTable` | header 12/700 `inkMuted`; body 13.5; row separators 1 px `line`; highlighted column `primaryTint` with `primaryStrong` text |
| `QuestionMap` | grid of 5 columns, cells min height 44, radius 12. Answered: `primary`/`onPrimary`. Flagged: `butter`, 2 px `butterInk` border, flag icon. Current: `primaryTint`, 2 px `primary` border. Unanswered: `surface`, border `borderControl`, `inkMuted` |
| `TabBar` | `surface`, top radius 24, tab-bar shadow; four items, min height 52; 22 px icon in a 56×30 pill (`primaryTint` when active); label 12, active 800 `primaryStrong`, inactive 600 `inkMuted` |
| `SideNav` (web ≥ 1024 px) | `surface` column about 224 px; items min height 48, pill; active `primaryTint`/`primaryStrong` 800 |

## Icons

Stroke icons on a 24×24 view box, stroke 2 (2.5 for check and cross), round caps and joins, colour from the parent. Draw them with `react-native-svg`; copy the path data from the reference HTML. Set: check, cross, back arrow, chevron, calendar, book, stopwatch, chart, notebook, pencil, camera, flame, flag, bookmark, info, lightbulb, medal, trophy.

Task type → tile: review `mint` + check when done; lesson `primaryTint` + book; topic test `butter` + pencil; photo solve `rose` + camera; streak `butter` + flame.

## Voice and copy

- Turkish, informal singular ("sen"). Short, warm, concrete.
- Encourage effort and state facts: "Güzel başladın.", "Adayların %71'ini geride bıraktın", "Yarın 6 soru seni bekliyor".
- Never blame, never hype, never promise a result.
- Inside the mock exam the copy is neutral.
- Do not write new copy when a string exists in `docs/SCREENS.md`. Strings marked NEW there are drafts waiting for product review; keep them together in `tr.ts` under a `draft` comment.

## Formatting (locale `tr-TR`)

- Decimal comma and thousands dot: `38,25`, `1.420`. Percent sign before the number: `%71`. Currency before the number: `₺990`.
- Ranges use an en dash without spaces: `28–34`. Durations: `10 dk`. Timer: `81:36` (minutes:seconds, minutes may exceed 59).
- Dates: `1 Şubat Pazartesi`, `7 Şubat 2027`.
- Turkish suffixes after numbers follow vowel harmony and must be computed, not hard-coded. Write one helper, with tests, for the possessive/accusative pair used in the copy ("4 görevden 1'i", "5 günün 0'ı", "%71'ini", "110 dakikanın 104'ünü"). The suffix follows the last spoken word of the number: 1 bir → `'i`, 2 iki → `'si`, 3 üç → `'ü`, 4 dört → `'ü`, 5 beş → `'i`, 6 altı → `'sı`, 7 yedi → `'si`, 8 sekiz → `'i`, 9 dokuz → `'u`, 0 sıfır → `'ı`, 10 on → `'u`, 20 yirmi → `'si`, 30 otuz → `'u`, 40 kırk → `'ı`, 50 elli → `'si`, 60 altmış → `'ı`, 70 yetmiş → `'i`, 80 seksen → `'i`, 90 doksan → `'ı`, 100 yüz → `'ü`.

## Accessibility

- Text contrast at least 4.5:1 (3:1 from 24 px). The token pairs above pass; do not invent new pairs.
- Touch targets at least 44×44.
- Never rely on colour alone: correct and wrong have icons and labels; flagged has a flag icon; selected has a filled badge and heavier weight.
- Every control has a role and a Turkish accessibility label. Labels for icon-only controls are in `docs/SCREENS.md`.
- Layouts must survive 1.3× text scaling: allow wrapping and scrolling, never clip.
- On web use real buttons, links, headings and tables, and keep keyboard focus visible.

## Layout and responsiveness

- The reference frames are 390×844. In the app every screen scrolls; where the reference anchors actions to the bottom, pin them in a bottom action area above the safe-area inset.
- No fake status bar. Respect safe areas on all edges.
- Web under 1024 px: phone layout, centred, max width 560 px, bottom tab bar.
- Web from 1024 px: `SideNav` replaces the tab bar. The Today screen uses the two-column layout of `web-today.html` (tasks, then a side panel that wraps under them when space runs out). Other screens keep the phone layout in a centred 560 px column until wide designs exist.
