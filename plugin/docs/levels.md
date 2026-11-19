# What each level includes

The complete list of what belongs to each level: skills, files in your repository, guardrail recipes and the settings the Owner makes on GitHub. Each level includes everything in the levels below it. For what each part achieves and what it can't do, see [`suggestion.md`](suggestion.md).

Every skill ships with the plugin, so all of them are installed from Level 0. A skill is listed at the level where it becomes part of the recommended workflow, usually because it needs a file from that level.

## Level 0: skills only

Install the plugin. Nothing in the repository changes.

| Kind | Item | What it adds |
| --- | --- | --- |
| Skill | [`tdd`](../skills/tdd/SKILL.md) | A failing test before the code, one behaviour at a time |
| Skill | [`evidence`](../skills/evidence/SKILL.md) | "Done" comes with commands, real output and the model's name |
| Skill | [`plan`](../skills/plan/SKILL.md) | Requests become tickets with completion conditions, dependencies and scope, approved by the Owner |
| Skill | [`build`](../skills/build/SKILL.md) | One ticket, one branch, one PR, red then green |
| Skill | [`verify`](../skills/verify/SKILL.md) | A fresh subagent re-runs the work and posts PASS or FAIL |
| Skill | [`report`](../skills/report/SKILL.md) | A summary of merged work for the Owner, every claim linked to evidence |
| Skill | [`ask-owner`](../skills/ask-owner/SKILL.md) | Unclear or risky decisions go to the Owner with options instead of a guess |

Without a harness file, these skills use safe defaults: the current account, the Owner merges, two fix rounds.

## Level 1: the default

Includes everything in Level 0. Run `/setup`, then make the GitHub settings below.

| Kind | Item | What it adds |
| --- | --- | --- |
| Skill | [`setup`](../skills/setup/SKILL.md) | Installs this level's files without overwriting anything, and writes the harness file |
| Skill | [`handoff`](../skills/handoff/SKILL.md) | Notes that let another session take over stopped work |
| Skill | [`learning`](../skills/learning/SKILL.md) | An optional review for the Owner, turned on in the harness file |
| File, filled in | `docs/agents/harness.md`, from [`harness-template.md`](../skills/setup/harness-template.md) | The config every skill reads first: Owner, machine account, test command, tickets, level |
| File | [`AGENTS.md`](../templates/AGENTS.md) | The map every agent tool starts from |
| File | [`CLAUDE.md`](../templates/CLAUDE.md) | Makes Claude Code read `AGENTS.md` |
| File | [`docs/agents/glossary.md`](../templates/docs/agents/glossary.md) | The project's words |
| File | [`docs/agents/architecture.md`](../templates/docs/agents/architecture.md) | The module map |
| File | [`docs/agents/learnings.md`](../templates/docs/agents/learnings.md) | What earlier work learned the hard way |
| File | [`docs/decisions.md`](../templates/docs/decisions.md) | The Owner's decisions, append only (leave it out with `--no-decisions`) |
| File | [`.claude/settings.json`](../templates/.claude/settings.json) | Denies reading secrets, allows routine commands, registers the hooks |
| Hook | [`.claude/hooks/no_push_main.py`](../templates/.claude/hooks/no_push_main.py) | Blocks pushes to `main` and force pushes |
| Hook | [`.claude/hooks/no_destructive.py`](../templates/.claude/hooks/no_destructive.py) | Blocks commands that wipe work, such as `git reset --hard` |
| Hook | [`.claude/hooks/ask_on_rule_files.py`](../templates/.claude/hooks/ask_on_rule_files.py) | Asks a person before an agent edits its own rules |
| Workflow | [`.github/workflows/tests.yml`](../templates/.github/workflows/tests.yml) | Runs the test command on every PR |
| Recipe, Owner on GitHub | [protect-main](guardrails/protect-main.md) | A ruleset: changes reach `main` only through PRs, `tests` is a required check, only the Owner merges |

## Level 2: parallel agents

Includes everything in Level 1. Add the recipes you need, one at a time; each is a copyable check plus a required status. Most need tickets that state a scope and the test IDs for their completion conditions, and some need the test command to write JUnit XML.

| Kind | Item | What it adds |
| --- | --- | --- |
| Recipe | [machine-account](guardrails/machine-account.md) | One GitHub account per agent role, with Write access only |
| Recipe | [commit-author](guardrails/commit-author.md) | Every commit in a PR is authored by the expected machine account |
| Recipe | [scope](guardrails/scope.md) | A PR changes only the paths its ticket lists |
| Recipe | [read-only-paths](guardrails/read-only-paths.md) | Rules, specs and CI can't change in a ticket PR unless the ticket names the file |
| Recipe | [no-weakened-tests](guardrails/no-weakened-tests.md) | Every test that passes on the base still exists and passes |
| Recipe | [done-when](guardrails/done-when.md) | Every completion condition has a test that exists and passes |
| Recipe | [append-only](guardrails/append-only.md) | Listed files only gain lines |
| Recipe | [serial-resources](guardrails/serial-resources.md) | Only one ticket at a time changes a migration, lockfile or other shared resource |
| Recipe | [evidence](guardrails/evidence.md) | A PR without an evidence section, or a UI change without screenshots, can't merge |

## Level 3: long-running autonomy

Includes everything in Level 2. `agent-merge` needs every Level 2 check turned on first.

| Kind | Item | What it adds |
| --- | --- | --- |
| Skill | [`retro`](../skills/retro/SKILL.md) | Repeated mistakes become proposed rules with an enforcer, and spent guardrails get retired |
| Recipe | [progress-file](guardrails/progress-file.md) | A start-up routine and a feature list where agents may only mark items as passing |
| Recipe | [second-model-review](guardrails/second-model-review.md) | Another model reviews sensitive or risky PRs |
| Recipe | [agent-merge](guardrails/agent-merge.md) | Agents merge after CI is green and the latest verdict on the current commit is PASS |
| Recipe | [project-evals](guardrails/project-evals.md) | A task set drawn from real failures, run before and after a harness change |

