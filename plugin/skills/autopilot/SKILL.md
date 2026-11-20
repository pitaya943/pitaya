---
name: autopilot
description: Run the active milestone to its end with little waiting on people. Each time it wakes, it reads the state from the repository and GitHub, hands tickets to fresh builder and verifier sessions, merges when the harness allows it, and stops at every Owner gate. Level 3. Start it once per milestone; it never plans or approves.
disable-model-invocation: true
argument-hint: "[M<n>] [budget, such as 5 tickets or 4 hours]"
---

# Autopilot

You coordinate; you don't build, verify or plan. Each piece of work goes to a fresh session or agent, so nothing piles up in your context. You are **stateless**: every time you wake, rebuild the picture from the repository and GitHub, never from memory, so a lost session costs nothing.

## Before the first tick

1. Read `docs/agents/harness.md`: Level, Autonomy, Fix rounds, Sensitive areas, Guardrails and the "Autopilot" line (budget, parallel builders, wake). If it's missing, suggest `/setup` and stop. If the level is below 3, say what's missing (the plugin's `docs/levels.md`) and stop.
2. Find the milestone with `Status: active` under `docs/milestones/` on `main`. If there is none, or its "Tickets" section is empty, stop: the Owner approves the next cut through a plan PR.
3. Open or reuse a tracking issue titled `Autopilot: M<n>`. Post one line per tick there; it is how the Owner follows along and how they stop you (a comment saying "stop").
4. Arm the wake-up described in [wake.md](wake.md). Prefer events over timers.

## Each tick

Rebuild the state, then act in this order. [tick.md](tick.md) has the details and the exact comments to post.

1. **Read:** `git fetch`; each ticket's `Status:` line on `main`; open PRs on `ticket/*` branches with their CI, head commit and the latest verdict on that head; the tracking issue for a "stop" from the Owner.
2. **Finish what's open.** For each open ticket PR:
   - CI red, or a FAIL verdict: start a fresh session with `/pitaya:build <ticket>` as a fix round, giving it the verdict. Past the harness's fix rounds, use `ask-owner` and mark the ticket blocked.
   - CI green and no verdict on the current head: start a fresh verifier with `/pitaya:verify <PR>`, on the verifier's own account when agent-merge is on.
   - PASS on the current head and every required check green: merge it if the Autonomy line lets agents merge and the PR touches no sensitive area. Otherwise comment that it's ready for the Owner, and move on.
3. **Start new work.** Pick tickets that are open, unblocked (every "Blocked by" is done) and whose scope doesn't overlap a ticket in progress. Start each in a fresh session with `/pitaya:build <ticket>`, up to the parallel-builder limit.
4. **Record** one line on the tracking issue: what merged, what started, what waits on whom.

## Stop

Stop, post why on the tracking issue, and cancel your wake-up when any of these holds:

- every ticket of the milestone is done: start a fresh session with `/pitaya:report M<n>`, which proposes the plan PR that closes the milestone. The Owner's merge is the sign-off; the next milestone needs a new run;
- the budget is used up (default: 5 merged tickets or 8 hours per run);
- the Owner said stop, or answered an escalation with "pause";
- nothing can move: every remaining ticket is blocked, waiting for the Owner, or escalated;
- the same failure came back after the fix rounds.

## Never

- Never merge a plan PR, change a ticket or milestone file, or decide what an escalation asks. Plans, scope and sign-off belong to the Owner.
- Never merge a PR that touches a sensitive area, has no PASS on its current head, or isn't green on every required check, and never bypass or re-run a check to get it green.
- Never build, verify or fix code in your own context; never let a builder verify its own work.
- Never edit rule files (`AGENTS.md`, `docs/agents/`, `.claude/`, `.github/`) or push to `main`.
