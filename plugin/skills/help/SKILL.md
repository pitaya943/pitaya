---
name: help
description: Say where the project stands and what to do next, or how to do something with pitaya. Reads the harness file, the milestones, tickets, branches and PRs, and answers with the current state, what waits on whom, and the next command to type. Read only; it never changes anything.
disable-model-invocation: true
argument-hint: "[a question, such as \"how do I add the scope check\" or \"what is blocking M2\"]"
---

# Help

You answer two kinds of question: **where are we** (no argument, or "what's next") and **how do I** (anything else). This skill is read only: you read files and GitHub, and you never write a file, push, comment, merge or start another session. If the user wants something done, name the command and let them type it.

## Before you start

1. Read `docs/agents/harness.md`: Level, Owner, Autonomy, Tickets, Milestones. If it's missing, say the project is at Level 0, that the skills work with safe defaults, and that `/setup` writes the harness file; then answer from what the repository shows.
2. Read [states.md](../../docs/concepts/states.md) for the state machines and where each state lives. Rebuild state from those places only, never from memory of earlier sessions.

## Where are we

Gather, with read-only commands (`git fetch`, `git branch -r`, `gh pr list`, `gh issue list`, or the GitHub tool's list and read calls where `gh` isn't available, as in cloud sessions):

1. **Milestone:** the one with `Status: active` under `docs/milestones/`, and whether `milestone/M<n>` and its PR exist.
2. **Tickets:** each ticket of that milestone with its state: open, blocked (a "Depends on" not done), claimed (a `ticket/<id>-*` branch), in review, fixing (FAIL on the head, and how many rounds), escalated (an open `needs-owner` issue), done.
3. **Waiting on the Owner:** plan PRs, the milestone PR, `needs-owner` issues, and below Level 3 every green PR with a PASS.
4. **Autopilot:** at Level 3 and up, the last line on the `Autopilot: M<n>` tracking issue and whether it said it stopped.

Answer in the document language, short:

```text
Level 3 · M2 active (4 of 7 tickets done)
Waiting on you: PR #41 (milestone M1 sign-off), issue #44 (needs-owner: T-012 retention rule)
In progress: T-010 in review (PASS, merging next tick) · T-011 fixing, round 1 of 2
Next: /pitaya:verify 45   (T-013: CI green, no verdict on its head)
```

Pick **one** next step: the one that unblocks the most. Prefer a step the user can take now over one that waits on someone else. When nothing can move, say who it waits on.

## How do I

1. Find the answer in the plugin's docs, in this order: [levels.md](../../docs/levels.md) for what a level includes, the recipes under `docs/guardrails/` for one guardrail, [concepts](../../docs/concepts/README.md) for roles, autonomy, escalation, access, states and layout, then the skill that does the work.
2. Answer in three to six lines: what to do, the command or file, and the page to read for details. Link the page; don't copy it.
3. If the question asks for something a level doesn't allow (an agent merging into `main`, skipping the verifier), say so and name the level or recipe that changes it.

## Never

- Never write, commit, push, comment, label, merge or close anything, and never start a build, verify or plan session yourself.
- Never guess a state you couldn't read: say "unknown" and which command would show it.
- Never print secrets or the contents of `.env` files.
