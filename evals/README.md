# Evals for pitaya itself

Tasks that measure whether the harness makes agents work better. Run them **before and after** changing a skill, a template, a hook or the recommended model, and compare. This is the project-evals recipe applied to pitaya (decision D17).

## A task

Each task lives in `tasks/<nnn>-<name>/`:

- `task.md`: where it comes from, the starting state, and the exact prompt.
- `ticket.md`: the ticket the agent works on.
- `grading.md`: outcomes to check, as a checklist. Tests and scripts come before judgement.
- `starter/`: the repository the task starts from, when it's small enough to keep here.

## Running one

1. Copy `starter/` into a fresh directory, `git init` it, and install the pitaya plugin at the version under test.
2. Run `/pitaya:setup` with the answers in `task.md`, then give the agent the prompt exactly as written.
3. Grade with `grading.md` without reading the transcript first.
4. Then read the transcript, above all when the result changed since the last run. The score says whether something changed; the transcript says why.
5. Add a row to `results.md`.

Run each task in a clean checkout, and rerun a task before trusting a single changed result.
