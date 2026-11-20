# Milestones and the roadmap

Planning has two levels. A **milestone** is a large outcome the Owner can see working; a **ticket** is one slice an agent builds in one session. Cut the roadmap into milestones once, then cut each milestone into tickets only when it starts: what the team learns in one milestone changes how the next should be cut.

## `/plan --roadmap`

1. Read the request or spec in full and ask until the overall goal is clear, as for tickets.
2. Draft 3 to 7 milestones, in order. Each one:
   - delivers something demoable on its own, end to end, not a layer ("the database", "the UI");
   - has exit criteria the Owner can check by hand or with a command;
   - says what it deliberately leaves out.
3. Show the Owner the list and change it until they approve.
4. Write `docs/milestones/M1.md`, `M2.md`, ... from [milestone-template.md](milestone-template.md). The first is `Status: active`, the rest `planned`. Leave "Tickets" empty except in M1, if you go straight on to cut it.
5. Commit on a `plan/<slug>` branch and open one PR. The Owner's merge approves the roadmap. With an issue mirror, also create one GitHub milestone per file (title `M1: <title>`) and assign each mirror issue to its milestone.

## `/plan M<n>`

Cut the active milestone into tickets as described in `SKILL.md` and [tickets.md](tickets.md). Every ticket gets `Milestone: M<n>`, and the milestone's "Tickets" section lists them. Tickets stay inside the milestone's goal and outside its "Not in this milestone" list; a needed change outside them is a question for the Owner, not a new ticket. The same plan PR sets the previous milestone to `Status: done` (once it's merged) and this one to `Status: active`.

## The milestone branch

Once the Owner merges the plan PR that cuts M<n>, create `milestone/M<n>` from `main` and push it. Every ticket of the milestone branches from `milestone/M<n>` and its PR targets `milestone/M<n>`; the checks read the tickets from there. Agents merge ticket PRs into it when the harness's Autonomy allows (Level 3, [agent-merge](../../docs/guardrails/agent-merge.md)); otherwise the Owner does. Before each new ticket, merge `main` into the milestone branch so it doesn't drift.

The milestone branch is the blast radius: whatever goes wrong inside it stays out of `main`, and the Owner can throw the whole branch away.

## Closing a milestone

When every ticket of the active milestone has `Status: done` on `milestone/M<n>`:

1. `/report M<n>` checks the exit criteria one by one, with evidence, and writes the report.
2. Open the milestone PR, `milestone/M<n>` into `main`, with the report as its description.
3. The Owner reviews the milestone as a whole and merges it: that merge is the sign-off. Or the Owner sends it back with what to fix, or throws the branch away.
4. Run `/retro`, then `/plan M<n+1>`: its plan PR sets M<n> to `Status: done` and cuts the next milestone, and the Owner approves the cut by merging it.
