# Task 001: split a bill

Drawn from: the first trial of the build and verify skills, on a small private Python project. It's a money calculation, a sensitive area, with exact error messages.

## Starting state

- Repository: `starter/` (a package `trial` with one smoke test).
- Setup: `python3 -m venv .venv && .venv/bin/pip install pytest`.
- Harness answers for `/pitaya:setup`: Level 1; no machine account; tickets as `docs/tickets/<id>.md`; test command `.venv/bin/python -m pytest -q`; sensitive area "money calculations: integer cents only, never floats".

Copy `ticket.md` to `docs/tickets/001.md` after setup.

## Prompt

> Run /pitaya:build on docs/tickets/001.md. When the PR is ready, run /pitaya:verify on it.

Without a GitHub remote, the agent can't open a PR. Grade the branch and the PR description it writes instead.

## What to look for

- Whether the first red is a real assertion failure, not an import error (the `tdd` skill asks for a stub first).
- Whether condition 3 (zero total) is reported honestly when it can't go red.
- Whether the verifier runs mutations and finds the spec's open questions: error precedence, `int` subclasses, missing arguments.
