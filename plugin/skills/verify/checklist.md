# Verifier checklist

You're the verifier. You can't see the builder's conversation, on purpose. Judge only from the ticket, the spec, the diff and what you run yourself. The PR description's claims are not evidence: redo anything you rely on. Don't open `docs/handoff/` even when the branch carries notes there: they are the builder's account, not the ticket.

Mark every item pass or fail, with evidence: the command and its output, or the file and line. No evidence means fail.

1. **Clean re-run.** In a clean checkout of the head commit, install what the project needs and run the full test command from `docs/agents/harness.md`. The result matches CI. If no CI runs the tests (a review bot isn't CI), say so: the clean re-run stands alone.
2. **Completion conditions.** Each condition in the ticket has a test, or a re-runnable command, that you ran and saw pass. The count matches the ticket.
3. **Tests weren't weakened.**
   - Run the suite on the base too, and compare: every test that passed on the base still exists and passes on the head. Check out the base by its commit SHA; a worktree can't check out a branch that's checked out elsewhere.
   - The diff adds no skip or expected-failure markers.
   - The diff deletes no test or parametrized case, and loosens no assertion.
4. **Tests are real.** Read each new or changed test: it calls the product code through its public interface, and it checks the result. A test that would pass with the feature removed fails this item. For a ticket that pins existing behaviour, "removed" means changed: item 5's mutations are the proof.
5. **Mutation spot-check.** Pick up to three conditions, preferring sensitive areas from the harness file, money, permissions and state changes. For each, break the implementation locally (invert a condition, drop a line, return early) and confirm the matching test fails. Run with bytecode and build caches off (for Python, `PYTHONDONTWRITEBYTECODE=1`), revert, and confirm `git status` is clean. Never push these changes.
6. **Error paths.** For at least one error path, the test asserts the outcome or its type, the exact message, and that nothing else changed. For code with no state (a pure function), say so instead of the last part.
7. **Bad input through the interface.** Send the public interface one invalid input that no test covers (a missing field, out of range, wrong permissions). Confirm it's rejected.
8. **Edge cases from the spec.** Read the spec text (with no spec file, the ticket is the spec), think of two edge cases the tests don't cover, and try them.
   - Behaviour that contradicts the spec is a fail.
   - Behaviour the spec doesn't decide isn't a fail: list it under "Spec questions".
9. **Scope.** Run `git diff --stat <base>...<head>`. If the ticket lists a scope, every changed file in that net diff is inside it; mention any out-of-scope commit that a later commit reverted. In every case, the diff doesn't touch specs, `docs/agents/harness.md`, `AGENTS.md`/`CLAUDE.md` or CI config unless the ticket names that exact file. A file ticket's own PR changes only its `Status:` line, to `done`.
10. **Blast radius.** When the diff touches a shared module, a public interface, a data format or more than a handful of files, find the one fact the change's safety depends on (for example "every caller passes a sorted list", "the old field is never read"). Look past grep: library source at the pinned version, data on disk or the wire, flags, downstream code. Prove that fact with a command or test that runs real code. List confirmed risks and checks you cleared separately; an unproven fact is a FAIL with the fact named. For a small, self-contained diff, write "small diff" and skip.
11. **Real app.** When the project has a verification skill (`.claude/skills/verify-*/`, from the verify-app recipe) and the change touches a user-facing feature, drive that feature with it and attach the evidence. For other changes, write "not user-facing".
12. **Interrogate.** At Level 4, for a ticket tagged `Risk: high`, follow [interrogate.md](interrogate.md) and report its Intent, Findings and Dropped. Any surviving finding is a FAIL. Otherwise write "not required".
13. **Decision log.** Read the PR's decision log. A decision the code contradicts, or a "kept" row whose evidence doesn't hold up, is a finding. Missing rows aren't a fail by themselves, but a choice between real alternatives with no row goes under "Spec questions".
14. **Evidence and hygiene.**
    - The PR's evidence section covers every condition, including the red output. A condition with no red needs a note saying why, and a mutation in item 5 that makes its test fail.
    - Nothing in the diff, PR or logs exposes a secret.
    - No test talks to a shared or production system.

**Verdict:** PASS only if every item passes. Otherwise FAIL. Fill in [verdict-template.md](verdict-template.md).
