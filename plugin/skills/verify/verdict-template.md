<!-- Verdict comment for /verify. Write it in the document language from docs/agents/harness.md. Post it from the heading down, without this line: the comment must start with "## Verification:". -->

## Verification: PASS | FAIL

- Model: <name and version from the session's configuration, or "unavailable: <reason>">
- Verify round: <n> of at most <the harness's "Fix rounds" + 1> (for a round beyond that, link the Owner's authorisation)
- Next step: <for PASS, "the Owner merges" or "agents merge"; for FAIL, "fix round <n> in a fresh session" (every round under `/autopilot`, which is when the harness's "Autopilot" line is on; elsewhere every round after the first), "fix round 1 in the builder's session" (only when a person runs the work), or "escalate to the Owner" (FAIL number "Fix rounds" + 1)>
- Head commit: <the full 40-character sha>
- Session: <this session's ID, or "unavailable: <reason>" (with agent-merge, a PASS without a real ID doesn't count)>
- Ticket: <link or path>

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Clean re-run | pass / fail | <command, summary line> |
| 2 | Completion conditions | | |
| 3 | Tests not weakened | | |
| 4 | Tests are real | | |
| 5 | Mutation spot-check | | |
| 6 | Error paths | | |
| 7 | Bad input | | |
| 8 | Spec edge cases | | |
| 9 | Scope | | |
| 10 | Blast radius | | <the one fact, and the command that proves it; or "small diff"> |
| 11 | Real app | | <feature, evidence path; or "not user-facing"> |
| 12 | Interrogate | | <findings and dropped; or "not required"> |
| 13 | Decision log | | |
| 14 | Evidence and hygiene | | |

## Problems

<!-- FAIL only. For each problem: where (file:line), how to reproduce, what was expected, what happened. No fix code. -->

## Attention

<!-- On PASS and FAIL alike. One row for each thing the Owner should see at sign-off, classified by what the diff and the PR show, never by intent; "None" if there are none. Kinds: `gate-change` (the PR loosens, disables, skips or soft-fails a test, check, hook, workflow, read-only path or ruleset; required even when justified), `role` (work outside the session's role, such as verifying its own build or editing a verdict), `unproven-claim` ("done", "passes" or "verified" with no evidence), `undisclosed` (a change or pivot the decision log should show and doesn't). "Disclosed" is yes when the PR description or its decision log says so. -->

| Kind | Where | Disclosed | Evidence |
| --- | --- | --- | --- |
| <kind> | <file:line, commit or comment> | yes / no | <the diff line, command and output, or link> |

## Spec questions

<!-- Behaviour the spec doesn't decide. "None" if none. -->

## Learning proposals

<!-- Something the next agent should know, for docs/agents/learnings.md. "None" if none. -->
