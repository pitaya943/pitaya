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
5. Commit on a `plan/<slug>` branch and open one PR; if the session has an assigned branch (cloud sessions do), ask the user to allow `plan/<slug>` instead of using the assigned branch. The Owner's merge approves the roadmap. With an issue mirror, also create one GitHub milestone per file (title `M1: <title>`) and assign each mirror issue to its milestone. If your tools can't create GitHub milestones, say so in the plan PR and list them for the Owner to create; the files stay the source of truth.

## `/plan M<n>`

From Level 2, the milestone is designed first: `docs/milestones/M<n>-design.md` holds its scenarios (`S-1`, `S-2`, ...), interfaces, data flow and state owners (the `design` skill). Cut the tickets from the scenarios: every scenario belongs to exactly one ticket, which lists it under "Scenarios" and turns it into a done-when condition with the test the design names; interfaces a ticket introduces come from the design, not from the builder. Then, as described in `SKILL.md` and [tickets.md](tickets.md), every ticket gets `Milestone: M<n>`, and the milestone's "Tickets" section lists them. Tickets stay inside the milestone's goal and outside its "Not in this milestone" list; a needed change outside them is a question for the Owner, not a new ticket. The same plan PR sets this milestone to `Status: active`, and leaves the one before it alone: that one became done when the Owner merged its milestone PR. Cut M<n> only once the milestone before it is done on `main`. One repair is allowed: if that milestone's milestone PR is merged and `main` still says `active` (it was signed off before report PRs existed, or its report PR was skipped), a plan PR into `main` sets its `Status: done`, since the sign-off already happened. Below Level 4 the cut's own plan PR carries that line; at Level 4 the cut goes into a milestone branch, where it may not touch another milestone's file, so the repair is a plan PR of its own for the Owner to merge. At Level 4 under `/autopilot` nobody approves the cut before it merges into the milestone's branch: the Owner reads the design and the tickets at the milestone's sign-off, so record every choice the Owner would have been asked about in the plan PR's description.

## The milestone branch

Every active milestone has this branch, at every level (D44). Once the Owner merges the plan PR that cuts M<n>, create `milestone/M<n>` from `main` and push it. (At Level 4 `/autopilot` creates the branch first and merges the cut into it, so from then on the milestone's `Status:` and tickets are read on its branch; `main` shows it `planned` until the sign-off.) That merge happens outside any session, so whichever comes first creates the branch if it's missing: this skill's next run, `/build` for the milestone's first ticket, or an `/autopilot` tick. Every ticket of the milestone branches from `milestone/M<n>` and its PR targets `milestone/M<n>`; the checks read the tickets from there. Agents merge ticket PRs into it when the harness's Autonomy allows (Level 3, [agent-merge](../../docs/guardrails/agent-merge.md)); otherwise the Owner does. Before each new ticket, bring in what `main` gained (plan PRs land there) through a **sync PR**, never by pushing to the protected milestone branch and never with "Update branch" on a PR from `main` (that merges the milestone into `main`, ahead of the sign-off):

1. Create `sync/M<n>-<short sha of main>` from `milestone/M<n>`, merge `origin/main` into it with a plain `git merge` (no strategy option such as `-s ours` or `-X theirs`, no edits in the merge commit), and push it.
2. Open a PR from it into `milestone/M<n>`. It's up to date by construction.
3. The ticket checks pass it when its tree is exactly the milestone merged with `main` and every commit it adds is a true merge, and `agent-merge` gives it a `verdict` without a verifier for the same reason. Anything else in it fails both. A conflict fails too: the Owner resolves it.
4. Merge it like a ticket PR: the Owner below Level 3, agents from Level 3.

A ticket PR that falls behind its milestone branch uses GitHub's "Update branch" as usual. From Level 3 its PASS carries over that merge, and only that merge, unless the ticket is `Risk: high`, whose PASS never carries (the [agent-merge](../../docs/guardrails/agent-merge.md) recipe).

The milestone branch is the blast radius: whatever goes wrong inside it stays out of `main`, and the Owner can throw the whole branch away.

## Closing a milestone

When every ticket of the active milestone has `Status: done` on `milestone/M<n>`:

1. `/report M<n>` checks the exit criteria one by one, with evidence, and writes the report.
2. It opens the **report PR**, `plan/M<n>-report` into `milestone/M<n>`: `Status: done` in `docs/milestones/M<n>.md`, the report as `docs/reports/M<n>.md`, and nothing else. It merges like a sync PR: the Owner below Level 3, agents from Level 3 (the `verdict` check passes it without a verifier).
3. Once that is merged, the milestone PR is opened, `milestone/M<n>` into `main`, with the report as its description: by the `/autopilot` tick when one runs the milestone, otherwise by `/report M<n>`, in the same session or run again after the merge.
4. The Owner reviews the milestone as a whole and merges it: that merge is the sign-off, and it is what brings `Status: done` to `main`. There is one definition of done, and no later PR completes it. Or the Owner sends it back with what to fix, or throws the branch away. What to fix becomes new tickets: below Level 4 through a plan PR on `main` and a sync PR. At Level 4 the milestone file on `main` is still the roadmap's copy, so that sync would conflict, and the tickets go in a plan PR into `milestone/M<n>`, which adds them like a cut. The milestone is active again while any of them is open, though its branch still says `Status: done`.
5. Run `/retro` (with the Owner; `/autopilot` doesn't run it), then `/plan M<n+1>`: its plan PR cuts the next milestone, and the Owner approves the cut by merging it.

Between steps 2 and 4 the milestone is closing: its branch says `Status: done` and `main` still says `active`. Only `main` decides whether it is done.
