<!-- Verdict comment for /verify. Write it in the document language from docs/agents/harness.md. -->

## Verification: PASS | FAIL

- Model: <name and version from the session's configuration, or "unavailable: <reason>">
- Verify round: <n> of at most <the harness's "Fix rounds" + 1> (for a round beyond that, link the Owner's authorisation)
- Next step: <for PASS, "the Owner merges" or "agents merge"; for FAIL, "fix round <n> in the builder's session" or "fix round <n> in a fresh session" or "escalate to the Owner">
- Head commit: <sha>
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

## Spec questions

<!-- Behaviour the spec doesn't decide. "None" if none. -->

## Learning proposals

<!-- Something the next agent should know, for docs/agents/learnings.md. "None" if none. -->
