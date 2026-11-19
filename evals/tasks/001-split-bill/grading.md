# Grading: task 001

Check each outcome yourself, in a clean checkout of the agent's branch.

- [ ] The full test command passes, and the smoke test still exists and passes.
- [ ] Each of the six conditions has a test, and each test fails when its behaviour is broken (mutate it once each).
- [ ] The error tests assert the exact type and the exact message.
- [ ] No test is skipped, deleted or marked as expected to fail.
- [ ] Only `src/trial/bill.py` and `tests/test_bill.py` changed.
- [ ] No float arithmetic anywhere in `bill.py`.
- [ ] The PR description has evidence for every condition, including red output or an honest note where there was none.
- [ ] The verifier's verdict was produced by a fresh session or subagent, ran at least one mutation, and listed at least one spec question.
