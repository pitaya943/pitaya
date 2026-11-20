# Waking up

pitaya ships no scheduler. A tick only needs something to start it, and the tools you already have can. Prefer events: they wake you when there is something to do, and cost nothing while you wait.

| Mechanism | How | Use it for |
| --- | --- | --- |
| **PR events** | The session subscribes to each ticket PR it starts, and to the report PR, the milestone PR and the plan PR of a cut when it finds them (in Claude Code on the web, the PR-activity subscription). CI results, verdict comments and merges each wake it | The main loop: a verdict arrives, so merge; a merge happens, so start the next ticket |
| **In-session loop** | `/loop` without an interval lets the session pace itself; or keep one long session running | A milestone you watch run in one sitting |
| **Schedule** | A scheduled task or cron that starts a fresh session with `/pitaya:autopilot M<n> wake` every few hours | A safety net when an event gets lost, and runs nobody watches overnight |
| **GitHub Action** | A workflow on `pull_request` (closed, merged), `issue_comment` and `check_suite` events that starts an agent with `/pitaya:autopilot M<n> wake`, for example through the Claude GitHub Action. Give the workflow a `concurrency` group for the milestone, so one tick runs at a time | Running entirely in CI, with no session kept open |

Because every tick is stateless, mixing them is safe: two wake-ups at once only repeat a read, and the start lines keep them from starting the same session twice ([tick.md](tick.md#sessions-at-work)).

A schedule or an Action starts a fresh session each time, so it passes `wake`. A session started that way carries on the run that is open and never starts a new run: the budget is counted from the open run's `Run started` line on the tracking issue, so it holds across sessions, and a run that stopped stays stopped until a person starts the next one with `/pitaya:autopilot M<n>`.

Whichever you use, stop it when the run stops: cancel the schedule, end the loop, or let the subscriptions lapse. A tick that ends waiting for the Owner to merge the milestone PR or a plan PR is not the run stopping: keep the subscription to that PR, or the schedule, so the merge starts the next tick.
