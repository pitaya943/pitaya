# Changelog

Changes are grouped by what users copy or install: skills, templates and recipes.

## 0.1.4 (2026-11-20)

The two W8 part 2 fixes that change the merge gate (D58).

### Recipes

- `agent-merge`: a PASS carries over GitHub's "Update branch" and nothing else. The check fetches the PR's commits as data and passes a head only if its tree equals the current base merged into the PASS head; a change folded into that merge, or any later commit, needs a new verdict. A FAIL on the PASS head stops the carry. Sync PRs need no verdict when they only merge the default branch into a milestone.
- The shared "Find the ticket" step recognises sync PRs (`sync/<slug>` into `milestone/<id>`): it passes one only when its tree is exactly the milestone merged with the newest default-branch commit it contains, and fails any other change or a conflict.

### Skills

- `plan/milestones.md`: bring `main` into a milestone through a sync PR, never by pushing to the milestone branch or with "Update branch" on a PR from `main`. `autopilot` opens a sync PR when `main` moved.

## 0.1.3 (2026-11-20)

Fixes for the problems the W8 trial found at Level 2 (D57). The two that change the merge gate (P14, P20) follow in 0.1.4.

### Skills

- `build` fetches its base before branching and checks the ticket file is on it (a cloud checkout's remote refs can be stale), and reads the learning proposals in the verdicts of PRs already merged into the milestone.
- `verify`: checklist item 6 checks error messages by mutation (change one character; a substring or prefix match fails the item). Verdicts say "Verify round: n of at most m" and the exact next step, and fix rounds are named as such.
- `report`: the closing plan PR adds `docs/reports/M<n>.md`, and the milestone PR lists `Closes #<n>` for every done ticket's issue mirror.
- `plan`: the ticket template states the Test ID format.
- `setup`: the hand-over gives the milestone ruleset the same bypass as `main`.

### Templates

- `AGENTS.md`: a "Branches" section grants pitaya's branch names once for every session, so cloud sessions don't need the permission pasted each time.
- `tests.yml`: the setup comment names `actions/setup-python` v7 and `actions/setup-node` v5.

### Recipes

- `done-when` accepts pytest-path Test IDs (`tests/test_x.py::test_y`) and treats an ID without parameters as all of a parametrized test's cases.
- Plan PRs may add `docs/reports/*.md`.
- `protect-main`: the `protect-milestones` ruleset has a bypass list.
- The setup comments in `no-weakened-tests` and `done-when` name `actions/setup-python` v7.

### Docs

- `concepts/escalation.md`: verify rounds and fix rounds alternate, verify 1, fix 1, verify 2, fix 2, verify 3, escalate.

## 0.1.2 (2026-11-20)

Fixes for the problems the W8 trial found at Level 1 (D55).

### Skills

- `build`, `plan` and `autopilot` insist on pitaya's branch names (`ticket/<id>-<slug>`, `plan/<slug>`, `milestone/M<n>`). In a session with an assigned branch, as cloud sessions have, they ask the user to allow those names instead of using the assigned branch; `autopilot` passes the permission to the sessions it starts.
- `evidence`: when the environment forbids model identifiers in repository text, the model line says "withheld" with the reason, and the Owner gets the model in the session.
- `plan`: every worked example in a condition is computed or run before it's written; the ticket template says so under "Done when".
- `plan/milestones.md`: when the tools can't create GitHub milestones for the issue mirror, the plan PR says so and lists them for the Owner.
- `build`: each fix round also updates the PR description's "How to verify" and "Scope".
- Milestone branches at every level (D56): `build` creates a missing `milestone/M<n>` from `main` instead of falling back to `main`; `plan/milestones.md` says who creates it after the Owner's merge; `help` reports a missing branch or a milestone ticket PR aimed at `main`.
- `verify`: the verdict's "Round" line links the Owner's authorisation for a round beyond "Fix rounds".

### Docs

- `concepts/states.md` no longer says milestone branches start at Level 3; they exist at every level, as D44 decided.
- `concepts/escalation.md`: the Owner may authorise an extra fix round; it runs in a fresh session, and its verdict links the authorisation.
- README: cloud sessions start by allowing pitaya's branch names.

## 0.1.1 (2026-11-20)

### Skills

- Every `gh` command in the skills names the GitHub tool alternative, for sessions where `gh` can't reach GitHub, such as cloud sessions (D54).

### Docs

- README: a "Cloud sessions" section. Cloud sessions load the plugins their environment's setup script installs, so the install is the same two commands in the setup script (D54).
- `skills/README.md` no longer links to `docs/design.md`, which isn't shipped.

## 0.1.0 (2026-11-20)

### Skills

- `/verify` doesn't open `docs/handoff/`; `/handoff` writes notes on the branch only as a last resort and removes them before review. `autopilot/tick.md` defers to `docs/concepts/states.md`. A test now checks that every path a role's skill uses is R or W in that role's column of `access.md` (D50).

- New skill `help` (D49): read only; says where the project stands, what waits on whom and the next command, or how to do something. PR decision logs gain an `Options` column, filled in when there were two or more real options. `plan/adr-template.md`: big decisions with real options get a record in `docs/adr/`, linked from `docs/decisions.md`.

- Level 4 (D48): tickets carry a Risk tag; `/verify` interrogates high-risk PRs (`verify/interrogate.md`, reproduce or drop); `/report M<n>` adds a scenario swarm and a decision-log audit (`report/milestone-level4.md`); `/design` runs an arena for contested designs (`design/arena.md`); `/autopilot` cuts the next milestone inside its branch.

- New Level 2 skill `design` (D47): scenarios first, then interfaces, data flow, notifications and state owners; tickets are cut from the scenarios, and `/report M<n>` checks each one. `/verify` drives the real app when the project has a verification skill.

- Adapted from pstack (D46): `/plan` sharpens the brief and explores how and why first (`plan/sharpen.md`); PRs carry an append-only decision log, failures included; `/verify` checks blast radius and reads the decision log; `/retro` follows the correct ladder (architecture, types/lint/CI, tests, docs) and keeps only lessons that hold for six months; `/report` draws on decision logs.

- Milestone branches (D44): `/plan` creates `milestone/M<n>` once a cut is approved; `/build` branches from it and targets it; `/autopilot` merges ticket PRs only into it, opens the milestone PR into `main` and stops for the Owner's sign-off, then starts the next cut. `/verify` posts the verdict as a comment from the machine account.

- `/autopilot` claims a ticket by pushing its branch before starting a builder.

- `/verify` posts the verdict as a review from the verifier account when agent-merge is on.

- New Level 3 skill `autopilot`: runs the active milestone in stateless ticks, dispatching fresh builder and verifier sessions, merging when the harness allows, stopping at Owner gates and a budget. `wake.md` lists how to wake it (PR events, `/loop`, a schedule, a GitHub Action).

- Milestones (`plan/milestones.md`, `milestone-template.md`): `/plan --roadmap` writes `docs/milestones/M<n>.md`; `/plan M<n>` cuts the active one into tickets; `/report M<n>` checks its exit criteria for the Owner's sign-off. Tickets carry `Milestone: M<n>`.

- Tickets have three modes (`plan/tickets.md`): `docs/tickets/T-<nnn>.md` files with an issue mirror (recommended), files only, issues only. File tickets carry `Status: open`; `/build`'s PR sets it to `done`.

- `setup`, `plan`, `build`, `verify`, `report`, `handoff`, `retro`, `autopilot`, `tdd`, `evidence`, `ask-owner` and `learning`.

### Templates

- Hooks look inside `sh -c` and `eval`; `ask_on_merge.py` reads only the Autonomy value and also catches `gh -R ... pr merge`, GraphQL merge and auto-merge mutations and auto-merge tools; `no_push_main.py` handles `--repo`; `ask_on_rule_files.py` covers all of `.github/` and inline scripts that name a rule file. `settings.json` also denies nested `.env` files.

- New hook `ask_on_merge.py` asks before an agent merges a PR unless the harness file lets agents merge. `AGENTS.md` says so under "Never".


- Workflows use `actions/checkout@v6` and `actions/setup-python@v7` (Node 24).
- Level 1: `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, three hooks (`no_push_main`, `no_destructive`, `ask_on_rule_files`), `.github/workflows/tests.yml`, `docs/decisions.md`, and the memory files `docs/agents/glossary.md`, `learnings.md` and `architecture.md`.

- Clarified from the W6 trial: hand-off notes state whether the working copy is clean and list every check that must pass; mutation evidence when a condition can't go red; mutation hygiene (no bytecode caches, clean `git status`); the verifier's checklist for behaviour-pinning tickets and reverted out-of-scope commits.
- `install_templates.py --skip PATH` leaves out a template the project already covers.

### Docs

- New concept pages (D49): `access.md` (who reads and writes what, the control and data planes, which crossings matter, what is enforced and what is prose), `states.md` (ticket, milestone, verdict and autopilot state machines and where each state lives) and `layout.md` (a full project's files and branches).
- `docs/levels.md`: every skill, template and recipe, listed by the level it belongs to, with what each requires and works better with. Generated from `docs/components.json`.
- `retro` and `handoff` are part of Level 1 (they were listed under Level 3 in `suggestion.md`).
- `docs/components.json`: every component with its level, `requires`, `recommends` and project `needs`; it generates `levels.md`.
- Levels 0-4 form one spectrum from close control (like Matt Pocock's skills) to the most agent authority (like pstack); `levels.md` opens with who holds authority at each level. There is no custom selection.
- `templates/docs/agents/README.md` explains why `harness.md` is filled in by `/setup` rather than copied. Template `README.md` files are never copied.

### Recipes

- `docs/adr/**` is read-only by default, plan PRs may add `docs/adr/*.md`, and the agent-merge CODEOWNERS file owns `/docs/adr/` (D49).
- `second-model-review` becomes a swappable adapter: a different Claude model, Cursor CLI, Cursor Bugbot or a Grok action. New Level 4 recipe `deep-verification`.

- New Level 2 recipe `verify-app`: a project skill that drives the real app, with templates for the skill and its feature map.

- `protect-main` adds a `protect-milestones` ruleset for `milestone/*`. `agent-merge` gates merges into milestone branches; it reads verdict comments from the machine account (edited ones don't count, any FAIL on the head is final) and refuses plan and milestone PRs. New `multi-account` recipe holds CODEOWNERS for repositories with several agent accounts.

- `append-only` accepts lines only after the last existing one. `serial-resources` maps resources to paths and fails undeclared changes. `protect-main` requires up-to-date branches (or a merge queue) from Level 2. `progress-file` runs on every PR, keeps its files in `docs/progress/`, and lets Owner accounts change requirements.

- Every workflow runs the base branch's copy of its check. `no-weakened-tests` and `done-when` run the PR's tests in a separate job; an empty base report fails. `agent-merge` reads the verdict from the verifier account's pull request review on the current head, runs with `pull_request_target`, and refuses plan PRs and a verifier equal to `MACHINE_ACCOUNT`. Token permissions and the required-check source are spelled out.

- The shared "Find the ticket" step: every account in `MACHINE_ACCOUNT` (comma separated, any case) must use an open ticket, and it fails closed when the variable is unset; milestone PRs (`milestone/*`) are left to the Owner; file tickets never fall back to issues; done tickets, closed issues and tickets another open PR works on can't be claimed. New `multi-account` recipe: CODEOWNERS and code-owner review, only for repositories with more than one agent account.

- Workflows pass step outputs to scripts through `env:`, never inline, so a branch or file name can't inject shell code.

- `docs/milestones/**` is read-only for ticket PRs; plan PRs may change `docs/milestones/*.md`.

- `protect-main` requires 1 approval, dismissed on new pushes; `agent-merge` lowers it to 0 because the `verdict` status replaces it.

- Plan PRs (`plan/<slug>` branches) skip the ticket checks and may change only ticket and planning files; anything else fails the shared "Find the ticket" step.

- `scope` and `read-only-paths` take `--ticket-path`; a PR may change only its own ticket file's `Status:` line. `docs/tickets/**` is read-only by default. The shared "Find the ticket" step outputs `ticket_path`.

- Adding a guardrail is rule work: the Owner opens it, or it's a ticket listing the exact files.
- Every workflow uses `actions/checkout@v6` and `actions/setup-python@v7`.
- Level 1: `protect-main`.
- Level 2: `machine-account`, `commit-author`, `scope`, `read-only-paths`, `no-weakened-tests`, `done-when`, `append-only`, `serial-resources`, `evidence`, each check with a copyable script and workflow.
- Level 3: `progress-file` (start-up routine and a feature list where agents may only flip "passes"), `agent-merge` (a `verdict` status tied to the current head commit), `second-model-review`, `project-evals`.
