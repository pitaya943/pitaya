---
name: setup
description: Configure this repo for the pitaya skills. Explore it, ask a few questions, install the Level 1 defaults (AGENTS.md, permissions, hooks, a tests workflow) without overwriting anything, and write docs/agents/harness.md, the file every other skill reads first. Run once per repo, and again to update stale copies.
disable-model-invocation: true
---

# Setup

Install the defaults for the chosen level and write `docs/agents/harness.md`, the short config every pitaya skill reads first. There is no gate: other skills work without it, using safe defaults, so keep this quick. Re-running is safe; it reports stale copies instead of overwriting them.

## 1. Explore before asking

Read what exists. Don't assume.

- `git remote -v`: is this a GitHub repo, and which one?
- `docs/agents/harness.md`: if it exists, you're updating it. Show the current values and ask only about what changes.
- The test command: look at `package.json` scripts, `pyproject.toml`, `pytest.ini`, `Makefile`, `go.mod`, `Cargo.toml` and CI workflows. Run the best candidate once, exactly as you'll record it, and note whether it passes.
- `docs/tickets/` or issues labelled `ticket`: where does planned work already live?
- `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, `.github/workflows/`: what the project already has that the install must not overwrite.
- Who you are on GitHub: `gh api user --jq .login`, or the GitHub tool's "get me" call. Don't guess.
- Where the agents run. In Claude Code cloud sessions the plugin comes from the environment's setup script, not from `/plugin` (the plugin's `README.md`, "Cloud sessions"); everything this skill installs is committed to the repository, so it works there too.
- If the skills were copied into `.claude/skills/`, run `git check-ignore -v .claude/skills/*/SKILL.md`. A broad rule such as `build/` hides the `build` skill from git; anchor it (`/build/`) and tell the user.

## 2. Ask, one question at a time

Lead each question with your recommendation, so the user can accept it in a word. Skip any question that exploring already settled.

1. **Owner and machine account.** Who merges `main`? Which separate machine account do the agents act as? Recommend one in every project: without it a session acts as the account it is signed in with, usually the Owner's, and holds the Owner's bypass of the rulesets. It is required before agents act unattended (`/autopilot`, a schedule, another session starting them, permission prompts off) and from Level 2 (the plugin's `docs/concepts/autonomy.md`, "Unattended work needs a machine account"). "None" is an answer only while a person watches every step: then write "none" and what it means into the harness file, and say in your output that merge protection is the hooks alone. If the account you are signed in as (step 1) is the Owner's, say so now.
2. **Where tickets live.** Recommend `docs/tickets/T-<nnn>.md` files mirrored by issues labelled `ticket`: the file is the source of truth (checks read it from the base branch, so a PR can't edit its own ticket), and the issue gives discussion and notifications. Alternatives: files only, or issues only (lightest; an issue body can be edited by anyone with write access).
3. **Test command.** Confirm one that actually runs here, as typed: if the test tool lives in a virtualenv, use that path (for example `.venv/bin/python -m pytest -q`). Otherwise ask for it. The install writes it into `.github/scripts/test.sh`, the one place it lives; everything else runs `sh .github/scripts/test.sh`. If nothing runs yet, pass `false` as the command, so the script fails until someone fills it in, and say that `/build` needs one.
4. **Language, records and sensitive areas.** Which language documents are written in (PRs, issues, reports); whether to keep `docs/decisions.md` (recommended); which areas need a covering test before anyone changes them (money, permissions, migrations). "None" is fine.

If an answer contradicts something you found (an account that doesn't exist, a failing test command), say what you found and ask again. Never fill in an answer yourself.

## 3. Install and write

1. **Level.** Recommend Level 1 (the default) unless the user only wants the skills (Level 0). With no machine account, don't record Level 2 or higher and leave "Autopilot" off: say that both wait for the account, and stay at Level 1. If the harness file already records either with no account, say so, ask which one changes, and change nothing else until the Owner answers. The plugin's `docs/levels.md` (`../../docs/levels.md` from this file) lists every component by level; `docs/suggestion.md` says what each achieves. The levels are a spectrum from close control (Level 0, like Matt Pocock's skills) to the most agent authority (Level 4, like pstack): ask how much control the Owner wants to keep.
2. **Preview, then install.** From the repo root, run [scripts/install_templates.py](scripts/install_templates.py) with `--level`, `--test-command "<the confirmed command>"`, `--no-decisions` if the user declined the decision log, `--skip <path>` for any template the project already covers (such as the tests workflow when CI exists), and `--check`. Show the user the output, then run it again without `--check`.
   - `created` and `merged` are done. `merged` means `.claude/settings.json` gained rules and hooks; nothing of theirs was removed.
   - `withdrawn` names an allow rule in `.claude/settings.json` that an earlier version installed and this one no longer does, with the reason. The install only adds rules: show the line and let the user delete the rule.
   - `differs` and `stale` files were left alone. Show the diff against `../../templates/<path>` (relative to this file) and let the user choose. Never overwrite one yourself. A `.github/scripts/test.sh` that differs is the project's own command: to change the command, edit that script, and nothing else.
   - If `AGENTS.md` differs, add a short "Agent harness" section to theirs instead, pointing to `docs/agents/harness.md`.
3. **Harness file.** Copy [harness-template.md](harness-template.md) to `docs/agents/harness.md` and fill it in: the answers, the level (the selection label if you customized), and under "Guardrails" the parts that are now installed. Delete lines that don't apply rather than leaving placeholders.
4. **Memory.** From what you explored, draft `docs/agents/architecture.md` (the main modules, their paths, one line each) and seed `docs/agents/glossary.md` with the few terms the code and docs use most. Ask the Owner to correct both; leave `docs/agents/learnings.md` empty.
5. **CI.** Add to `.github/workflows/tests.yml` the setup steps the test command needs (a language runtime, installing dependencies), each action pinned by commit as the template's are. Run `sh .github/scripts/test.sh` once here. The first pull request must show the `tests` check passing; with no test command yet, it stays red until the script has one.
6. Show the user the diff. Then, never on `main`: create the branch `setup/pitaya` (on a re-run, when that name is taken or its PR has merged, `setup/update-<version>`), commit there with the message `Configure pitaya skills`, push, and open a PR into `main`, which the Owner merges (skip the PR only if the user says so). The rules this step just installed forbid work on `main`, and the hook blocks a push to it. In a session with an assigned branch, ask the user to allow the setup branch's name first: the grant in the new `AGENTS.md` isn't the Owner's until this PR is merged. In a repository with no remote there is nothing to open a PR on: keep the commit on the branch and say so. From Level 2 the ticket checks fail a setup PR that an agent account opened, on purpose, because it names no ticket: the Owner reads the diff and merges it through the bypass.

## 4. Hand the Owner the repo settings

The machine account can't change repo settings, so list these steps for the Owner, and check them afterwards where you can read them. With no machine account the session usually acts as the Owner and could change them: still don't, and say what that means: the ruleset's bypass is the agent's too, the hooks are the only thing before a merge, and agents must not act unattended until there is a machine account.

- A ruleset on `main`: require a pull request with 1 approval (dismissed on new pushes), block force pushes and deletions, require the `tests` check, and let only the Owner bypass. A machine account can't approve its own PR, so only the Owner merges `main`. With milestones, a second ruleset on `milestone/*`, with the same bypass and 1 approval below Level 3 (the plugin's `docs/guardrails/protect-main.md`).
- The machine account is a collaborator with Write, not Admin, and isn't on a bypass list (the plugin's `docs/guardrails/machine-account.md`). With "none", this is the step that is missing.

Then name the next steps: `/plan --roadmap` to cut the project into milestones (or `/plan` for a single small piece of work), and the next level up from the plugin's `docs/suggestion.md`, usually nothing until a second agent works in the repo (Level 2). With no machine account, name that first: it comes before any unattended session.

## Don't

- Don't write secrets, tokens or passwords anywhere. Name the secret, never its value.
- Don't change repo settings (rulesets, collaborators, secrets). Explain the steps; the Owner makes the change.
