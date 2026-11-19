# Recipe: evidence

Level: 2. Files: [`check_evidence.py`](files/evidence/check_evidence.py), [`evidence.yml`](files/evidence/evidence.yml).

## What it guards against

A pull request that says "done, tests pass" and shows nothing: no command, no output, no screenshot. The Owner then has to take the claim on trust or redo the work.

## When it's worth adding

When PRs arrive faster than the Owner can re-run them, or the first time a "verified" claim turns out to be unverified.

## How to add it

1. Copy `files/evidence/check_evidence.py` to `.github/guardrails/check_evidence.py`.
2. Copy `files/evidence/evidence.yml` to `.github/workflows/evidence.yml`. It re-runs when the PR description is edited.
3. Tickets with a visible change say so under "## Screenshots": `required` or `not required`.
4. After the first run, make `evidence` a required check.

The PR description needs a "## Evidence" section holding at least one code block (the commands and their output) or a link. The `build` skill's PR template already has it. When the ticket requires screenshots, the section must show an image, or the PR must add one under `docs/evidence/`.

## How to prove it works

Open a PR whose "## Evidence" section only says "tests pass". The check fails. Paste the test command and its output in a code block, and the check passes on the edit.

## Cost and false positives

- Seconds per PR.
- It checks that evidence is there, not that it's true. The verifier re-runs it.
- A pure documentation PR still needs some evidence, such as the link checker's output.

## Error message

```text
FAIL evidence: the "## Evidence" section has no code block or link, only prose.
To fix: paste the commands and their real output in a code block, or link the CI run.
```

## Afterwards

Add `evidence` under "Guardrails" in the harness file. "Screenshots" is now a ticket field for visible changes.

## When to remove it

When a verifier's verdict, which re-runs everything, is required for every merge, so the PR description no longer matters.
