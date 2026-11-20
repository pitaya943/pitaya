<!-- pitaya template 0.1.9 · docs/agents/learnings.md -->
# Learnings

What the next agent should know before starting: things that cost time, surprised someone, or went wrong more than once. Read it before planning or building.

Append only: add a row, never edit or delete one; mark an outdated row as superseded in a new row. `/retro` adds the rows the Owner accepts. Verdicts and hand-off notes propose them.

| # | Date | Learning | Source | Supersedes |
| --- | --- | --- | --- | --- |
| 1 | 2026-11-19 | A broad `build/` rule in `.gitignore` also hides `.claude/skills/build/`. Anchor build-output rules to the root (`/build/`) | first trial run; `/setup` now checks with `git check-ignore` | |
| 2 | 2026-11-19 | The personal-data scan reads its own source and the tests. Build address or mention shapes at runtime (`"@" + "..."`) instead of writing them literally | `tests/pii_scan.py` | |
| 3 | 2026-11-19 | A new module's first red is an import error unless you add a stub first; and a condition already met by earlier work can't go red. Say so in the PR and let the verifier back it with a mutation | first trial's verdict (fixes F1, F2) | |
| 4 | 2026-11-19 | A ruleset with no target branches protects nothing. Check `gh api repos/<owner>/<repo>/rules/branches/main` lists rules after setting one up | trial repository, twice | |
| 5 | 2026-11-19 | In a workspace Claude Code hasn't been trusted in, `permissions.allow` from `.claude/settings.json` is ignored, but hooks still run | W6 hook test with `claude -p` | |
| 6 | 2026-11-19 | Running a child `claude -p` with `--dangerously-skip-permissions` is refused by the session's safety classifier. Test hooks with `--allowedTools` limited to the exact commands, in an isolated copy with a local fake remote | W6 hook test | |
| 7 | 2026-11-19 | A clone that fetched only `main` has no remote-tracking ref for a new branch, so tools report it as unpushed. Add the branch to `remote.origin.fetch` and set its upstream after pushing | repeated stop-hook warnings | |
| 8 | 2026-11-19 | Installing pitaya on a project that already has CI creates a second tests workflow. Pass `--skip .github/workflows/tests.yml` | W6, installing pitaya on itself | |
| 9 | 2026-11-19 | GitHub warns that `actions/checkout@v4` and `actions/setup-python@v5` run on the deprecated Node 20. Use v6 and v7 (Node 24); `tests/test_action_versions.py` pins the minimum | W6, trial repository's Actions logs | |
| 10 | 2026-11-19 | After a mutation test, a restored file of the same size written in the same second keeps Python's stale bytecode: the next session saw 3 failures in correct code. Mutate with `PYTHONDONTWRITEBYTECODE=1` and check `git status` afterwards | W6, the hand-off session's first test run | |
| 11 | 2026-11-19 | A machine-account PR that installs a ticket-based guardrail from a non-ticket branch fails that guardrail's own check. Make the install a ticket that lists the exact files | W6, adding the scope recipe to the trial repository | |
