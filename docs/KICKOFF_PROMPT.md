# Kickoff prompts for Codex

## How to use this kit

1. Create an empty Git repository and copy this kit into its root, keeping the folder structure (`AGENTS.md`, `.agent/`, `docs/`). Commit it.
2. Open the repository in Codex and start a new task with the first prompt below.
3. Review the result, merge it, then run one milestone per task with the follow-up prompt.

Codex loads `AGENTS.md` automatically. The prompts stay short because the rules and specs are in the repository.

## First prompt (milestone M0)

```text
Goal
Implement milestone M0 from docs/MILESTONES.md: scaffold the Kürsü monorepo so that the Expo app (web, iOS, Android) and the FastAPI service run locally, talk to each other, and pass all checks.

Context
- AGENTS.md has the stack, layout, commands and rules.
- docs/ARCHITECTURE.md describes the structure you are creating.
- docs/MILESTONES.md, section M0, lists the scope and acceptance criteria.
- The repository contains only docs so far. You create everything else.

Constraints
- Before writing code, write an ExecPlan at .agent/plans/M0-scaffold.md as described in .agent/PLANS.md. Keep it current while you work.
- Use the latest stable Expo SDK and install Expo-aware packages with `npx expo install`.
- Build only what M0 asks for. No product screens, no product tables beyond what M0 lists.
- If the spec is silent, choose the simplest option and record it as ASSUMPTION: in the plan and in your summary.

Done when
- Every M0 acceptance criterion is met and you show how you verified each one.
- `pnpm check` and `pnpm test:e2e` pass from a clean clone after `pnpm setup`.
- Your final message lists what you created, how to run it, every ASSUMPTION, and open questions.
```

## Follow-up prompt (one milestone per task)

Replace `M<n>` and the plan name.

```text
Goal
Implement milestone M<n> from docs/MILESTONES.md.

Context
- AGENTS.md, docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md.
- For UI: docs/DESIGN_SYSTEM.md, docs/SCREENS.md and the reference files the milestone names in docs/design/reference/.
- Earlier plans in .agent/plans/ record decisions and assumptions already made.

Constraints
- Write an ExecPlan at .agent/plans/M<n>-<slug>.md first and keep it current.
- Implement the rules exactly as numbered in docs/PRODUCT_SPEC.md and cover each with a test named after its rule id.
- Leave out P1 and P2 elements unless this milestone lists them.
- Do not start the next milestone.

Done when
- Every acceptance criterion of M<n> is met, with evidence for each.
- `pnpm check` and `pnpm test:e2e` pass.
- Docs you made stale are updated, and your final message lists changes, ASSUMPTIONs and open questions.
```

## Useful one-off prompts

```text
Compare the implemented <screen name> screen with docs/design/reference/<file>.html at 390 px width. List every visual difference (spacing, size, colour, copy), then fix them. Do not change behaviour.
```

```text
Review the last milestone against docs/PRODUCT_SPEC.md. For each rule id it covers, name the test that proves it, or write the missing test.
```
