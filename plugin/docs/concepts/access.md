# Access: who reads and writes what

Every role works on one repository, so this page says which files each role should read, which it may change, and how much of that is **enforced** by a check and how much is only written down. A read or write the matrix doesn't allow is a crossing; [Crossing the line](#crossing-the-line) lists the ones that matter.

## Two layers

A project that uses pitaya has two layers, like a network's control plane and data plane:

- The **control plane** is the harness: the rules, the plan and the record. `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.github/`, `docs/agents/`, `docs/decisions.md`, `docs/adr/`, `docs/milestones/` and `docs/tickets/`. It decides what work happens and how it is judged.
- The **data plane** is the product: the source code, its tests, and the evidence and notes that work leaves behind.

A ticket PR changes only the data plane, and only inside its ticket's scope. The control plane changes in two ways: the Owner edits it, or a plan PR changes the plan files listed in the plan skill's `tickets.md`, which only the Owner can merge into `main` (at Level 4 the Chief also merges the next cut into its milestone branch). The [`read-only-paths`](../guardrails/read-only-paths.md) and [`scope`](../guardrails/scope.md) checks enforce this in CI, and the `ask_on_rule_files` hook asks a person before a session edits a rule file.

## The matrix

**R** read it before working, **W** may change it, **·** no need to read it, **✗** must not read it. The Adversary is a second-model or worktree agent that interrogates a high-risk PR at Level 4.

| Path | Owner | Chief | Builder | Verifier | Adversary | Enforced by |
| --- | --- | --- | --- | --- | --- | --- |
| `AGENTS.md`, `CLAUDE.md` | W | R | R | R | · | read-only check; rule-file hook |
| `.claude/`, `.github/` | W | R | R | R (its `verify-*` skill) | · | read-only check; rule-file hook |
| `docs/agents/harness.md` | W | R | R | R | · | read-only check; rule-file hook |
| `docs/agents/` (glossary, architecture, learnings) | W | W through a plan PR or `/retro` | R, the parts the ticket touches; proposes changes in the PR | · | · | read-only check |
| `docs/decisions.md`, `docs/adr/` | W | W, recording the Owner's decisions | · | · | · | read-only and append-only checks |
| `docs/milestones/` (milestones and designs) | W | W through a plan PR | R, the design | R, the scenarios are the spec | R, the scenarios | read-only check; plan PR allowlist |
| `docs/tickets/` | W | W through a plan PR | R its own ticket; W its `Status:` line only | R | R | read-only check, with the `Status:` exception |
| `docs/progress/` | W | R | R; W its log and only `"passes": true` | R | · | progress-file check |
| `docs/handoff/` | R | R | W | ✗ | ✗ | prose only; fresh context |
| `docs/evidence/` | R | R | W | W under `verify/` | · | evidence check |
| `docs/reports/`, `docs/learning.md` | R | W | · | · | · | prose only |
| Product code and tests in the ticket's scope | W | ✗ writes | W | R, in a clean checkout | R, in its own worktree | scope check |
| PR description and decision log | R | R | W | R, as claims, never as evidence | ✗ | prose only |
| The Builder's conversation | R | R | W | ✗ | ✗ | prose only; a fresh session can't see it |
| `.env`, keys and credentials | R | ✗ | ✗ | ✗ | ✗ | Read tool deny rules in `.claude/settings.json` |

`tests/plugin/test_architecture_docs.py` fails when a skill names a repository path this matrix doesn't cover, so the matrix grows with the skills.

## What is enforced, and what is prose

- **Writes are enforced.** CI fails a ticket PR that changes files outside its scope or a read-only path, and the hooks stop or ask before the usual dangerous commands. A write a check misses still has to get past the verifier and the merge gate.
- **Reads are mostly prose.** Claude Code's permissions apply to a whole project, not to one role, so a check can't stop only the verifier from reading a file. Secrets are the exception: the Read tool is denied on them, though a shell command can still reach them, which is why credentials belong outside the repository.
- **Isolation does the rest, mostly.** The verifier and the adversaries start fresh and work in their own checkout or worktree, so the Builder's conversation isn't there to read. Keep it that way: never paste a builder's transcript into a verifier's prompt. One gap: hand-off notes committed as `docs/handoff/<branch>.md` travel with the branch into the verifier's checkout. `/handoff` writes that file only as a last resort and removes it before review, and the verifier's checklist says not to open it, but that is prose, not a check.

## Crossing the line

These reads and writes break a guarantee even when no check catches them:

| Crossing | Why it matters |
| --- | --- |
| The Verifier reads the Builder's conversation or `docs/handoff/`, or treats the PR description as evidence | The verdict is no longer independent: it grades the builder's story, not the code |
| An Adversary reads the PR description | The builder's framing steers what it looks for |
| The Chief writes product code | Nobody verifies the coordinator's own changes, and its context fills up |
| A Builder changes the spec, a ticket's conditions or `docs/agents/` | It moves the goalposts it is judged against |
| Any agent reads `.env` or credentials | Secrets end up in transcripts, logs or PRs |
| Any agent merges into `main` or approves its own plan | It removes the Owner's gate |

A Builder reading another ticket or unrelated code is not a crossing: reading is harmless there, and the scope check stops the write.

## Checking it

Write the matrix first, then check behaviour against it: a run that shows a read without a rule to compare it to can't say whether the read was wrong. A later eval can replay a milestone on a sample project and compare each role's tool calls in the transcripts against this table.
