# pitaya

Small, composable skills for developing with coding agents under human review: plan work into tickets, build red-then-green, verify cold in a fresh session, and report. Protection grows by **level** instead of a gate: `/setup` installs a cheap Level 1 default (an AGENTS.md map, permissions, three hooks and a tests workflow), and higher levels come from guardrail recipes when a project needs them.

> **Status: in development (0.1.0, unreleased).** All eleven skills exist; ten guardrail recipes are in [`plugin/docs/guardrails/`](plugin/docs/guardrails/README.md). Progress: [design, section 13](docs/design.md#13-implementation-plan). Which components each level should have, and what each one achieves: [`plugin/docs/suggestion.md`](plugin/docs/suggestion.md).

## Install

The plugin is named `pitaya`; once installed, skills appear as `/pitaya:setup`, `/pitaya:build` and so on. Pick one route.

**As a plugin (updates automatically).** In Claude Code, add this repository as a marketplace, then install. Replace `<owner>` with this repository's owner on GitHub.

```text
/plugin marketplace add <owner>/pitaya
```

```text
/plugin install pitaya@pitaya
```

**By copying (yours to edit).** Copy the `plugin/` folder somewhere on your machine and point Claude Code at it, or copy single `plugin/skills/<name>/` directories into your project's `.claude/skills/`. You pick up later changes yourself. `/setup` needs `plugin/templates/` next to its skill.

Then run `/pitaya:setup` in your project.

## Levels

| Level | For | What you get |
| --- | --- | --- |
| 0 | Trying it out | The skills only |
| 1 (default) | One person with one or a few agents | An AGENTS.md map, the harness config, permissions that deny secrets, hooks that block pushes to `main`, destructive commands and silent rule edits, and a tests workflow to make a required check |
| 2 | Agents working in parallel | Recipes: scope, read-only paths, no weakened tests, done-when, commit author, append-only files, serial resources, evidence |
| 3 | Long-running autonomy | Recipes: progress file, second-model review, agent merging, project evals |

## Skills

| Skill | Invoked by | What it does |
| --- | --- | --- |
| `/setup` | you | Ask a few questions, install the level's files without overwriting anything, write the harness config |
| `/plan` | you | Turn a request into vertical-slice tickets with done-when conditions; the Owner approves before they're written |
| `/build` | you | Build one ticket red-then-green and open a PR with evidence |
| `/verify` | you | A fresh subagent re-runs everything cold and judges PASS or FAIL |
| `/report` | you | Summarize merged work for the Owner from sources anyone can open |
| `/handoff` | you | Leave hand-off notes so another session picks up in minutes |
| `/retro` | you | Turn repeated mistakes into rule-and-enforcer proposals; check what can be retired |
| `tdd`, `evidence` | the agent | Red-then-green discipline; what counts as evidence |
| `ask-owner` | the agent | Stop and hand a decision to the Owner with options and a recommendation |
| `learning` | the agent, when turned on | The Owner answers four questions first, then compares with the agent's answers |

The ideas behind them: [`plugin/docs/concepts/`](plugin/docs/concepts/README.md).

## What's in this repository

- `plugin/` is what users install: the skills, the Level 1 templates, the guardrail recipes and the user docs. The marketplace installs this folder alone.
- Everything else is for developing pitaya: `docs/design.md` (the design, decisions and plan), `tests/`, `scripts/`, CI, and this repository's own `AGENTS.md`.

## Developing this repository

```bash
python3 scripts/check_skills.py
```

```bash
python3 -m pytest tests -q
```

The first checks the plugin manifests and every `SKILL.md`; the second runs every test, with no network access needed. Every file in this repository is written in English, and none may contain personal data (`tests/pii_scan.py`).

## License

[MIT No Attribution](LICENSE)
