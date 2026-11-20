# pitaya

Small, composable skills for developing with coding agents under human review: plan a roadmap of milestones and cut each into tickets, build red-then-green, verify cold in a fresh session, and report. Protection grows by **level** instead of a gate: `/setup` installs a cheap Level 1 default (an AGENTS.md map, permissions, four hooks and a tests workflow), and higher levels come from guardrail recipes when a project needs them. The levels form a spectrum, from close control like Matt Pocock's skills (Level 0) to the most agent authority like pstack (Level 4).

> **Status: 0.1.6.** Fourteen skills and seventeen guardrail recipes ([`plugin/docs/guardrails/`](plugin/docs/guardrails/README.md)). Progress: [design, section 13](docs/design.md#13-implementation-plan). Everything each level includes: [`plugin/docs/levels.md`](plugin/docs/levels.md); what each part achieves: [`plugin/docs/suggestion.md`](plugin/docs/suggestion.md).

## Install

The plugin is named `pitaya`; once installed, skills appear as `/pitaya:setup`, `/pitaya:build` and so on. Pick one route.

**As a plugin (updates automatically).** In Claude Code, add this repository as a marketplace, then install. Replace `<owner>` with this repository's owner on GitHub.

```text
/plugin marketplace add <owner>/pitaya
```

```text
/plugin install pitaya@pitaya
```

**In cloud sessions** (claude.ai/code, or the desktop app's cloud sessions), which have no `/plugin`: add `claude plugin marketplace add <owner>/pitaya` and `claude plugin install pitaya@pitaya` to the environment's setup script, under Settings → Environments. Every new session there has the plugin; check with `/pitaya:help`. Details: [`plugin/README.md`](plugin/README.md#cloud-sessions).

**By copying (yours to edit).** Copy the `plugin/` folder somewhere on your machine and point Claude Code at it, or copy single `plugin/skills/<name>/` directories into your project's `.claude/skills/`. You pick up later changes yourself. `/setup` needs `plugin/templates/` next to its skill.

Then run `/pitaya:setup` in your project.

## Levels

| Level | For | What you get |
| --- | --- | --- |
| 0 | Trying it out | The skills only |
| 1 (default) | One person with one or a few agents | An AGENTS.md map, the harness config, memory files, permissions that deny secrets, hooks that block pushes to `main` and destructive commands and ask before rule edits and merges, a tests workflow, and a ruleset where only the Owner merges |
| 2 | Agents working in parallel | `/design` (scenarios, interfaces, data flow). Recipes: machine account, commit author, scope, read-only paths, no weakened tests, done-when, append-only files, serial resources, evidence, verify the real app, multi-account |
| 3 | Milestone autonomy | `/autopilot`; agents merge into the milestone branch and the Owner signs off each milestone. Recipes: progress file, agent merging |
| 4 | Max | The most agent authority: the Chief also cuts each milestone. Recipes: second-model review (Claude, Cursor CLI, Bugbot or Grok), deep verification, project evals |

## Skills

| Skill | Invoked by | What it does |
| --- | --- | --- |
| `/setup` | you | Ask a few questions, install the level's files without overwriting anything, write the harness config |
| `/plan` | you | `--roadmap` sharpens the brief and cuts the project into milestones; `M<n>` cuts the active milestone into vertical-slice tickets. The Owner approves through a plan PR |
| `/design` | you | Level 2: a milestone's Given/When/Then scenarios, then its interfaces, data flow, notifications and state owners; tickets come from the scenarios |
| `/build` | you | Build one ticket red-then-green and open a PR with evidence |
| `/verify` | you | A fresh subagent re-runs everything cold and judges PASS or FAIL |
| `/report` | you | Summarize merged work for the Owner from sources anyone can open |
| `/handoff` | you | Leave hand-off notes so another session picks up in minutes |
| `/retro` | you | Turn repeated mistakes into rule-and-enforcer proposals; check what can be retired |
| `/autopilot` | you | Level 3: run the active milestone, handing tickets to fresh builders and verifiers, stopping at the Owner's gates |
| `/help` | you | Where the project stands, what waits on whom and the next command; or how to do something. Read only |
| `tdd`, `evidence` | the agent | Red-then-green discipline; what counts as evidence |
| `ask-owner` | the agent | Stop and hand a decision to the Owner with options and a recommendation |
| `learning` | the agent, when turned on | The Owner answers four questions first, then compares with the agent's answers |

The ideas behind them, including who may read and write which files, the state machines and a full project's layout: [`plugin/docs/concepts/`](plugin/docs/concepts/README.md).

## What's in this repository

- `plugin/` is what users install: the skills, the Level 1 templates, the guardrail recipes and the user docs. The marketplace installs this folder alone.
- Everything else is for developing pitaya: `docs/design.md` (the design, decisions and plan), `evals/` (tasks that measure the harness itself), `tests/`, `scripts/`, CI, and this repository's own `AGENTS.md`.

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
