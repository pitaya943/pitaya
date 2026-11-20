# Escalation

Agents stop and ask the Owner instead of guessing. The `ask-owner` skill has the procedure; this page explains when and why.

## When agents stop

- The spec or ticket is unclear, or contradicts itself.
- The work needs a change the ticket didn't authorize: a data model, a public interface, a dependency, a file outside its scope.
- The fix rounds are used up.
- A sensitive area would change with no test covering it.
- The next step can't be undone.

Work that doesn't depend on the answer carries on.

## Fix rounds

When the verifier says FAIL:

1. **Round 1:** the same Builder session fixes each listed problem.
2. **Round 2:** a fresh session fixes what's left, reading only the ticket, the diff and the verdicts. A fresh context avoids repeating the first session's blind spots.
3. **Still FAIL:** escalate to the Owner with the open problems and options.

The number of rounds is the `Fix rounds` field in the harness file (default 2). Two kinds of round alternate: a **verify round** checks and posts a verdict, a **fix round** changes code. With the default, the sequence is verify 1, fix 1, verify 2, fix 2, verify 3, escalate. A verdict says which verify round it is and the next step.

The Owner may answer an escalation by authorising an extra round. Only the Owner can: the answer on the escalation issue is the authorisation, and the extra round runs in a fresh session like round 2. Its verdict names the round and links the authorisation, so a reader can see why a ticket had more rounds than the harness allows.

## A good question

- Names the exact source: the spec section, ticket condition, file and line.
- Gives two or three options, each with what changes for users, what it touches and how costly it is to reverse.
- Recommends one, with the reason.
- Doesn't start implementing the recommendation before the answer.

The Owner's answer is recorded in `docs/decisions.md` when the project keeps one, so it isn't asked again.
