# One tick, in detail

## Reading the state

Everything comes from places anyone can open, so a fresh session can take over at any tick. The plugin's `docs/concepts/states.md` draws the state machines and lists where each state lives; the table below is the part a tick needs, and when the two disagree, `states.md` wins and this table gets fixed:

| What | Where |
| --- | --- |
| The active milestone and its tickets | `docs/milestones/M<n>.md` on `main` ("Status: active", the "Tickets" section) |
| Whether a ticket is done | its `Status:` line on `milestone/M<n>` (file tickets) or whether its issue is closed (issue tickets) |
| Dependencies | the ticket's "Depends on" lines |
| Work in progress | open PRs whose branch is `ticket/<id>-<slug>` |
| CI and the verdict | the PR's check runs, and the verifier's reviews on the PR's current head commit (with agent-merge), or the latest verdict comment that names it |
| Fix rounds used | the verdict comments on the PR: one round per FAIL |
| Owner instructions | the tracking issue `Autopilot: M<n>`, and answers on `needs-owner` issues |
| Whether `main` moved | `git merge-base --is-ancestor origin/main origin/milestone/M<n>` fails: open a sync PR `sync/M<n>-<short sha>` (the plan skill's `milestones.md`); ticket PRs behind the milestone use "Update branch", which keeps their PASS |

`gh pr list --search "head:ticket/"`, `gh pr checks <n>` and `gh pr view <n> --json headRefOid,comments` cover most of it; where `gh` can't reach GitHub, as in cloud sessions, use the GitHub tool's list, read and check-run calls instead.

## Starting sessions

Use whatever this tool offers to start a fresh session or background agent, in this order of preference: a new session on the machine account, a background agent, a subagent. A verifier must never be the builder's own subagent or context; every role uses the one machine account. Give each session only what its skill needs: the ticket reference, and for a fix round the PR and the verdict.

Don't start more builders than the harness's "parallel builders" (default 2), and never two whose scopes overlap.

**Claim before you start.** Two ticks can run at once, so claim a ticket before handing it to a builder: push an empty branch `ticket/<id>-<slug>` from the milestone branch (`git push origin milestone/M<n>:refs/heads/ticket/<id>-<slug>`), and skip any ticket that already has such a branch or an open PR. The builder works on that branch. If the push fails because the branch exists, another tick claimed it first. The CI checks back this up: a second PR on the same ticket fails.

## Comments to post

Keep them short and in the document language. On the tracking issue, one line per tick:

> Tick 14:05. Merged: T-003 (#41). Started: T-005. Verifying: T-004 (#42). Waiting for the Owner: T-006 (sensitive area: payments). Budget: 2 of 5 tickets.

On a PR that is ready but can't be merged by an agent:

> Ready for the Owner: CI green and PASS on <sha>. Not merged by autopilot because <the harness says only the Owner merges | it touches the sensitive area "<area>">.

When stopping:

> Stopped: <reason>. Open: <tickets and what each waits on>. Next: <the Owner's step, such as merging the plan PR that closes M2>.

## Merging

Merge with the method the repository uses (`gh pr merge <n> --squash` or `--merge`, or the GitHub tool's merge call), only after re-reading the head commit: if it changed since the verdict, the PASS no longer counts. The `ask_on_merge.py` hook stays quiet only when the Autonomy line lets agents merge; if it asks, the harness doesn't allow it, so leave the PR for the Owner.
