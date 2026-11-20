# Where tickets live

The harness file's "Tickets" line picks one of three modes. The checks in the guardrail recipes support all three: each looks for `docs/tickets/<id>.md` on the base branch first, then for the issue numbered in the branch name.

## Files with an issue mirror (recommended)

The file is the source of truth; the issue is where people discuss it and get notified.

1. Number the tickets `T-001`, `T-002`, and on: three digits, never reused. Read `docs/tickets/` for the highest number so far.
2. For each ticket, open an issue labelled `ticket`, titled `T-001: <title>`. Its body is one line of summary and: "The source of truth is `docs/tickets/T-001.md`; edits here don't change the ticket." Dependencies stay in the file.
3. Write `docs/tickets/T-001.md` from [ticket-template.md](ticket-template.md), with `Status: open` and `Issue: #<n>`. Dependencies read `Blocked by T-002`.
4. Commit all the files on a branch named `plan/<short-slug>` and open one PR. Use that name even if the session was given an assigned branch (cloud sessions are): the checks recognise a plan PR by it, so ask the user to allow it instead of using the assigned branch. The Owner's merge puts them on `main`, where the checks read them, and is the plan's approval of record. A plan PR may change only `docs/tickets/*.md`, `docs/milestones/*.md`, `docs/agents/glossary.md`, `docs/agents/architecture.md`, `docs/decisions.md` and `docs/adr/*.md`; the guardrail workflows skip their ticket checks for it and fail it if it changes anything else. A plan PR targets `main`, where only the Owner's approval merges it (the machine account can't approve its own PR), at every level.

Afterwards, a builder works on `ticket/T-001-<slug>`. Its PR changes the file's `Status:` line to `done` and says `Closes #<n>`, so the file and the issue close in the same merge. The scope and read-only checks allow that one line in the PR's own ticket file, and nothing else in any ticket file.

To find open work, read the `Status:` lines: `grep -L "Status: done" docs/tickets/*.md`.

## Files only

The same, without step 2 and without the `Issue:` line. Use it when the Owner doesn't want issues.

## Issues only

The lightest mode: each ticket is an issue labelled `ticket`, with "Blocked by #<n>" lines; the branch is `ticket/<n>-<slug>` and the PR says `Closes #<n>`. The checks read the issue body when they run, and anyone with write access can edit it, so a PR's author could widen its own scope. Prefer files once the scope or read-only checks are on.

## Risk

Every ticket carries `Risk: low` or `Risk: high`. `/plan` sets **high** when the ticket touches a sensitive area from the harness file, changes a public interface or the data model, includes a migration, or has a scope that spans more than one module. The Owner may override the tag in the plan PR, either way. At Level 4, high-risk tickets get the extra verification in the `verify` skill's `interrogate.md`; below Level 4 the tag is information only.
