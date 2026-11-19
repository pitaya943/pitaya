# AGENTS.md

Rules for agents developing this repository (the pitaya plugin itself).

## Commands

- Tests: `python3 -m pytest tests -q` (needs `pytest`; no network access).
- Skill check: `python3 scripts/check_skills.py`.
- Personal-data scan: `python3 tests/pii_scan.py`, and `--commits <base>..HEAD` before pushing.

## Rules

- Every file is written in English (`tests/test_english.py`).
- No personal data in any file, commit message or PR text: no real names, accounts or emails. Use `example-owner` and `example-bot`. The plugin's name, `pitaya`, is the one deliberate exception.
- Write the failing test first. Never skip, delete or loosen a test to get green.
- Work on a branch and open a pull request; only the Owner merges `main`.
- Commit as the machine account: its login as the name and its GitHub noreply address as the email (D29). Commit messages are in English.
- Each `SKILL.md` is at most 80 lines; put details in sibling files.
- Skill files, templates and recipes ship to users: keep them free of anything specific to this repository.

## Where things are

- `docs/design.md`: the design, decisions and plan.
- `docs/suggestion.md`: what each level should have, for users.
- `skills/`, `templates/`, `.claude-plugin/`: what ships.
