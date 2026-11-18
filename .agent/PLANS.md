# Writing an ExecPlan

Write the plan before implementing a milestone or starting a task expected to take more than about an hour. Save milestone plans at `.agent/plans/M<n>-<slug>.md`. Use the milestone's acceptance criteria to define the scope. [Repository instructions](../AGENTS.md) · [Milestones](../docs/MILESTONES.md)

- In **Purpose**, describe what someone will be able to do when the work is complete. Include the relevant product rule IDs or design references when the milestone names them.
- In **Implementation sequence** and **Progress**, outline the changes in order and keep a checklist current as work proceeds.
- In the **Decision log**, record choices and their reasons. When the spec is silent, mark the simplest choice with `ASSUMPTION:` and include it in the final summary.
- In **Validation**, pair each acceptance criterion with the command, test or observation that verifies it. Record actual results, including `pnpm check` and `pnpm test:e2e` as required by the milestone. If a check is blocked, identify the blocker and the verification still needed.
- In **Outcomes**, summarize what changed, how to run it and any open questions.

The scaffold plan shows this format in use. [M0 ExecPlan](plans/M0-scaffold.md)
