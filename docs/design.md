# pitaya design

- Status: draft 0.2, under Owner review. Steps W0–W2 are done; W3 is next (section 13).
- What users read instead: [`suggestion.md`](suggestion.md) explains which components each level should have and what each one achieves.

## Contents

1. [Why](#1-why)
2. [Principles](#2-principles)
3. [Levels](#3-levels)
4. [Repo layout](#4-repo-layout)
5. [Skills](#5-skills)
6. [Per-project config](#6-per-project-config)
7. [Ticket format](#7-ticket-format)
8. [Level 1 defaults](#8-level-1-defaults)
9. [Guardrail recipes](#9-guardrail-recipes)
10. [Distribution and updates](#10-distribution-and-updates)
11. [Decisions](#11-decisions)
12. [Failure modes](#12-failure-modes)
13. [Implementation plan](#13-implementation-plan)
14. [Open questions](#14-open-questions)

## 1. Why

pitaya is a harness for developing software with coding agents under human review: the skills, defaults and optional guardrails a repository needs so agents work reliably and people can trust the result.

It replaces an earlier, heavyweight template. That version asked 16 configuration questions with no defaults, verified seven repository settings and enforced eleven CI checks before the first line of product code. Its weight came from enforcement: under 400 lines of skills against more than 5,000 lines of gate, check and sync code with tests. The process felt cumbersome and limited development.

A first lightweight draft overcorrected in the other direction: it made every guarantee an optional document. Research into the frontier labs' published harness guidance and three public harnesses (mattpocock/skills, Cursor's pstack, gstack) showed three things:

- Every source agrees that rules with no exceptions belong in mechanisms, not prose.
- Both earlier designs missed session-level mechanisms: hooks and permission settings, which act the moment an agent acts and cost far less than CI.
- Neither tested the harness itself, handled hand-offs across sessions, or said when a component could be retired.

pitaya therefore uses **levels**: a cheap, universally endorsed Level 1 installed by default, and higher levels added from recipes when a project needs them.

## 2. Principles

| # | Principle | Meaning |
| --- | --- | --- |
| R1 | Process in skills, guarantees in mechanisms | Skills teach agents how to work; rules with no exceptions are enforced by hooks, permissions or CI |
| R2 | Every skill stands alone | Using only `/verify` or only `tdd` works |
| R3 | Two kinds of skill | User-invoked skills orchestrate (`disable-model-invocation: true`); model-invoked skills hold reusable discipline. Orchestrators may call disciplines, never each other |
| R4 | No gate, but defaults | Nothing blocks the repo; `/setup` installs Level 1 by default and higher levels come from recipes |
| R5 | Cheapest enforcement that suffices | Prose (agent discipline) → session mechanisms (hooks, permissions) → merge mechanisms (CI, branch protection) |
| R6 | Every component says how to retire it | Each one assumes the model can't do something; when models improve, there must be evidence to remove it |
| R7 | Short | Each `SKILL.md` is at most 80 lines; details go in sibling reference files |
| R8 | No personal data | Shipped files carry no names, accounts or emails. The one deliberate exception is the plugin's name, `pitaya` (D25) |
| R9 | English | Every file in the repository is written in English (D27) |

## 3. Levels

One harness, four levels (D1). Each level includes the one before. [`suggestion.md`](suggestion.md) explains each component and what it achieves.

| Level | For | Components | How to get it |
| --- | --- | --- | --- |
| 0 | Trying it out | Skills only | Install the plugin |
| 1 (default) | One person with one or a few agents | AGENTS.md map, harness config, one test command, CI as a required check, `main` protection, permissions, three hooks, a fresh verifier, a decision log | `/setup` copies `templates/` |
| 2 | Agents working in parallel | Machine accounts and author checks, scope, read-only paths, no weakened tests (JUnit comparison), done-when, append-only files, serial resources, evidence checks | Recipes |
| 3 | Long-running autonomy | Progress file and start-up routine, second-model review, an agent-merge policy, project evals | Recipes |

## 4. Repo layout

```text
.claude-plugin/          plugin.json (plugin "pitaya") and marketplace.json
skills/<name>/           SKILL.md plus sibling reference files and scripts
templates/               Level 1 files that /setup copies into a project
docs/
  suggestion.md          what each level should have, and what each part achieves
  design.md              this document
  guardrails/            Level 2-3 recipes, with copyable files under files/<id>/
  concepts/              roles, autonomy, evidence, escalation
evals/                   tasks for testing the harness itself (run by hand)
scripts/check_skills.py  manifest and SKILL.md checker
tests/                   checker, hooks, install script, docs, English, personal-data scan
```

Users install the plugin and run `/setup`; the copied files then belong to their project (D4).

## 5. Skills

**User-invoked (orchestrators)**

| Skill | What it does | Role (D21) | Status |
| --- | --- | --- | --- |
| `/setup` | Explore the repo, ask a few questions, choose a level, install the Level 1 files without overwriting anything, write the harness config; re-runs report stale copies | Owner | Done |
| `/plan` | Split work into verifiable vertical-slice tickets with dependencies; write them where the config says once the Owner agrees | Chief | W3 |
| `/build <ticket>` | Build one ticket red-then-green and open a PR with evidence | Builder | Done |
| `/verify <PR>` | Dispatch a fresh subagent that re-runs everything cold and judges PASS or FAIL against a checklist | Verifier | Done |
| `/report` | Summarize merged work for the Owner | Chief | W3 |
| `/handoff` | Write hand-off notes when work stops: goal, done, in progress, next step, where the evidence is (D11) | Any | W3 |
| `/retro` | Turn repeated mistakes into rule-to-enforcer proposals and review what can be retired; the Owner approves (D18, D19) | Chief | W3 |

**Model-invoked (disciplines)**

| Skill | What it does | Status |
| --- | --- | --- |
| `tdd` | Red for the right reason, then green, then refactor; stub new modules first; never weaken a test | Done |
| `evidence` | What counts as proof; the model name comes from the session's configuration | Done |
| `ask-owner` | Escalate with two or three options, their consequences and a recommendation | W3 |
| `learning` | Optional: the Owner answers four questions first, then compares and records (D22) | W3 |

Every skill reads `docs/agents/harness.md` first; if it's missing, it suggests `/setup` once and continues with safe defaults.

## 6. Per-project config

`docs/agents/harness.md` is Markdown for agents, with no schema.

| Field | Default | Decision |
| --- | --- | --- |
| Level | 1 | D1 |
| Templates | the version `/setup` installed | D20 |
| Owner, machine account | asked by `/setup`; the machine account may be "none" | — |
| Autonomy | only the Owner merges `main`; may become "agents merge after CI is green and the verdict is PASS" at Level 3 | D3 |
| Tickets | GitHub Issues labelled `ticket` with a GitHub remote, else `docs/tickets/<id>.md` | D9 |
| Test command | one command that really runs, recorded as typed; JUnit XML from Level 2 | D5 |
| Document language | asked by `/setup` | — |
| Verification | a fresh subagent; may become a separate session with a named model | D13 |
| Fix rounds | 2 | D16 |
| Decisions | `docs/decisions.md` on; pitfalls off unless asked for | D12 |
| Sensitive areas | asked by `/setup` | — |
| Guardrails | the Level 1 parts, plus any recipe added later | — |
| Learning | off | D22 |

## 7. Ticket format

Fields grow with the level (D10); a field is needed only once its guardrail is adopted.

| Field | Level | Used by |
| --- | --- | --- |
| Goal, done-when conditions, dependencies, scope | 1 | every skill; each condition maps to a test or a re-runnable command |
| Test IDs for done-when | 2 | the done-when recipe (JUnit comparison) |
| Serial resources | 2 | the serial-resource recipe |
| Append-only files | 2 | the append-only recipe |
| Screenshots required | 2 | the evidence recipe |

## 8. Level 1 defaults

`/setup` copies these from `templates/`. Each file that allows comments starts with a `pitaya template <version>` header (D20); `settings.json` can't, so its version is the "Templates" field in the harness config.

| File | Content | Decision |
| --- | --- | --- |
| `AGENTS.md` | A map of at most 100 lines: where to start, the test command, what done means, what never to do, where things are | D2 |
| `CLAUDE.md` | One line importing `AGENTS.md` | D2 |
| `.claude/settings.json` | Deny reading `.env*`, key files and cloud credentials; allow the test command and read-only git; ask for everything else; no sandbox. Merged additively when the project already has one | D8 |
| `.claude/hooks/no_push_main.py` | Deny pushes to the default branch (read from `origin/HEAD` too), force pushes, remote deletes, `--all` and `--mirror` | D6 |
| `.claude/hooks/no_destructive.py` | Deny recursive `rm` of `/`, `~`, `$HOME`, `.` or `..`; `git reset --hard`; forced `git clean` with `-d` or `-x` | D6 |
| `.claude/hooks/ask_on_rule_files.py` | Ask before a file tool or a shell write touches AGENTS.md, CLAUDE.md, the harness config, `.claude/` or `.github/workflows/` | D6 |
| `.github/workflows/tests.yml` | One job running the test command; `/setup` adds the runtime setup steps and hands the Owner the ruleset steps | D7 |
| `docs/decisions.md` | Append-only decision log | D12 |

Rules shared by the hooks:

- Standard library only. Read the PreToolUse JSON on stdin; to block or ask, print the documented `hookSpecificOutput` with `permissionDecision` `deny` or `ask`; print nothing to let the call through.
- On unreadable input, exit 1 with a message: fail open, loudly, so a broken hook can't wedge a session.
- Every block says why and what to do instead.
- Every rule is tested both ways, and each header says when the hook can be removed (R6).
- Hooks run only in Claude Code. Other tools read the same rules as prose in AGENTS.md, and the ruleset still guards `main` at merge time (D2).

The install script never overwrites: an existing file is reported as `unchanged`, `stale` (an older template version) or `differs` (the project's own), and the user decides.

## 9. Guardrail recipes

### 9.1 Format

Each recipe in `docs/guardrails/<id>-<name>.md` has eight sections:

1. What it guards against: the concrete incident without it.
2. When it's worth adding: the signal, such as a second agent working in the repo.
3. How to add it: steps, plus copyable files under `docs/guardrails/files/<id>/`.
4. How to prove it works: an action that makes it fail, and the expected output.
5. Cost and false positives: time added, normal work it blocks, how to handle that.
6. Error message: what it prints on failure, which must tell the agent how to fix it.
7. Afterwards: record it under "Guardrails" in the harness config; extend the ticket format if needed.
8. When to remove it: the evidence that it's no longer needed (D18).

### 9.2 Catalogue

| Level | Recipe | Origin |
| --- | --- | --- |
| 1 | Protect `main`: ruleset, Owner-only merges, required checks (the steps `/setup` hands over) | earlier template's setup guide |
| 2 | Machine account: creation, Write access, token, commit author | earlier identity checks |
| 2 | Commit-author check | earlier `commit-author` check |
| 2 | Scope: a PR changes only the ticket's paths | earlier `path-scope` check |
| 2 | Read-only paths: rules, specs and CI can't change in a ticket PR | earlier `readonly-paths` check |
| 2 | No weakened tests: every test passing on the base exists and passes on the PR | earlier `no-weakened-tests` check |
| 2 | Done-when: every completion condition's test exists and passes | earlier `done-when` check |
| 2 | Append-only files | earlier `append-only` check |
| 2 | Serial resources: one ticket at a time per migration or lockfile | earlier `serial-resource` check |
| 2 | Evidence: the PR has an evidence section; screenshots when there's a UI | earlier `evidence` check |
| 3 | Second-model review (D14) | earlier optional review module |
| 3 | Progress file and start-up routine (D11) | new |
| 3 | Agent merging and its prerequisites (D3) | new |
| 3 | Project evals | new |
| — | Docs lint (links, structure) | earlier docs-lint module |

The earlier bootstrap gate and branch-to-ticket gate are not carried over (D26).

### 9.3 Copyable files

Standard library and git only; one standalone file per check; configuration in header constants or workflow `env:`; a source-version header; and failing-case tests in this repo for every file.

## 10. Distribution and updates

| Part | How users get it | How it updates |
| --- | --- | --- |
| Skills | The `pitaya` plugin: `/plugin marketplace add <owner>/pitaya`, then `/plugin install pitaya@pitaya`; or copy `skills/<name>/` | Automatically when the plugin version changes |
| Level 1 files | `/setup` copies `templates/` | Re-run `/setup`: it lists stale copies and diffs, and the user decides |
| Recipe files | The user copies them | `CHANGELOG.md` flags recipe fixes; headers carry the version |

Semver; the plugin version matches the git tag; `CHANGELOG.md` lists changes to skills, templates and recipes separately; breaking changes only in major versions (D20).

## 11. Decisions

| # | Decision |
| --- | --- |
| D1 | Levels 0–3 in one harness |
| D2 | Claude Code first; AGENTS.md as the entry point; skills follow the open Agent Skills format; hooks work only in Claude Code |
| D3 | Autonomy is a setting; by default only the Owner merges `main` |
| D4 | Skills ship as a plugin; `/setup` copies the Level 1 files |
| D5 | Level 1 needs one test command that runs; JUnit XML from Level 2 |
| D6 | Level 1 hooks: no pushes to `main` or force pushes, no destructive commands, ask before editing rule files |
| D7 | Level 1 CI: one job running the test command, a required check on `main` |
| D8 | Level 1 permissions: deny secrets, allow common read-only commands, no sandbox |
| D9 | `/setup` chooses where tickets live; Issues by default |
| D10 | Ticket fields: four at Level 1, more at Level 2 |
| D11 | Memory is issues, PRs and git history plus a `handoff` skill; a progress file at Level 3 |
| D12 | `docs/decisions.md` on by default; pitfalls off |
| D13 | The verifier is a fresh subagent by default; a separate session is optional |
| D14 | Second-model review is a Level 3 recipe |
| D15 | Evidence lives in the PR; only screenshots go into the repo |
| D16 | Two fix rounds before escalating, configurable |
| D17 | `evals/` holds harness tasks, run by hand; the first comes from the trial run |
| D18 | Every recipe, hook and skill says when to remove it |
| D19 | `retro` proposes improvements; the Owner approves |
| D20 | Semver, a changelog and version headers in copied files |
| D21 | Owner, Chief, Builder and Verifier stay as concepts mapped to skills |
| D22 | `learning` is an optional skill |
| D23 | The plugin has its own versionless name |
| D24 | Work continues from the existing v3 progress |
| D25 | The plugin is named `pitaya`; the Owner accepts this as the one exception to the no-personal-data rule; accounts and emails stay banned |
| D26 | The earlier CI checks become Level 2 recipes; the bootstrap gate and branch-to-ticket gate are dropped |
| D27 | Every file in the repository is in English |
| D28 | A new repository with a fresh history; the earlier repository keeps the full history of both earlier versions |
| D29 | Agents commit to this repository as the machine account, with its GitHub noreply identity (display name equal to the login); the personal-data scan accepts that form and nothing else personal |

## 12. Failure modes

| Situation | Worst case | Mitigation |
| --- | --- | --- |
| Plugin installed, `/setup` never run (Level 0) | An agent pushes to `main` or deletes tests | Skills suggest `/setup`; `/verify` checks scope and test counts |
| A tool other than Claude Code | Hooks don't run | AGENTS.md carries the same rules; the ruleset still guards `main` |
| A hook blocks normal work | Work stops | The message gives the alternative; rule files only ask; every hook is tested |
| `/setup` would overwrite a project file | The project's changes are lost | The script never overwrites; it reports and the user decides |
| Copied files go stale | Fixed bugs stay in the project | Version headers; re-running `/setup` lists stale copies |
| A plugin update changes skill behaviour | Work in progress changes | Semver; breaking changes only in major versions, in the changelog |
| Autonomy set to agent merging | Unreviewed code reaches `main` | The recipe lists prerequisites; never the default |
| The personal-data exception is read broadly | Other personal data creeps in | The scan still runs; the exception covers only the plugin name |

## 13. Implementation plan

Done before the move to this repository: W0 (design and `suggestion.md`), W1 (plugin name and config fields), W2 (Level 1 templates, three hooks, the install script, `/setup` updates). The Owner reviews each step before the next.

| Step | Content | Done when |
| --- | --- | --- |
| W3 | Skills `plan`, `report`, `handoff`, `retro`, `ask-owner`, `learning`; `docs/concepts/` | Each at most 80 lines; `/plan` and `/handoff` tried on the trial repository |
| W4 | Level 2 recipes and copyable files, ported from the earlier checks; the "protect `main`" recipe | Every copyable file has a failing-case test; tests check that error messages give a fix |
| W5 | Level 3 recipes; `evals/` with the first task; `CHANGELOG.md` | CI green |
| W6 | Trial: move the trial repository to Level 1 with `/setup`, add one Level 2 recipe and prove it blocks; run the hooks in a real Claude Code session | A trial record with evidence |
| W7 | Release `v0.1.0` | The Owner creates the release |

## 14. Open questions

| # | Question | Recommendation |
| --- | --- | --- |
| O4 | Should this repository's own commits use the machine account? | Decided: yes (D29) |
| O6 | Should `/setup` configure rulesets itself? | Decided: no. The machine account isn't an admin; `/setup` hands over the steps |
