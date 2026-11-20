<!-- pitaya template 0.1.3 · docs/agents/architecture.md -->
# Architecture

A map of the codebase, for orientation before changing it: the main modules, where they live and what each is for. Keep it short; the code is the detail.

`/setup` drafts it from the repository and the Owner corrects it. `/plan` updates it when a plan adds, removes or moves a module.

| Module | Path | Purpose |
| --- | --- | --- |
| plugin | `plugin/` | Everything that ships, and nothing else (D32). The marketplace installs this folder alone |
| skills | `plugin/skills/<name>/` | The thirteen skills; `setup/scripts/install_templates.py` copies the templates |
| templates | `plugin/templates/` | The Level 1 files `/setup` copies into a project, each with a version header |
| recipes | `plugin/docs/guardrails/` | Level 1-3 recipes; standalone checks and workflows under `files/<recipe>/` |
| components | `plugin/docs/components.json` | Every part of the harness with its level and dependencies (D33); `levels.md` is generated from it by `scripts/render_levels.py` and tests check its dependencies against the recipes |
| user docs | `plugin/docs/levels.md`, `plugin/docs/suggestion.md`, `plugin/docs/concepts/` | What each level includes; what each part achieves; roles, autonomy, escalation, access, states and layout |
| design | `docs/design.md` | The design, decisions D1-D32 and the W-step plan; later decisions in `docs/decisions.md` |
| memory | `docs/agents/`, `docs/decisions.md` | This repository's own harness config and memory (D31) |
| checker | `scripts/check_skills.py` | Follows the marketplace source to the plugin; checks manifests and every `SKILL.md` |
| tests | `tests/` | One folder per area: plugin, templates (hooks, install), guardrails; plus docs, layout, English, personal data |
| evals | `evals/` | Tasks that measure the harness itself, run by hand before and after a change |

## How the parts connect

A user installs `plugin/`; `/pitaya:setup` runs `install_templates.py`, which copies `plugin/templates/` into their project. Skills reach the recipes and the suggestion doc by paths relative to themselves (`../../docs/...`), so the structure inside `plugin/` must not change without updating them. Tests reach everything through `REPO_ROOT` and `PLUGIN_ROOT`.
