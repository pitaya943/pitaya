# Recipe: scope

Level: 2. Files: [`check_scope.py`](files/scope/check_scope.py), [`scope.yml`](files/scope/scope.yml).

## What it guards against

A pull request changing files its ticket never mentioned: drive-by refactors, "while I was there" fixes, or two agents working in parallel overwriting each other's files.

## When it's worth adding

When two or more agents work at the same time, or when a review finds out-of-scope edits more than once.

## How to add it

1. Make sure tickets have a "## Scope" section listing paths or globs, one per bullet. `/plan` writes it. `*` matches inside one directory; `**` matches across directories.
2. Copy `files/scope/check_scope.py` to `.github/guardrails/check_scope.py`.
3. Copy `files/scope/scope.yml` to `.github/workflows/scope.yml`.
4. Name PR branches `ticket/<id>-<slug>`, which `/build` already does. See [how the checks find the ticket](README.md#how-the-checks-find-the-ticket).
5. After the first run, add the `scope` check to the required checks of [protect-main](protect-main.md).

## How to prove it works

On a ticket branch, change a file outside the ticket's scope and open a PR. The `scope` check fails and lists that file. Revert it, and the check passes.

Locally:

```bash
python3 .github/guardrails/check_scope.py --base origin/main --head HEAD --ticket ticket.md
```

## Cost and false positives

- Seconds per PR.
- A ticket whose scope was too narrow blocks a legitimate change. The fix is a one-line scope edit, which the Owner approves.
- A scope of `**` disables the check without anyone noticing, so the verifier should flag over-wide scopes.

## Error message

```text
FAIL scope: these files are outside the ticket's scope:
  README.md
To fix: revert the changes to these files, or, if the ticket really needs them, ask the Owner to add them to the ticket's "## Scope" section.
```

## Afterwards

Add `scope` under "Guardrails" in `docs/agents/harness.md`. The "Scope" field is now required in every ticket.

## When to remove it

When agents no longer work in parallel, or when months of transcripts show no out-of-scope edits and review catches the rare one.
