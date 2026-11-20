# Changelog

Changes are grouped by what users copy or install: skills, templates and recipes.

## Unreleased (0.1.0)

### Skills

- New Level 3 skill `autopilot`: runs the active milestone in stateless ticks, dispatching fresh builder and verifier sessions, merging when the harness allows, stopping at Owner gates and a budget. `wake.md` lists how to wake it (PR events, `/loop`, a schedule, a GitHub Action).

- Milestones (`plan/milestones.md`, `milestone-template.md`): `/plan --roadmap` writes `docs/milestones/M<n>.md`; `/plan M<n>` cuts the active one into tickets; `/report M<n>` checks its exit criteria for the Owner's sign-off. Tickets carry `Milestone: M<n>`.

- Tickets have three modes (`plan/tickets.md`): `docs/tickets/T-<nnn>.md` files with an issue mirror (recommended), files only, issues only. File tickets carry `Status: open`; `/build`'s PR sets it to `done`.

- `setup`, `plan`, `build`, `verify`, `report`, `handoff`, `retro`, `autopilot`, `tdd`, `evidence`, `ask-owner` and `learning`.

### Templates

- Hooks look inside `sh -c` and `eval`; `ask_on_merge.py` reads only the Autonomy value and also catches `gh -R ... pr merge`, GraphQL merge and auto-merge mutations and auto-merge tools; `no_push_main.py` handles `--repo`; `ask_on_rule_files.py` covers all of `.github/` and inline scripts that name a rule file. `settings.json` also denies nested `.env` files.

- New hook `ask_on_merge.py` asks before an agent merges a PR unless the harness file lets agents merge. `AGENTS.md` says so under "Never".

- `setup/scripts/select_components.py` resolves a custom selection (a level plus or minus components): adds what is required, refuses to drop what is still required, warns about missing recommendations, prints the steps in order and the `--skip` arguments for `install_templates.py`. It only prints a plan.

- Workflows use `actions/checkout@v6` and `actions/setup-python@v7` (Node 24).
- Level 1: `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, three hooks (`no_push_main`, `no_destructive`, `ask_on_rule_files`), `.github/workflows/tests.yml`, `docs/decisions.md`, and the memory files `docs/agents/glossary.md`, `learnings.md` and `architecture.md`.

- Clarified from the W6 trial: hand-off notes state whether the working copy is clean and list every check that must pass; mutation evidence when a condition can't go red; mutation hygiene (no bytecode caches, clean `git status`); the verifier's checklist for behaviour-pinning tickets and reverted out-of-scope commits.
- `install_templates.py --skip PATH` leaves out a template the project already covers.

### Docs

- `docs/levels.md`: every skill, template and recipe, listed by the level it belongs to, with what each requires and works better with. Generated from `docs/components.json`.
- `retro` and `handoff` are part of Level 1 (they were listed under Level 3 in `suggestion.md`).
- `docs/components.json`: every component with its level, `requires`, `recommends` and project `needs`. Levels are presets you can add to or remove from.
- `templates/docs/agents/README.md` explains why `harness.md` is filled in by `/setup` rather than copied. Template `README.md` files are never copied.

### Recipes

- The shared "Find the ticket" step: only `OWNER_ACCOUNTS` may skip it (fail closed when unset); file tickets never fall back to issues; done tickets, closed issues and tickets another open PR works on can't be claimed. `commit-author` checks every non-Owner PR. `protect-main` and `agent-merge` ship `CODEOWNERS` files and require code-owner review.

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
