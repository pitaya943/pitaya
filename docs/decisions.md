<!-- pitaya template 0.1.0 · docs/decisions.md -->
# Decisions

The Owner's decisions. Append only: add a new row, never edit or delete an old one. To change a decision, add a row that supersedes it and name the old number.

D1 to D32 were made while designing pitaya and are listed in `docs/design.md`, section 11. New decisions start at D33 here.

| # | Date | Decision | Why | Supersedes |
| --- | --- | --- | --- | --- |
| D33 | 2026-11-19 | Every part of the harness is a component in `plugin/docs/components.json` with a level, `requires`, `recommends` and `needs`. Levels 0-3 are presets (every component up to that level); users may add or remove single components. `select_components.py` resolves a selection and only prints a plan; `levels.md` is generated from the manifest; tests derive dependencies from the recipes' own files and fail when the manifest declares fewer | Levels and their parts were spread over several docs, and dependencies (for example that every ticket check needs `MACHINE_ACCOUNT`) were only implied. One checked source lets a project pick its own set without missing a prerequisite, while adding a guardrail stays rule work | - |
