# What each level includes

<!-- Generated from components.json. Edit the manifest, not this file. -->

Every part of the harness by level: skills, files in your repository, guardrail recipes and the GitHub settings the Owner makes. Each level includes everything in the levels below it. **Requires** must be in place first; **Works better with** is optional. For what each part achieves and what it can't do, see [`suggestion.md`](suggestion.md).

Every skill ships with the plugin, so all of them are installed from Level 0. A skill is listed at the level where it joins the recommended workflow. There is no custom mix: pick the level whose authority you want to give agents.

## The spectrum

Each level up gives agents more authority and adds the safeguards that authority needs. Level 0 is closest to Matt Pocock's skills, where a person decides and merges everything; Level 4 is closest to pstack, where agents run on their own. Pick a lower level for a project you want to keep close control of.

| Level | Agent authority | What the Owner does | What keeps it safe |
| --- | --- | --- | --- |
| 0 | Writes code in your session | Every decision and every merge | Your own review |
| 1 | Opens PRs, runs a fresh verifier | Approves plans, merges every PR | Hooks, CI, protected main |
| 2 | A Chief dispatches parallel builders | Approves plans, merges every PR | Ticket checks: scope, tests, evidence |
| 3 | Merges tickets into the milestone branch | Signs off each milestone, approves each cut | Verdict on the head from another session, milestone branch as blast radius |
| 4 | Also cuts the next milestone inside its branch | Signs off each milestone, owns the roadmap | Interrogation of high-risk PRs, a swarm and log audit per milestone, evals |

## What the levels assume

