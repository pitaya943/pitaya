# Recipe: read-only paths

Level: 2. Files: [`check_read_only.py`](files/read-only-paths/check_read_only.py), [`read-only-paths.yml`](files/read-only-paths/read-only-paths.yml).

## What it guards against

An agent changing the rules it works under to get its work through: editing AGENTS.md or the harness config, loosening CI, rewriting the spec to match the code, or rewriting past decisions.

## When it's worth adding

With [scope](scope.md), when agents work without someone reading every diff, or as soon as an agent has edited a rule or spec file in a ticket PR.

## How to add it

Set the repository variable `MACHINE_ACCOUNT` to the agents' login first, if it isn't set yet: the workflow uses it to tell agent PRs from the Owner's ([details](README.md#how-the-checks-find-the-ticket)).

1. Copy `files/read-only-paths/check_read_only.py` to `.github/guardrails/check_read_only.py`.
2. Copy `files/read-only-paths/read-only-paths.yml` to `.github/workflows/read-only-paths.yml`, and add your spec paths to `--also` (for example `docs/spec/**`).
3. After the first run, make `read-only-paths` a required check.

Read-only by default: every `AGENTS.md` and `CLAUDE.md`, `docs/agents/**`, `.claude/**`, `.github/**`, `docs/decisions.md`, `docs/adr/**`, `docs/tickets/**` and `docs/milestones/**`. A ticket PR may change one line of its own ticket file, `Status:`, to mark it done; the workflow passes the ticket's path so the check knows which file that is.

The one exception: a ticket's "## Scope" lists the file **exactly**, with no wildcard, because the Owner approved that change. A glob such as `.github/**` in the scope never unlocks a read-only path.

## How to prove it works

In a ticket PR, change `AGENTS.md`. The check fails and names the file. Then list `AGENTS.md` exactly in the ticket's scope: the check passes. Change the scope entry to `*.md`: it fails again.

## Cost and false positives

- Seconds per PR.
- Rule and spec changes now need either the Owner's own PR or an exact scope entry. That's the intent, but it adds a step to normal maintenance.
- It only covers ticket PRs. The Owner's own changes aren't affected.

## Error message

```text
FAIL read-only-paths: this PR changes read-only files:
  AGENTS.md
To fix: revert these changes. If the ticket really needs one of them, ask the Owner to list that exact file (no wildcard) in the ticket's "## Scope" section.
```

## Afterwards

Add `read-only-paths` under "Guardrails" in the harness file, with the extra paths you added to `--also`.

## When to remove it

When rule and spec files sit behind a CODEOWNERS review that the agents' accounts can't satisfy. That enforces the same thing at merge time.
