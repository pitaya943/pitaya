# Harness

Read by every pitaya skill before it plans, builds, verifies or reports. Written by `/setup`; edit it by hand or re-run `/setup`.

## Level

- Level: 1. Or a custom selection's label from `select_components.py`, such as "Level 1 + scope, machine-account". What it includes: `docs/levels.md` in the pitaya plugin; what each part achieves: `docs/suggestion.md`. Raise it by adding guardrail recipes; record each under "Guardrails" below.
- Templates: pitaya 0.1.0. The version `/setup` installed; re-run `/setup` to find stale copies.

## People and accounts

- Owner: example-owner.
- Machine account: example-bot. Agents push, open PRs and comment as this account. If it's "none", agents use the current session's account.
- Autonomy: Only the Owner merges `main`.
  The alternative, Level 3 with the agent-merge recipe only, is the value "Agents merge ticket PRs into milestone branches; only the Owner merges main". The `ask_on_merge.py` hook reads only the value after "Autonomy:".

## Work

- Issue tracker: GitHub Issues in this repo.
- Tickets: `docs/tickets/T-<nnn>.md` files, each mirrored by a GitHub issue labelled `ticket` that links to the file. The file is the source of truth; checks read it from the base branch. (Alternatives: "files only", or "GitHub Issues labelled `ticket`" for the lightest setup.)
- Milestones: `docs/milestones/M<n>.md`, written by `/plan --roadmap`; one is active at a time.
- Test command: `pytest -q`. Recorded exactly as it runs here. From Level 2 it must also write JUnit XML.
- Document language: en. Used for PRs, issues, comments and reports. Code, identifiers and commit messages stay in English.

## Review

- Verification: a fresh subagent, started by `/verify`. (Alternative: "a separate session", optionally with a named model.)
- Fix rounds: 2. Round 1 in the builder's session, the rest in fresh sessions; still failing after the last round means escalating to the Owner.
- Autopilot: off. When on (Level 3): budget per run (default 5 merged tickets or 8 hours), parallel builders (default 2), and how it wakes (PR events, `/loop`, a schedule or a GitHub Action).
- Learning: off. When on, `/report` ends by offering the `learning` review.

## Records

- Decisions: `docs/decisions.md`. Append only: add new entries, never rewrite old ones.
- Glossary: `docs/agents/glossary.md`. The project's words; `/plan` keeps it current.
- Learnings: `docs/agents/learnings.md`. Append only; `/retro` adds what the Owner accepts.
- Architecture: `docs/agents/architecture.md`. The module map; `/plan` keeps it current.

## Sensitive areas

Areas where a change needs a covering test before it starts, otherwise escalate to the Owner. Examples: money calculations, permissions, data migrations.

- (none yet)

## Guardrails

Guardrails in place. Skills rely on these being enforced by hooks or CI rather than re-checking them by hand.

- (none yet)
