# Recipe: done-when

Level: 2. Files: [`check_done_when.py`](files/done-when/check_done_when.py), [`done-when.yml`](files/done-when/done-when.yml).

## What it guards against

A ticket called done while one of its completion conditions has no test, or a test that never ran. Green CI only says the existing tests pass, not that the ticket's conditions are covered.

## When it's worth adding

With [no-weakened-tests](no-weakened-tests.md), once tickets are planned with `/plan` and verified by a fresh verifier, so their conditions are precise enough to name tests.

## How to add it

Set the repository variable `MACHINE_ACCOUNT` to the agents' login first, if it isn't set yet: the workflow uses it to tell agent PRs from the Owner's ([details](README.md#how-the-checks-find-the-ticket)).

1. Add a "## Test IDs" section to tickets: one test ID per done-when condition, in order: `classname::name` as JUnit reports it, or a pytest path such as `tests/test_cli.py::test_x`. An ID without parameters covers all of a parametrized test's cases. `/plan` writes it when this guardrail is listed in the harness file.
2. Copy `files/done-when/check_done_when.py` to `.github/guardrails/check_done_when.py`.
3. Copy `files/done-when/done-when.yml` to `.github/workflows/done-when.yml`, and add your runtime setup steps to the `head-tests` job. That job runs `sh .github/scripts/test.sh` with `JUNIT` set, the script `/setup` installed as the one place the test command is written: make the command there write JUnit XML to `"$JUNIT"` when it is set (for pytest, `python -m pytest -q ${JUNIT:+--junitxml="$JUNIT"}`). The PR's tests run in that job alone; the check runs in another job, with the base branch's copy of the script.
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
