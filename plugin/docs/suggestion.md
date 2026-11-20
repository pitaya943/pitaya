# What each level should have

Which components a project developed with coding agents should have at each level, what each component **achieves**, and what it **can't** do. It's based on the frontier labs' published harness guidance and three public harnesses ([sources](#sources)), and it's maintained as that research and the levels evolve. For the plain list of skills, files and recipes in each level, see [`levels.md`](levels.md).

## How to read this

Each component is tagged with how it's enforced, which sets how far you can rely on it:

| Enforcement | When it acts | Reliability | Cost |
| --- | --- | --- | --- |
| **Prose** | When the agent reads and follows it | Lowest: agents can skip or forget it | Lowest: writing a document |
| **Session mechanism** | The moment the agent acts (Claude Code hooks and permission settings) | Medium: always in Claude Code, absent in other tools | Low: one committed settings file |
| **Merge mechanism** | When a pull request merges (CI, branch protection) | Highest: no tool or person gets around it, except someone with bypass rights | Medium: CI and ruleset setup, a few minutes per PR |

Rule of thumb: enforce rules that have no exceptions with the cheapest mechanism that suffices, and leave only judgment calls to prose.

## Overview

| Level | For | In one sentence |
| --- | --- | --- |
| [Level 0](#level-0-skills-only) | Trying it out without touching the repo | Agents get good working habits, but nothing stops them |
| [Level 1](#level-1-the-default) | One person with one or a few agents (**the recommended minimum for every project**) | Agents can't break `main` directly, tests always run, secrets stay unreadable, and "done" is verified independently |
| [Level 2](#level-2-parallel-agents) | Several agents working at once | Each PR stays in its scope, tests can't be quietly removed, and every action traces back to an agent |
| [Level 3](#level-3-milestone-autonomy) | Agents working for long stretches or unattended | `/autopilot` runs a milestone to its end, work continues across sessions, and agents merge into the milestone branch; the Owner signs off each milestone |
| [Level 4](#level-4-max) | Projects where agents should run as far as they can | The most agent authority, with the most verification: another model reviews risky work, and evals measure the harness |

The levels form one spectrum: Level 0 is closest to Matt Pocock's skills, where a person decides and merges everything, and Level 4 to pstack, where agents run on their own. Each level up gives agents more authority and adds the safeguards that authority needs. Pick a lower level for a project you want to keep close control of; [`levels.md`](levels.md#the-spectrum) has the table.

When to move up:

- **To Level 2:** a second agent works in the same repo, or an agent once changed files outside its scope, or a deleted test left CI green.
- **To Level 3:** one piece of work spans several sessions, or agents should keep working while nobody watches (overnight, for example).
- **To Level 4:** Level 3 runs smoothly, and waiting for the Owner is still the bottleneck; or a wrong merge costs enough to want a second model on risky work.

---

## Level 0: skills only

Install the plugin. Nothing in the repository changes.

| Component | Enforcement | What it achieves | What it can't do |
| --- | --- | --- | --- |
| **`tdd` skill** (red, then green) | Prose | Each behaviour gets a test that fails for the right reason before the code exists, so new features come with tests that really fail when the feature breaks | Nothing makes the agent follow it; it can't stop tests being deleted later |
| **`evidence` skill** | Prose | Every "done" comes with the command, its real output and the model that did the work, so reviewers don't have to take claims on trust | It can't prove the output wasn't made up; only a re-run can |
| **`build` skill** | Prose | One ticket, one branch, one PR, with a fixed description that also lists assertions stricter than the spec | It can't keep the agent inside the ticket's files |
| **`verify` skill** (a fresh subagent reading cold) | Prose | A subagent that never saw the work re-runs the tests, mutates the code and probes the spec's edges, then gives PASS or FAIL with evidence. It catches tests that test nothing, and spec gaps: the trial run raised three spec questions | The verifier shares the builder's model and its blind spots; nothing stops a merge without verification |
| **`help` skill** (read only) | Prose | Rebuilds where the project stands from the repository and GitHub, and names the one next step or the page that answers a "how do I" | It only reads; it can be wrong when a state lives somewhere it doesn't look |

**Risk at this level:** an agent can push straight to `main`, read `.env`, and delete a failing test to turn the run green. Every guarantee rests on the agent's discipline.

---

## Level 1: the default

`/setup` copies these files. Every component here is cheap and on every source's minimum list.

| Component | Enforcement | What it achieves | What it can't do |
| --- | --- | --- | --- |
| **AGENTS.md map** (at most 100 lines; CLAUDE.md imports it) | Prose | Every agent tool (Claude Code, Codex, Gemini CLI, Cursor) starts from the same entry point: the test command, what done means, where the docs are. Nobody re-explains the project each session | Agents skim long files; it can't force compliance |
| **`docs/agents/harness.md`** | Prose | Every skill reads one config (Owner, machine account, test command, ticket location, autonomy, fix rounds), so behaviour stays the same across people and sessions | A wrong value is followed faithfully |
| **One test command** | Tool | Agents run the tests after each change, read the result and fix it themselves without waiting for a person. This is what makes self-correction possible | Green only means correct if the tests are good |
| **CI runs the tests, as a required check on `main`** | Merge | A PR with failing tests **can't merge**, whoever opened it. "It passed locally" stops counting | It can't stop tests from being deleted or loosened; that's Level 2's "no weakened tests" |
| **`main` protection** (a ruleset: changes through PRs, only the Owner merges) | Merge | Agents can't change `main` directly; every change goes through a PR and the Owner, so mistakes stay on branches | People with bypass rights can still get around it |
| **Hook: no pushes to `main`, no force pushes** | Session | Stops the command as it's typed and says to open a PR instead, without waiting for the push to fail or rewriting history | Claude Code only; other tools rely on the ruleset above |
| **Hook: no destructive commands** (recursive delete of `/` or home, `git reset --hard`, `git clean -fdx`) | Session | Local work and uncommitted changes can't be wiped by a single command | It lists the most common and least recoverable forms, not every one |
| **Hook: ask before editing rule files** (AGENTS.md, the harness config, `.claude/`, CI workflows) | Session | An agent can't quietly loosen its own rules to get past them; every rule change is seen and approved by a person | Normal maintenance gets one more prompt; other tools lack this layer |
| **Hook: ask before merging** (`gh pr merge`, the merge API, the GitHub tool) | Session | An agent doesn't merge a PR while the harness file says only the Owner merges; at Level 3 with agent-merge it stops asking | The ruleset's required approval is the guarantee; this only stops the attempt early |
| **Permissions in `.claude/settings.json`** (deny secrets, allow common commands) | Session | The Read tool can't open `.env` files (also nested ones), key files or cloud credentials, so secrets don't end up in a conversation or PR by accident. Routine test and git commands stop asking each time | It isn't a sandbox: a shell command such as `cat .env` can still read them, so keep real secrets out of the working tree; agents can still reach the network and run other commands (with a prompt) |
| **A fresh verifier** (`/verify`) | Prose | Every PR comes with an independent verdict and evidence before merge, so the Owner's review starts from the verdict instead of the raw diff | Same as Level 0: shared blind spots; nothing forces verification before merge |
| **Memory files** (`docs/agents/glossary.md`, `learnings.md`, `architecture.md`) | Prose | Agents start from the project's own words, its module map and what earlier work learned the hard way, so they name things consistently, change the right module, and don't repeat a known mistake. The glossary alone makes conversations and code noticeably more concise | They're only as good as their upkeep: `/plan` and `/retro` keep them current, and a stale map misleads |
| **`docs/decisions.md`** (append only) | Prose | The Owner's decisions have one home, so a new session neither asks the same question again nor overturns what was settled | "Append only" is checked by machine only at Level 2 |
| **`handoff` skill** | Prose | When work stops, it leaves the goal, what's done, what's in progress, the next step and where the evidence is, so another person or session can pick it up | It needs a chance to run before the stop |
| **`retro` skill** | Prose | Repeated mistakes become proposals of the form "rule, and what enforces it" (a test, lint, hook, CI or a doc), applied once the Owner approves, so people stop repeating the same reminder | It proposes; it doesn't change anything itself |

**Stopped at this level:** agents breaking `main` directly, merges without running the tests, secrets leaking into conversations, a working tree wiped by one command, agents loosening their own rules.

**Still not stopped:** edits outside a ticket's scope, deleted or loosened tests (CI stays green), and not knowing which agent did what. Those are Level 2.

---

## Level 2: parallel agents

Added from recipes in `docs/guardrails/`. These are the earlier template's CI checks, now separately selectable. Most need tickets to state a scope and the test IDs for their completion conditions.

| Component | Enforcement | What it achieves | What it can't do |
| --- | --- | --- | --- |
| **Machine accounts** (one GitHub account per agent role, Write access only) | Merge | Every push, PR and comment traces back to an agent, and agent accounts can't merge `main` at the GitHub level | More accounts and tokens to manage |
| **Commit-author check** | Merge | Every commit in a PR is authored by the expected machine account (checked by GitHub account, not email), so commits under the wrong identity can't merge | It can't tell apart sessions sharing one account |
| **Scope check** (the ticket's scope) | Merge | A PR changes only the paths its ticket lists, so parallel agents can't overwrite each other and drive-by edits can't merge | A wide scope makes it useless; tickets must state scope |
| **Read-only paths** | Merge | Rules, specs, CI config and the decision log can't change in a ticket PR unless the ticket names that file, so code can't bend the spec to fit | It checks ticket PRs only; the Owner's own changes are unaffected |
| **No weakened tests** (JUnit comparison) | Merge | Every test that passes on the base must exist and pass on the PR. Deleting, renaming or skipping one blocks the merge even when everything else is green | Real renames need the Owner to record the mapping. A loosened assertion in a test that still exists isn't caught; the verifier's mutation checks cover that |
| **Done-when check** | Merge | Every completion condition in the ticket has a test ID that exists and passes, so "done but untested" can't merge | It can't judge whether the test means what the condition means |
| **Append-only files** (a changelog, the decision log) | Merge | Listed files only gain lines in a PR, so history can't be rewritten | It can't check that the new lines are right |
| **Serial resources** (migrations, lockfiles) | Merge | Only one ticket at a time changes a given resource, avoiding two PRs that are each fine but conflict once merged | Someone has to keep the in-progress list (a board or issue labels) |
| **Evidence check** | Merge | A PR without an evidence section, or a UI change without screenshots, can't merge, so the Owner always sees evidence | It checks that evidence exists, not that it's true |
| **`design` skill** (scenarios first, then interfaces, data flow, notifications and state owners) | Prose | Parallel builders share one contract: every ticket comes from a Given/When/Then scenario with a named test, and `/report` checks each scenario at the end | It's only as good as the scenarios; a missed behaviour stays missed |
| **Verify the real app** (a project skill that drives the UI, CLI or API) | Prose, checkable | Catches "every test passes, but the feature is broken": the verifier drives the feature as a user would and attaches evidence | It needs a runnable, isolated app and upkeep as features change |

**Stopped at this level:** parallel agents overwriting each other, failing tests deleted to turn CI green, specs bent to fit the code, work nobody can attribute, two migrations colliding.

---

## Level 3: milestone autonomy

Added from recipes. This level lets work continue across sessions, and lets agents merge inside a milestone while the Owner keeps `main`.

| Component | Enforcement | What it achieves | What it can't do |
| --- | --- | --- | --- |
| **Progress file and start-up routine** (read the progress, read the git log, run the tests once, then pick the next item) | Prose | A new session takes over in minutes without redoing finished work or building on a broken state. Anthropic's long-running harness relies on exactly this | A wrong progress file misleads the next session |
| **A JSON feature list** (agents may change only the "passes" field) | Prose, checkable | Agents can't delete or rewrite unfinished requirements, only mark them passing, so long work doesn't quietly shrink its scope | A machine guarantee needs an extra check that only that field changed |
| **`autopilot` skill** (runs the active milestone; stateless ticks woken by events, a loop or a schedule) | Prose | One command runs a milestone to its end: fresh builders and verifiers per ticket, merges when the harness allows, a line per tick on a tracking issue | It stops at every Owner gate (plan, sensitive areas, fix rounds, sign-off, budget); it plans nothing itself and needs something to wake it |
| **Agent-merge policy** (agents merge ticket PRs into the milestone branch after CI is green and the verdict is PASS) | Merge | A milestone runs to its end without waiting for a person; `main` changes only when the Owner merges the milestone | Ticket PRs reach the milestone branch unread; the Owner reviews the milestone as a whole, and a bad one costs that milestone |
| **"When to remove" reviews** | Prose | Every component states what evidence shows it's no longer needed, so as models improve the harness can shrink on evidence instead of only growing | It works only if retros actually happen |

---

## Level 4: max

Added from recipes. The most agent authority pitaya offers, closest to pstack, with the verification that authority needs.

| Component | Enforcement | What it achieves | What it can't do |
| --- | --- | --- | --- |
| **Second-model review** (another vendor or model) | Prose | Another model catches the first one's blind spots on sensitive or risky PRs | It adds cost and time; two models can still be wrong together |
| **Project evals** (20–50 tasks drawn from real failures) | Tool | Before and after changing a skill, a prompt or a model, run the set and compare numbers instead of impressions | The set takes time to build and maintain; too few tasks give noisy numbers |
| **Deep verification** (risk tags, interrogation of high-risk PRs, a swarm and a decision-log audit per milestone, an arena for contested designs) | Prose | Agents can cut and merge a whole milestone while the Owner reads only what the Attention section and the scenario table point at; a second model's findings count only when a run reproduces them | Two to four times the verification cost on high-risk tickets; the gain should be measured with project evals |

---

## Not recommended up front

| Practice | Why not |
| --- | --- |
| Turning on Levels 2–3 from day one | The earlier template showed it: 16 setup questions and 11 checks before any work make the process heavy and slow development down. Start at Level 1 and move up on the matching signal |
| A long AGENTS.md instead of mechanisms | Agents skim long files; rules with no exceptions are reliable only as hooks or CI |
| Letting an agent grade its own work | Every source warns that agents overrate their own results; the verifier must have a fresh context |
| Trusting a green CI alone | Green means the existing tests passed. It stays green when tests are deleted or loosened |

## Sources

- Anthropic: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (2024-12), [Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (2025-09), [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (2025-09), [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk) (2025-09), [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) (2025-10), [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (2025-11), [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (2026-01), [Harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) (2026-03), [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices), [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- OpenAI: [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/) (2026-02; summarized from secondary sources because the page couldn't be opened during research), [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) (guardrails)
- Google: [Gemini CLI](https://github.com/google-gemini/gemini-cli) (context files, hooks, sandboxing, Agent Skills support)
- Open formats: [AGENTS.md](https://github.com/agentsmd/agents.md), [Agent Skills](https://github.com/agentskills/agentskills)
- Public harnesses: [mattpocock/skills](https://github.com/mattpocock/skills), [pstack](https://github.com/cursor/plugins/tree/main/pstack), [gstack](https://github.com/garrytan/gstack)
- This project's own trial: a `/build` → `/verify` run on a money-calculation ticket (PASS, three spec questions, nine skill fixes)
