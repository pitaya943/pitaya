# Recipe: done-when

Level: 2. Files: [`check_done_when.py`](files/done-when/check_done_when.py), [`done-when.yml`](files/done-when/done-when.yml).

## What it guards against

A ticket called done while one of its completion conditions has no test, or a test that never ran. Green CI only says the existing tests pass, not that the ticket's conditions are covered.

## When it's worth adding

With [no-weakened-tests](no-weakened-tests.md), once tickets are planned with `/plan` and verified by a fresh verifier, so their conditions are precise enough to name tests.

## How to add it

1. Add a "## Test IDs" section to tickets: one `classname::name` per done-when condition, in order. `/plan` writes it when this guardrail is listed in the harness file.
2. Copy `files/done-when/check_done_when.py` to `.github/guardrails/check_done_when.py`.
3. Copy `files/done-when/done-when.yml` to `.github/workflows/done-when.yml`, and set `TEST_COMMAND` so it writes JUnit XML.
4. After the first run, make `done-when` a required check.

## How to prove it works

Open a PR for a ticket whose "## Test IDs" lists a test that doesn't exist yet. The check fails and names it. Write the test under exactly that ID, and the check passes.

## Cost and false positives

- One test run per PR; it shares the JUnit setup with no-weakened-tests.
- Test IDs have to be decided while planning, which takes a little more care.
- A test renamed during the work fails the check until the ticket's ID is updated.
- It confirms each named test passes, not that the test means what the condition says. The verifier's "tests are real" check covers that.

## Error message

```text
FAIL done-when: these done-when tests don't pass:
  tests.test_bill::test_rounding: missing
To fix: write or fix the test for each condition so it runs and passes under exactly this ID, or ask the Owner to correct the ID in the ticket.
```

## Afterwards

Add `done-when` under "Guardrails" in the harness file. "Test IDs" is now a required ticket field.

## When to remove it

When the verifier's checklist reliably catches untested conditions, and keeping test IDs in tickets costs more than it saves.
