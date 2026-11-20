<!-- pitaya template 0.1.6 · docs/guardrails/files/progress-file/progress.md -->
# Progress

Updated by every session before it ends; read by every session before it starts. Newest entry first. Link, don't paste.

## Start-up routine

1. `pwd`, then read this file and `git log --oneline -20`.
2. Run the test command from `docs/agents/harness.md`, and note the result.
3. If anything that passed before now fails, fix that first.
4. Pick the next feature in `docs/progress/features.json` with `"passes": false`. Work on that one feature only.

## Log

### <date> · <session or branch>

- Did: <what changed, with commit links>
- Tests: `<command>` gives `<summary line>`
- Features now passing: <ids>
- Next: <the exact next step>
- Watch out: <anything the next session should know>