pitaya assumes **cooperating agents**: agents that try to do the work as asked, and sometimes get it wrong. It defends against three things, in this order: its own rules contradicting each other or claiming to prove what they don't; honest mistakes, such as loosening a test to get green, editing CI, verifying one's own work or dropping changes in a merge; and text from outside (issues, PR comments, upstream code) steering an agent. It does not defend against an agent that sets out to get round it: one that forges a verdict, rewrites the workflow that judges it, sidesteps a hook or commits under another email. [Access](concepts/access.md#what-pitaya-assumes) lists where that line runs.

What follows from it:

- **Level 3 means agents you trust.** Every agent role uses one machine account, so the verdict that lets agents merge guards against mistakes, not forgery: it stops a stale or missing verification and a session passing its own work, not a session that lies about who it is.
- **Don't run Levels 3 and 4 with agents, models or code you don't trust.** Below Level 3 a person reads and merges every PR, which is the defence those levels lack.
- **Hooks prevent accidents.** They are not a security boundary: a script, another tool or a differently spelled command gets past them. The rulesets are the boundary.
- **The tripwire is an `undisclosed` row** in a verdict's Attention section: a change or pivot the PR should have declared and didn't. When one appears, the Owner reviews it and decides whether the assumption still holds, or whether to add the stricter defences (a separate verifier account, checks that run from the base branch only, signed commits).

## Level 0: skills only

Install the plugin. Nothing in the repository changes. Closest to Matt Pocock's skills: the agent works in your session and you decide and merge everything. Without a harness file, the skills use safe defaults: the current account, the Owner merges, two fix rounds.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Skill | [`skill:tdd`](../skills/tdd/SKILL.md) | - | - | A failing test before the code, one behaviour at a time |
| Skill | [`skill:evidence`](../skills/evidence/SKILL.md) | - | - | "Done" comes with commands, real output and the model's name |
| Skill | [`skill:plan`](../skills/plan/SKILL.md) | - | - | A roadmap of milestones, then each milestone cut into tickets with conditions and scope, approved by the Owner |
| Skill | [`skill:build`](../skills/build/SKILL.md) | - | `skill:tdd`, `skill:evidence` | One ticket, one branch, one PR, red then green |
| Skill | [`skill:verify`](../skills/verify/SKILL.md) | - | `skill:evidence` | A fresh subagent re-runs the work and posts PASS or FAIL |
| Skill | [`skill:report`](../skills/report/SKILL.md) | - | - | A summary of merged work for the Owner, every claim linked to evidence |
| Skill | [`skill:ask-owner`](../skills/ask-owner/SKILL.md) | - | - | Unclear or risky decisions go to the Owner with options instead of a guess |
| Skill | [`skill:help`](../skills/help/SKILL.md) | - | - | Where the project stands and the next command, or how to do something; read only |

## Level 1: the default

Includes everything in Level 0. Run `/setup`; it copies the files and fills in the harness file. The Owner then makes the GitHub settings in protect-main.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Skill | [`skill:setup`](../skills/setup/SKILL.md) | - | - | Installs the chosen files without overwriting anything, and writes the harness file |
| File, filled in | [`harness-file`](../skills/setup/harness-template.md): `docs/agents/harness.md` | `skill:setup` | - | The config every skill reads first: Owner, machine account, test command, tickets, level |
| Files | [`agents-map`](../templates/AGENTS.md): [`AGENTS.md`](../templates/AGENTS.md), [`CLAUDE.md`](../templates/CLAUDE.md) | - | - | The map every agent tool starts from; CLAUDE.md makes Claude Code read it |
| Files | [`memory-files`](../templates/docs/agents/README.md): [`docs/agents/glossary.md`](../templates/docs/agents/glossary.md), [`docs/agents/architecture.md`](../templates/docs/agents/architecture.md), [`docs/agents/learnings.md`](../templates/docs/agents/learnings.md) | - | - | The project's words, its module map, and what earlier work learned the hard way |
| Files | [`decisions`](../templates/docs/decisions.md): [`docs/decisions.md`](../templates/docs/decisions.md) | - | - | The Owner's decisions in one place, append only |
| Files | [`session-guards`](../templates/.claude/settings.json): [`.claude/settings.json`](../templates/.claude/settings.json), [`.claude/hooks/no_push_main.py`](../templates/.claude/hooks/no_push_main.py), [`.claude/hooks/no_destructive.py`](../templates/.claude/hooks/no_destructive.py), [`.claude/hooks/ask_on_rule_files.py`](../templates/.claude/hooks/ask_on_rule_files.py), [`.claude/hooks/ask_on_merge.py`](../templates/.claude/hooks/ask_on_merge.py) | - | - | Read denied on secrets, git denied `--output` and the like; hooks block main pushes and wipes, ask on rule edits, merges |
| Files | [`tests-workflow`](../templates/.github/workflows/tests.yml): [`.github/workflows/tests.yml`](../templates/.github/workflows/tests.yml) | - | - | Runs the test command on every PR |
| Recipe | [`protect-main`](guardrails/protect-main.md) | - | `tests-workflow` | A ruleset: changes reach main only through PRs, tests must pass, only the Owner merges |
| Skill | [`skill:handoff`](../skills/handoff/SKILL.md) | - | - | Notes that let another session take over stopped work |
| Skill | [`skill:learning`](../skills/learning/SKILL.md) | `harness-file` | - | An optional review for the Owner, turned on in the harness file |
| Skill | [`skill:retro`](../skills/retro/SKILL.md) | - | `memory-files` | Repeated mistakes become proposed rules with an enforcer, and spent guardrails get retired |

## Level 2: parallel agents

Includes everything in Level 1. Add the recipes one at a time; each is a copyable check that becomes a required status.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Skill | [`skill:design`](../skills/design/SKILL.md) | `skill:plan` | - | Scenarios first, then interfaces, data flow, notifications and state owners; tickets come from the scenarios |
| Recipe | [`machine-account`](guardrails/machine-account.md) | `protect-main` | - | One GitHub account per agent role, with Write access only |
| Recipe | [`commit-author`](guardrails/commit-author.md) | `protect-main`, `machine-account` | - | Every commit in a PR is authored by the expected machine account |
| Recipe | [`scope`](guardrails/scope.md) | `protect-main`, `machine-account` | `read-only-paths`, `skill:plan`, `skill:build` | A PR changes only the paths its ticket lists |
| Recipe | [`read-only-paths`](guardrails/read-only-paths.md) | `protect-main`, `machine-account` | `scope` | Rules, specs and CI can't change in a ticket PR unless the ticket names the file |
| Recipe | [`no-weakened-tests`](guardrails/no-weakened-tests.md) | `protect-main`, `machine-account` | - | Every test that passes on the base still exists and passes |
| Recipe | [`done-when`](guardrails/done-when.md) | `protect-main`, `machine-account` | `no-weakened-tests`, `skill:plan`, `skill:verify` | Every completion condition has a test that exists and passes |
| Recipe | [`append-only`](guardrails/append-only.md) | `protect-main`, `machine-account` | `decisions` | Listed files only gain lines |
| Recipe | [`serial-resources`](guardrails/serial-resources.md) | `protect-main`, `machine-account` | `skill:plan` | Only one ticket at a time changes a migration, lockfile or other shared resource |
| Recipe | [`verify-app`](guardrails/verify-app.md) | - | `skill:verify` | A project skill that drives the real app as a user would, with evidence |
| Recipe | [`multi-account`](guardrails/multi-account.md) | `protect-main`, `machine-account` | - | Only with several agent accounts: CODEOWNERS, so only the Owner's approval counts |
| Recipe | [`evidence`](guardrails/evidence.md) | `protect-main`, `machine-account` | `skill:build`, `skill:evidence` | A PR without an evidence section, or a UI change without screenshots, can't merge |

## Level 3: milestone autonomy

Includes everything in Level 2. Agents merge ticket PRs into the milestone branch and `/autopilot` runs a milestone; the Owner signs off each milestone and approves each cut.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Skill | [`skill:autopilot`](../skills/autopilot/SKILL.md) | `skill:build`, `skill:verify`, `skill:report`, `protect-main`, `machine-account`, `scope` | `agent-merge`, `read-only-paths`, `no-weakened-tests`, `done-when` | Runs the active milestone: hands tickets to fresh builders and verifiers, merges when allowed, stops at Owner gates |
| Recipe | [`progress-file`](guardrails/progress-file.md) | `protect-main`, `machine-account` | `skill:handoff` | A start-up routine and a feature list where agents may only mark items as passing |
| Recipe | [`agent-merge`](guardrails/agent-merge.md) | `protect-main`, `machine-account`, `scope`, `read-only-paths`, `no-weakened-tests`, `done-when`, `skill:verify` | - | Agents merge ticket PRs into milestone branches on another session's PASS for the head; the Owner merges main |

## Level 4: max

Includes everything in Level 3. Closest to pstack: the most agent authority, with the most verification. The Owner's gate is the milestone sign-off.

| Kind | Component | Requires | Works better with | What it adds |
| --- | --- | --- | --- | --- |
| Recipe | [`second-model-review`](guardrails/second-model-review.md) | `skill:verify` | `agent-merge` | Another model reviews sensitive or risky PRs |
| Recipe | [`deep-verification`](guardrails/deep-verification.md) | `second-model-review`, `skill:design`, `skill:verify`, `skill:report` | `verify-app`, `project-evals`, `skill:autopilot` | Risk tags, interrogation of high-risk PRs, a swarm and a log audit per milestone, an arena for contested designs |
| Recipe | [`project-evals`](guardrails/project-evals.md) | - | - | A task set drawn from real failures, run before and after a harness change |

## What the project needs

Some components need something from the project itself, not from another component.

| Need | Meaning | Needed by |
| --- | --- | --- |
| `github` | A GitHub repository, so rulesets and required checks exist | `protect-main`, `machine-account` |
| `tickets` | Every agent PR comes from a ticket, on a branch named ticket/<id>-<slug>: docs/tickets/T-<nnn>.md files (recommended, optionally mirrored by issues) or issues (/plan writes tickets, /build names branches) | `scope`, `read-only-paths`, `no-weakened-tests`, `done-when`, `append-only`, `serial-resources`, `evidence`, `skill:autopilot` |
| `ticket-scope` | Each ticket lists the paths it may change under "## Scope" | `scope` |
| `ticket-test-ids` | Each ticket names one test per completion condition under "## Test IDs" | `done-when` |
| `junit-xml` | The test command can write JUnit XML | `no-weakened-tests`, `done-when` |
