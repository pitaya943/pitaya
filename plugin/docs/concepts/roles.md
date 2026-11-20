# Roles

pitaya describes the work with four roles. They're concepts, not accounts or processes: one person with one agent plays all of them in turn, and a larger setup can give each its own session.

| Role | Who | Does | Doesn't | Skills |
| --- | --- | --- | --- | --- |
| **Owner** | A person | Approves the roadmap and each milestone's tickets by merging plan PRs, answers escalations, signs off milestones, merges `main` (always, whatever the autonomy setting), sets the level | — | `/setup`, `learning` |
| **Chief** | An agent session | Cuts the roadmap into milestones and milestones into tickets, orders them, reports results, runs retros; from Level 2 designs each milestone; at Level 3 runs a milestone with `/autopilot`, and at Level 4 also cuts the next one | Write product code, merge into `main`, sign off a milestone | `/plan`, `/design`, `/report`, `/retro`, `/autopilot` |
| **Builder** | A fresh session per ticket | Builds one ticket red-then-green and opens a PR with evidence | Change the spec, change files outside the ticket's scope, merge | `/build`, `tdd`, `evidence` |
| **Verifier** | A fresh subagent or session per PR and round | Re-runs everything from a clean checkout and judges PASS or FAIL | Fix the code, see the Builder's conversation, merge | `/verify`, `evidence` |

Any role can use `ask-owner` and `/handoff`, and anyone can ask `/help` where things stand. Which files each role reads and writes is in [Access](access.md).

## Why separate Builder and Verifier

An agent that grades its own work overrates it; every source this project draws on agrees. The Verifier therefore starts with a fresh context and sees only the ticket, the spec, the diff and what it runs itself. Claims in the PR description aren't evidence to it.

## Solo and parallel

- **Solo (Level 1):** one session plans, then builds a ticket; `/verify` dispatches a fresh subagent; the Owner merges.
- **Parallel (Level 2):** one Chief session plans and tracks; each ticket gets a fresh Builder session, ideally acting as a machine account so its work is traceable; each PR gets a fresh Verifier. Tickets run in parallel only when they don't depend on each other and their scopes don't overlap. The Owner still merges.
- **Autopilot (Level 3):** the Chief runs `/autopilot` on the active milestone. Each time it wakes it starts fresh Builder and Verifier sessions, merges when the autonomy setting allows, and stops at the Owner's gates: plan PRs, sensitive areas, fix rounds, the milestone's sign-off and its budget.
