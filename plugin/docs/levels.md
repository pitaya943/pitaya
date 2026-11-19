# What each level includes

<!-- Generated from components.json. Edit the manifest, not this file. -->

Every part of the harness by level: skills, files in your repository, guardrail recipes and the GitHub settings the Owner makes. Each level includes everything in the levels below it. **Requires** must be in place first; **Works better with** is optional. For what each part achieves and what it can't do, see [`suggestion.md`](suggestion.md).

Every skill ships with the plugin, so all of them are installed from Level 0. A skill is listed at the level where it joins the recommended workflow.

## Level 0: skills only

Install the plugin. Nothing in the repository changes. Without a harness file, the skills use safe defaults: the current account, the Owner merges, two fix rounds.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Skill | [`skill:tdd`](../skills/tdd/SKILL.md) | - | - | A failing test before the code, one behaviour at a time |
| Skill | [`skill:evidence`](../skills/evidence/SKILL.md) | - | - | "Done" comes with commands, real output and the model's name |
| Skill | [`skill:plan`](../skills/plan/SKILL.md) | - | - | Requests become tickets with completion conditions, dependencies and scope, approved by the Owner |
| Skill | [`skill:build`](../skills/build/SKILL.md) | - | `skill:tdd`, `skill:evidence` | One ticket, one branch, one PR, red then green |
| Skill | [`skill:verify`](../skills/verify/SKILL.md) | - | `skill:evidence` | A fresh subagent re-runs the work and posts PASS or FAIL |
| Skill | [`skill:report`](../skills/report/SKILL.md) | - | - | A summary of merged work for the Owner, every claim linked to evidence |
| Skill | [`skill:ask-owner`](../skills/ask-owner/SKILL.md) | - | - | Unclear or risky decisions go to the Owner with options instead of a guess |

## Level 1: the default

Includes everything in Level 0. Run `/setup`; it copies the files and fills in the harness file. The Owner then makes the GitHub settings in protect-main.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Skill | [`skill:setup`](../skills/setup/SKILL.md) | - | - | Installs the chosen files without overwriting anything, and writes the harness file |
| File, filled in | [`harness-file`](../skills/setup/harness-template.md): `docs/agents/harness.md` | `skill:setup` | - | The config every skill reads first: Owner, machine account, test command, tickets, level |
| Files | [`agents-map`](../templates/AGENTS.md): [`AGENTS.md`](../templates/AGENTS.md), [`CLAUDE.md`](../templates/CLAUDE.md) | - | - | The map every agent tool starts from; CLAUDE.md makes Claude Code read it |
| Files | [`memory-files`](../templates/docs/agents/README.md): [`docs/agents/glossary.md`](../templates/docs/agents/glossary.md), [`docs/agents/architecture.md`](../templates/docs/agents/architecture.md), [`docs/agents/learnings.md`](../templates/docs/agents/learnings.md) | - | - | The project's words, its module map, and what earlier work learned the hard way |
| Files | [`decisions`](../templates/docs/decisions.md): [`docs/decisions.md`](../templates/docs/decisions.md) | - | - | The Owner's decisions in one place, append only |
| Files | [`session-guards`](../templates/.claude/settings.json): [`.claude/settings.json`](../templates/.claude/settings.json), [`.claude/hooks/no_push_main.py`](../templates/.claude/hooks/no_push_main.py), [`.claude/hooks/no_destructive.py`](../templates/.claude/hooks/no_destructive.py), [`.claude/hooks/ask_on_rule_files.py`](../templates/.claude/hooks/ask_on_rule_files.py) | - | - | Denies reading secrets; hooks block pushes to main, wiping commands and silent rule edits |
| Files | [`tests-workflow`](../templates/.github/workflows/tests.yml): [`.github/workflows/tests.yml`](../templates/.github/workflows/tests.yml) | - | - | Runs the test command on every PR |
| Recipe | [`protect-main`](guardrails/protect-main.md) | - | `tests-workflow` | A ruleset: changes reach main only through PRs, tests must pass, only the Owner merges |
| Skill | [`skill:handoff`](../skills/handoff/SKILL.md) | - | - | Notes that let another session take over stopped work |
| Skill | [`skill:learning`](../skills/learning/SKILL.md) | `harness-file` | - | An optional review for the Owner, turned on in the harness file |
| Skill | [`skill:retro`](../skills/retro/SKILL.md) | - | `memory-files` | Repeated mistakes become proposed rules with an enforcer, and spent guardrails get retired |

