# Recipe: deep verification

Level: 4. No files to copy: settings in the harness file, and steps the `verify`, `report` and `design` skills already carry.

Adapted from pstack's `/interrogate`, `/swarm`, `/show-me-your-work` and `/arena`.

## What it guards against

At Level 4 agents merge tickets and cut the next milestone with no person reading each step. A single verifier on the builder's model misses what the builder missed, a milestone can pass ticket by ticket and still fail its scenarios as a whole, and the Owner's sign-off has too much to read.

## When it's worth adding

When the project runs at Level 4. The extra agents are what Level 4's authority costs; below it, a person reads enough that this isn't worth the spend.

## How to add it

1. Add [second-model-review](second-model-review.md) and set "Second model" in the harness file.
2. Tag every ticket `Risk: low` or `Risk: high` (the `plan` skill's `tickets.md` has the rules); the Owner may override in the plan PR. The tag already matters at Level 3, where a high-risk ticket's PASS doesn't carry over a merge of its base; this level adds the interrogation.
3. `/verify` then interrogates each high-risk PR (`verify/interrogate.md`): adversaries in worktrees, and only findings a run reproduces survive.
4. `/report M<n>` runs a swarm over the design's scenarios and a decision-log audit that adds its findings to the report's Attention table for the Owner (`report/milestone-level4.md`).
5. `/design` runs an arena when two shapes come out close (`design/arena.md`).
6. Set Autonomy to "Agents merge ticket and plan PRs into milestone branches; only the Owner merges main", so `/autopilot` cuts the next milestone inside its branch.

## How to prove it works

Plant a bug in a high-risk ticket that the unit tests miss but a reordered call or an empty input exposes. The interrogation reproduces it and the verdict is FAIL. At a milestone, break one scenario after its ticket merged: the swarm's table shows it failing.

## Cost and false positives

- Roughly two to four times the verification cost of a high-risk ticket, and one swarm plus one audit per milestone. Low-risk tickets cost what they did at Level 3.
- Outside models raise guesses and style points; reproduce-or-drop keeps them out of the verdict.
- An arena costs about four design sessions; it runs only for contested designs.

## Error message

The verdict's "Interrogate" section lists each surviving finding with its reproduction and output. The milestone report's swarm table marks each failing scenario with its evidence.

## Afterwards

Record `deep-verification` under "Guardrails" in the harness file. Measure it with [project-evals](project-evals.md): compare the problems found and the cost per milestone with Level 3.

## When to remove it

When evals show the interrogation and the swarm find nothing the single verifier misses, or the project moves back to Level 3.
