# Recipe: no weakened tests

Level: 2. Files: [`compare_junit.py`](files/no-weakened-tests/compare_junit.py), [`no-weakened-tests.yml`](files/no-weakened-tests/no-weakened-tests.yml).

## What it guards against

The quietest way to get a green build: deleting a failing test, renaming it out of the way, or marking it skipped. CI stays green because the remaining tests pass.

## When it's worth adding

As soon as agents fix failing builds without a person reading every diff, or the first time a test disappears.

## How to add it

1. Make the test command write JUnit XML. Most tools can: pytest `--junitxml`, Jest `jest-junit`, Go `go-junit-report`, JUnit natively, cargo-nextest `--profile ci`.
2. Copy `files/no-weakened-tests/compare_junit.py` to `.github/guardrails/compare_junit.py`.
3. Copy `files/no-weakened-tests/no-weakened-tests.yml` to `.github/workflows/no-weakened-tests.yml`. Set `TEST_COMMAND`, and add your runtime setup steps.
4. After the first run, make `no-weakened-tests` a required check.

The workflow runs the tests twice: once on the base commit, with the base's own setup, and once on the PR. Then it compares results by test ID (`classname::name`). It judges results, not code, so it works for any language.

When a rename is really needed, the Owner adds it to the ticket:

```markdown
## Test renames

- `tests.test_bill::test_old_name -> tests.test_bill::test_new_name`
```

## How to prove it works

In a PR, delete one passing test, or mark it skipped. The check fails and names it. Restore it, and the check passes.

## Cost and false positives

- It runs the suite twice per PR, so CI time roughly doubles for this job.
- A legitimate rename fails until the Owner records it in "## Test renames".
- A flaky test that happened to pass on the base and fail on the PR fails the check: fix the flakiness rather than re-running until green.
- It can't catch a loosened assertion in a test that still passes. The verifier's mutation checks cover that.

## Error message

```text
FAIL no-weakened-tests: tests that passed before don't pass now:
  tests.test_bill::test_rounding: passed on the base, missing on the PR
To fix: restore or fix these tests; don't delete, skip or loosen them. If a rename is really needed, ask the Owner to add "old_id -> new_id" to the ticket's "## Test renames" section.
```

## Afterwards

Add `no-weakened-tests` under "Guardrails" in the harness file. The test command there must now write JUnit XML (Level 2).

## When to remove it

When the suite runs under mutation testing or coverage gates that would catch the same weakening, and transcripts show agents no longer try it.
