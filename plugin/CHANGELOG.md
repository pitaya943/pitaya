# Changelog

Changes are grouped by what users copy or install: skills, templates and recipes.

## Unreleased (0.1.0)

### Skills

- Tickets have three modes (`plan/tickets.md`): `docs/tickets/T-<nnn>.md` files with an issue mirror (recommended), files only, issues only. File tickets carry `Status: open`; `/build`'s PR sets it to `done`.

- `setup`, `plan`, `build`, `verify`, `report`, `handoff`, `retro`, `tdd`, `evidence`, `ask-owner` and `learning`.

### Templates

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

- Plan PRs (`plan/<slug>` branches) skip the ticket checks and may change only ticket and planning files; anything else fails the shared "Find the ticket" step.

- `scope` and `read-only-paths` take `--ticket-path`; a PR may change only its own ticket file's `Status:` line. `docs/tickets/**` is read-only by default. The shared "Find the ticket" step outputs `ticket_path`.

- Adding a guardrail is rule work: the Owner opens it, or it's a ticket listing the exact files.
- Every workflow uses `actions/checkout@v6` and `actions/setup-python@v7`.
- Level 1: `protect-main`.
- Level 2: `machine-account`, `commit-author`, `scope`, `read-only-paths`, `no-weakened-tests`, `done-when`, `append-only`, `serial-resources`, `evidence`, each check with a copyable script and workflow.
- Level 3: `progress-file` (start-up routine and a feature list where agents may only flip "passes"), `agent-merge` (a `verdict` status tied to the current head commit), `second-model-review`, `project-evals`.