## Level 2: parallel agents

Includes everything in Level 1. Add the recipes you need, one at a time; each is a copyable check that becomes a required status.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Recipe | [`machine-account`](guardrails/machine-account.md) | `protect-main` | - | One GitHub account per agent role, with Write access only |
| Recipe | [`commit-author`](guardrails/commit-author.md) | `protect-main`, `machine-account` | - | Every commit in a PR is authored by the expected machine account |
| Recipe | [`scope`](guardrails/scope.md) | `protect-main`, `machine-account` | `read-only-paths`, `skill:plan`, `skill:build` | A PR changes only the paths its ticket lists |
| Recipe | [`read-only-paths`](guardrails/read-only-paths.md) | `protect-main`, `machine-account` | `scope` | Rules, specs and CI can't change in a ticket PR unless the ticket names the file |
| Recipe | [`no-weakened-tests`](guardrails/no-weakened-tests.md) | `protect-main`, `machine-account` | - | Every test that passes on the base still exists and passes |
| Recipe | [`done-when`](guardrails/done-when.md) | `protect-main`, `machine-account` | `no-weakened-tests`, `skill:plan`, `skill:verify` | Every completion condition has a test that exists and passes |
| Recipe | [`append-only`](guardrails/append-only.md) | `protect-main`, `machine-account` | `decisions` | Listed files only gain lines |
| Recipe | [`serial-resources`](guardrails/serial-resources.md) | `protect-main`, `machine-account` | `skill:plan` | Only one ticket at a time changes a migration, lockfile or other shared resource |
| Recipe | [`evidence`](guardrails/evidence.md) | `protect-main`, `machine-account` | `skill:build`, `skill:evidence` | A PR without an evidence section, or a UI change without screenshots, can't merge |

## Level 3: long-running autonomy

Includes everything in Level 2. `agent-merge` comes last: it requires the main Level 2 checks and a second-model review.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Recipe | [`progress-file`](guardrails/progress-file.md) | `protect-main`, `machine-account` | `skill:handoff` | A start-up routine and a feature list where agents may only mark items as passing |
| Recipe | [`second-model-review`](guardrails/second-model-review.md) | `skill:verify` | - | Another model reviews sensitive or risky PRs |
| Recipe | [`agent-merge`](guardrails/agent-merge.md) | `protect-main`, `scope`, `read-only-paths`, `no-weakened-tests`, `done-when`, `second-model-review`, `skill:verify` | - | Agents merge after CI is green and the latest verdict on the current commit is PASS |
| Recipe | [`project-evals`](guardrails/project-evals.md) | - | - | A task set drawn from real failures, run before and after a harness change |

## What the project needs

Some components need something from the project itself, not from another component.

| Need | Meaning | Needed by |
| --- | --- | --- |
| `github` | A GitHub repository, so rulesets and required checks exist | `protect-main`, `machine-account` |
| `tickets` | Every agent PR comes from a ticket, on a branch named ticket/<id>-<slug> (/plan writes tickets, /build names branches) | `scope`, `read-only-paths`, `no-weakened-tests`, `done-when`, `append-only`, `serial-resources`, `evidence` |
| `ticket-scope` | Each ticket lists the paths it may change under "## Scope" | `scope` |
| `ticket-test-ids` | Each ticket names one test per completion condition under "## Test IDs" | `done-when` |
| `junit-xml` | The test command can write JUnit XML | `no-weakened-tests`, `done-when` |
| `verifier-account` | A verifier account the builder can't post as, in the repository variable VERIFIER_ACCOUNTS | `agent-merge` |

## Choosing your own set

Start from a level, then add or remove single components. [`select_components.py`](../skills/setup/scripts/select_components.py) adds whatever a component requires, refuses to remove something still required, warns about missing recommendations, and prints the steps in order. It only prints a plan; it copies nothing and changes no settings. Run it from the plugin's folder:

```bash
python3 skills/setup/scripts/select_components.py --level 1 --add scope --remove decisions
```

That run starts from Level 1, adds `scope` and the `machine-account` it requires, leaves out the decision log, and labels the result `Level 1 + scope, machine-account without decisions`. `/setup` records that label in the harness file.
