# Harness

Read by every pitaya skill before it plans, builds, verifies or reports. Written by `/setup`; edit it by hand or re-run `/setup`.

This repository develops pitaya with pitaya (decision D31).

## Level

- Level: 1, plus the machine-account commit identity from Level 2. What each level includes: `plugin/docs/levels.md`; what each part achieves: `plugin/docs/suggestion.md`.
- Templates: pitaya 0.1.10. The version `/setup` installed; re-run `/setup` to find stale copies.

## People and accounts

- Owner: the repository owner on GitHub.
- Machine account: the agents' machine account (see the repository's collaborators). Agents push, open PRs and comment as this account, and commit with its GitHub noreply identity (D29).
- Autonomy: Only the Owner merges `main`.

## Work

- Issue tracker: GitHub Issues in this repo.
- Tickets: GitHub Issues labelled `ticket`. Until now, work was planned as the W-steps in `docs/design.md`, section 13.
- Milestones: none yet; the W-steps play that role.
- Test command: `python3 -m pytest tests -q`. Needs pytest; no network access.
- Document language: en. Every file in this repository is English (`tests/test_english.py`).

## Review

- Verification: a fresh subagent, started by `/verify`.
- Fix rounds: 2. Under `/autopilot` every round is a fresh session; otherwise round 1 may stay in the builder's session. One more FAIL after the last round means escalating to the Owner.
- Autopilot: off.
- Learning: off.

## Records

- Decisions: `docs/decisions.md`. Append only. D1 to D32 are in `docs/design.md`, section 11; new decisions go here.
- Glossary: `docs/agents/glossary.md`. The project's words; `/plan` keeps it current.
- Learnings: `docs/agents/learnings.md`. Append only; `/retro` adds what the Owner accepts.
- Architecture: `docs/agents/architecture.md`. The module map; `/plan` keeps it current.

## Sensitive areas

Areas where a change needs a covering test before it starts, otherwise escalate to the Owner.

- Everything under `plugin/`: it ships to users. No personal data (`tests/pii_scan.py`), English only, and each `SKILL.md` at most 80 lines.
- The hooks in `plugin/templates/.claude/hooks/`: a wrong rule blocks users' agents or lets a dangerous command through. Every rule needs tests both ways.

## Guardrails

- Level 1 hooks and permissions: `.claude/settings.json` and `.claude/hooks/`.
- CI: `.github/workflows/ci.yml` (tests on Python 3.11 and 3.13, the skill check, the personal-data scan), with the `ci` check required on `main`. The template's `tests.yml` is left out because `ci.yml` covers it.
- protect-main: ruleset on `main` (PR required, no force push, no deletion, `ci` required). D37 adds one required approval, dismissed on new pushes; the Owner sets it.
- Commit author: the personal-data scan accepts only the machine account's noreply identity and the Claude default (D29).
