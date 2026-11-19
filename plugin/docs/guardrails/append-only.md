# Recipe: append only

Level: 2. Files: [`check_append_only.py`](files/append-only/check_append_only.py), [`append-only.yml`](files/append-only/append-only.yml).

## What it guards against

History being rewritten: an old decision edited to match what was built, a changelog entry quietly changed, or a log trimmed. These files are only useful if earlier entries stay as they were.

## When it's worth adding

When agents write to the decision log or changelog, or as soon as an old entry changed without anyone noticing.

## How to add it

1. Copy `files/append-only/check_append_only.py` to `.github/guardrails/check_append_only.py`.
2. Copy `files/append-only/append-only.yml` to `.github/workflows/append-only.yml`, and list your append-only files in `--files` (it starts with `docs/decisions.md,CHANGELOG.md`).
3. Tickets can add more under "## Append-only files".
4. After the first run, make `append-only` a required check.

A changed or removed line fails, and so does deleting the file. Creating it, and adding lines anywhere in it, passes.

## How to prove it works

In a PR, edit one existing line of `docs/decisions.md`. The check fails and shows the original line. Restore it and add the change as a new row instead: the check passes.

## Cost and false positives

- Seconds per PR.
- Fixing a typo in an old entry fails too. Add a correcting entry, or have the Owner make the edit in their own PR.
- It checks that lines were only added, not that the new lines are right.

## Error message

```text
FAIL append-only: these files lost or changed lines:
  docs/decisions.md:
    - | D3 | Only the Owner merges main |
To fix: restore the original lines and add your change as new lines at the end, for example a new entry that supersedes the old one.
```

## Afterwards

Add `append-only` under "Guardrails" in the harness file, with the list of files.

## When to remove it

When the files are generated, for example a changelog built from per-PR fragments, so nobody edits them by hand.
