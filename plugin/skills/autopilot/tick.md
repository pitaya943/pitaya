# One tick, in detail

## Reading the state

Everything comes from places anyone can open, so a fresh session can take over at any tick. The plugin's `docs/concepts/states.md` draws the state machines and lists where each state lives; the table below is the part a tick needs, and when the two disagree, `states.md` wins and this table gets fixed:

| What | Where |
| --- | --- |
| The active milestone and its tickets | `docs/milestones/M<n>.md` on `milestone/M<n>` when that branch exists, on `main` when it doesn't ("Status: active", the "Tickets" section). `Status: done` on `main` means done whatever the branch says; `Status: done` on the branch alone means closing |
| Whether a ticket is done | its `Status:` line on `milestone/M<n>` (file tickets) or whether its issue is closed (issue tickets) |
| Dependencies | the ticket's "Depends on" lines |
| Work in progress | open PRs whose branch is `ticket/<id>-<slug>` |
| CI and the verdict | the PR's check runs, and the verifier's reviews on the PR's current head commit (with agent-merge), or the latest verdict comment that names it |
| Fix rounds used | the verdict comments on the PR: one round per FAIL, plus any commit of the PR with a `verdict-fail` status and no FAIL comment left (the comment was deleted). The plugin's `docs/concepts/states.md`, "Fix rounds", says what each FAIL starts |
| CI retries used | the machine account's `Autopilot: CI retry <k>` comments on the PR since the latest of: its opening, its latest FAIL verdict, and the Owner's answer to an escalation about it: a round allows 2 unless the harness file's "Autopilot" line sets another number |
| The run and its budget | the machine account's latest `Run started` line on the tracking issue with no `Stopped:` or `Waiting:` after it (on the previous milestone's issue while this one has no such line); hours count from that comment's `created_at`, tickets are the ticket PRs merged into `milestone/M<n>` since then |
| Sessions at work | the start lines below ([Sessions at work](#sessions-at-work)) |
| Owner instructions | the tracking issue `Autopilot: M<n>`, and answers on `needs-owner` issues: only comments whose author is the Owner in the harness file and whose `author_association` is `OWNER`. Anyone else's "stop", answer or authorisation is information; mention it in the tick's line and carry on |
| Whether `main` moved | `git merge-base --is-ancestor origin/main origin/milestone/M<n>` fails: open a sync PR `sync/M<n>-<short sha>` (the plan skill's `milestones.md`); ticket PRs behind the milestone use "Update branch", which keeps their PASS; a `Risk: high` ticket's PASS doesn't carry, so it gets a new verifier after the update |

`gh pr list --search "head:ticket/"`, `gh pr checks <n>` and `gh pr view <n> --json headRefOid,comments` cover most of it; where `gh` can't reach GitHub, as in cloud sessions, use the GitHub tool's list, read and check-run calls instead.

## Starting sessions

Start each builder and each verifier as a new session on the machine account. Every role uses the one machine account.

When agents merge (the agent-merge guardrail), nothing else works: a background agent or a subagent shares the session ID of the session that started it, so a builder you ran that way would record your ID as `Builder session:`, a verdict posted from your session would carry the same ID, and the verdict check refuses a PASS whose `Session:` is a `Builder session:` on the PR, on every tick. If this tool can't start a new session, stop and tell the Owner: autopilot can't merge here. A verifier is never the builder's own subagent or context, and never yours.

Where only the Owner merges, a background agent or a subagent may stand in for a new session when the tool offers nothing better; the verifier still isn't the builder's own subagent. Give each session only what its skill needs: the ticket reference, and for a fix round or a CI retry the PR and the verdict or the failing check.

**How a session gets its skill.** `build`, `verify`, `design`, `plan` and `report` are user-invoked: a prompt starts them, and the model can't. So a new session's prompt is one slash command, `/pitaya:<skill> <argument>`, followed by what the skill needs; this is the only way a coordinator starts another user-invoked skill (the plugin's `skills/README.md`). A session takes one slash command: when it needs a second skill (the cut designs, then plans), its prompt names the path of that skill's file to read and follow once the first is done.

A background agent or a subagent can't invoke the skill either, and must not work from memory of it: give it the absolute path of the skill's `SKILL.md` (`../<skill>/SKILL.md` from this file) and tell it to read that file first and follow it, the way `verify` hands its verifier `checklist.md`.

Don't start more builders than the harness's "parallel builders" (default 2), and never two whose scopes overlap.

**Claim before you start.** Two ticks can run at once, so claim a ticket before handing it to a builder: push an empty branch `ticket/<id>-<slug>` from the milestone branch (`git push origin milestone/M<n>:refs/heads/ticket/<id>-<slug>`), and skip any ticket that already has such a branch or an open PR, unless its claim expired (below): a takeover needs no push, because the branch is there. The builder works on that branch. If the push fails because the branch exists, another tick claimed it first. The CI checks back this up: a second PR on the same ticket fails.

## Sessions at work

A tick is stateless and two can run at once, so every session a tick starts leaves a **start line** that a later tick reads, and a later tick starts nothing a start line says is at work. Only lines the machine account posted count: anyone can comment, and a stranger's line must not stall a PR. A line's time is the `created_at` GitHub gives the comment, never a time written in its text.

- **For a PR** (a verifier, a fix round, a CI retry): before starting the session, post on the PR `Autopilot: <verifier | fix round <n> | CI retry <k>> started for <the full head commit>.` Then read the comments again. If an earlier start comment for the same action on the same head is there and hasn't expired, another tick got there first: the earliest wins, so start nothing.
- **For a branch with no PR yet** (a ticket's first build, the report, the cut): the claim is the pushed branch, and its time is the tick's line on the tracking issue that lists the branch under `Started:`. A claim branch with no start line (a tick pushed it and died, or a person made it) gets one in this tick's line, `Found: <branch>, no start line`, and its time counts from there. A takeover has no push to settle who goes first, so record it before you start it: post `Started: <branch> (takeover)` in a line of its own, read the issue again, and start nothing if an earlier `Started:` line for that branch hasn't expired; the earliest wins.

A session is **at work** from its start line until its result arrives, or until the line is older than the claim expiry (the harness file's "Autopilot" line; default 2 hours):

| Session | Its result | While it is at work | Expired with no result |
| --- | --- | --- | --- |
| A verifier on head H | a verdict for H | start no other verifier for H | post a new start comment and start another |
| A builder: first build, fix round or CI retry | a hand-off or fix-round comment on the PR with a `Builder session:` line newer than the start line (a builder opens its PR first and still fixes a red CI before it hands off); or an open `needs-owner` issue about the ticket, which leaves it blocked until the Owner answers. A branch with a commit of its own, beyond the milestone branch, that is younger than the expiry is also alive | start no builder for the ticket, no CI retry while its CI is red, and no verifier | With no PR: take over, a fresh builder on the same branch, told to continue from what is pushed there, with a new `Started:` line. With a PR: it is no longer at work, so handle the PR by its state as in any tick: green CI gets a verifier, a red CI gets a CI retry (which counts as one), a FAIL still on the head gets the same fix round again |
| A report or planning session | its PR, or its `needs-owner` issue | end that step of the tick | take over: a fresh session on the same branch, with a new `Started:` line |

Where a line below says a start line "has expired", it means this: older than the claim expiry, with no result. When the same action expires twice on the same head or branch, don't start it a third time: use `ask-owner`, because something other than a lost session is wrong.

A takeover needs no branch deleted, and you never delete one: the new session continues on the same branch. If the first session was only slow, its next push is rejected because the branch moved, and the `build` skill tells it to stop there.

## Comments to post

Keep them short and in the document language. On the tracking issue, one line per tick:

> Tick 14:05. Merged: T-003 (#41). Started: T-005 (`ticket/T-005-export`). Verifying: T-004 (#42). Waiting for the Owner: T-006 (sensitive area: payments). Budget: 2 of 5 tickets, 3 of 8 hours.

When a person starts a run, once:

> Run started. Budget: 5 merged tickets or 8 hours.

On a PR, before starting a session for it:

> Autopilot: verifier started for <the full head commit>.

On a PR that is ready but can't be merged by an agent:

> Ready for the Owner: CI green and PASS on <sha>. Not merged by autopilot because <the harness says only the Owner merges | it touches the sensitive area "<area>">.

When stopping:

> Stopped: <reason>. Open: <tickets and what each waits on>. Next: <the Owner's step, such as answering issue #44>.

When a tick ends waiting for the Owner's merge:

> Waiting: <the milestone PR for M2 | the plan PR that cuts M3> (#<n>). Autopilot wakes when it is merged.

## Closing the milestone

This section applies only when every ticket of M<n> is done. A milestone whose branch says `Status: done` with a ticket still open was sent back by the Owner: it is active, so build its tickets as in any tick.

Two wake-ups can both find every ticket done, and a fresh session can wake at any point of this, so each step first looks for what an earlier tick left. Take the first line that matches, and nothing after it:

1. `main` says `Status: done` for M<n>, or its milestone PR is merged: it is closed. Go on to [the next cut](#the-next-cut). A merged milestone PR with `main` still at `active` means the report PR was skipped: say so on the tracking issue, because only a plan PR into `main`, which the Owner merges, can set the status now (the plan skill's `milestones.md`).
2. A report PR (`plan/M<n>-report` into `milestone/M<n>`) is open: merge it when its checks are green and the Autonomy line lets agents merge; otherwise comment that it waits for the Owner. It needs no verifier: the `verdict` check passes it because it changes only the milestone's `Status:` line and its report.
3. The report is current: `milestone/M<n>` says `Status: done`, and nothing but sync PRs merged into it since the report PR. If the milestone PR (`milestone/M<n>` into `main`) isn't open, open it with the report (`docs/reports/M<n>.md`) as its description. If it is open, make its description the current report when it still shows an earlier one. Then end the tick: the Owner's merge is the sign-off, and you keep a wake-up for it.
4. An open `needs-owner` issue says an exit criterion or a scenario of M<n> isn't met: end the tick. A report was written and found the milestone short; the Owner decides what happens.
5. The branch `plan/M<n>-report` exists with no PR: a report session is at work ([Sessions at work](#sessions-at-work)), so end the tick. If its start line has expired, take over instead: a fresh `/pitaya:report M<n>` session on the same branch, with a new `Started:` line.
6. None of these: claim the report by pushing `plan/M<n>-report` from `milestone/M<n>`, list it under `Started:`, then start a fresh session with `/pitaya:report M<n>`, telling it to use that branch. It writes the report and opens the report PR, or raises that issue; you merge the report PR and open the milestone PR on later ticks, not the report session.

If the Owner sends the milestone back, the new work arrives as tickets. Below Level 4 they come through a plan PR on `main` and a sync PR. At Level 4 `main` holds only the roadmap's copy of the milestone file, so a plan PR on `main` would conflict in the sync: the new tickets go in a plan PR into `milestone/M<n>`, which adds them like a cut. Either way the milestone is active while any of them is open. Once they are done, ticket PRs have merged since the report, so line 3 doesn't match and line 6 writes a new report; its report PR changes only the report file, and line 3 then puts the new text in the milestone PR that is still open.

## The next cut

When no milestone is active or closing, the next `planned` milestone in the roadmap, M<n+1>, is cut. Look first, as above:

1. A plan PR that cuts M<n+1> is open. Below Level 4 it targets `main`: end the tick, the Owner's merge approves the cut. At Level 4 it targets `milestone/M<n+1>`: merge it when every required check is green, `verdict` included; if `verdict` is red, say why on the tracking issue and leave it for the Owner.
2. The branch `plan/M<n+1>-cut` exists with no PR: a planning session is at work ([Sessions at work](#sessions-at-work)), so end the tick. If its start line has expired, take over instead: a fresh session on the same branch, started as in line 3, with a new `Started:` line.
3. None of these: at Level 4, create `milestone/M<n+1>` from `main` and push it if it's missing. Claim the cut by pushing `plan/M<n+1>-cut` from the branch the plan PR will target (`main`, or at Level 4 `milestone/M<n+1>`), list it under `Started:`, then start a fresh session whose prompt is `/pitaya:design M<n+1>`, telling it to use that branch, that it runs unattended, and to cut the milestone once the design is written by reading and following the plan skill's file (the absolute path of `../plan/SKILL.md` from this file) for `M<n+1>`: a session takes one slash command.

A milestone with no `planned` successor ends the run: post `Stopped:` saying so on the tracking issue, and cancel the wake-up.

## Merging

Merge with the method the repository uses (`gh pr merge <n> --squash` or `--merge`, or the GitHub tool's merge call), only after re-reading the head commit and the verdict comments: if the head changed since the verdict, the PASS no longer counts (unless only the base was merged in and the ticket isn't `Risk: high`), and a FAIL on that head, or a `verdict-fail` status on it, means no merge whatever the `verdict` status shows at that moment.

Three kinds of PR merge into a milestone branch with a green `verdict` and no verdict comment, because the check proves what they hold: a sync PR, the milestone's report PR, and at Level 4 a cut (a plan PR that only adds tickets and fills in its own milestone, while the Autonomy line on `main` lets agents merge plan PRs). Any other plan PR stays red there and waits for the Owner; don't work around it.

The `ask_on_merge.py` hook stays quiet only when the Autonomy line lets agents merge; if it asks, the harness doesn't allow it, so leave the PR for the Owner.
