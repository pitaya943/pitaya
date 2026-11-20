# Waking up

pitaya ships no scheduler. A tick only needs something to start it, and the tools you already have can. Prefer events: they wake you when there is something to do, and cost nothing while you wait.

| Mechanism | How | Use it for |
| --- | --- | --- |
| **PR events** | The session subscribes to each ticket PR it starts, and to the report PR, the milestone PR and the plan PR of a cut when it finds them (in Claude Code on the web, the PR-activity subscription). CI results, verdict comments and merges each wake it | The main loop: a verdict arrives, so merge; a merge happens, so start the next ticket |
| **In-session loop** | `/loop` without an interval lets the session pace itself; or keep one long session running | A milestone you watch run in one sitting |
| **Schedule** | A scheduled task or cron that starts a fresh session with `/pitaya:autopilot M<n>` every few hours | A safety net when an event gets lost, and runs nobody watches overnight |
| **GitHub Action** | A workflow on `pull_request` (closed, merged), `issue_comment` and `check_suite` events that starts an agent with `/pitaya:autopilot M<n>`, for example through the Claude GitHub Action | Running entirely in CI, with no session kept open |

Because every tick is stateless, mixing them is safe: two wake-ups at once only repeat a read. To avoid two runs acting on the same PR, a tick skips a PR whose latest comment from autopilot is less than ten minutes old.

Whichever you use, stop it when the run stops: cancel the schedule, end the loop, or let the subscriptions lapse. A tick that ends waiting for the Owner to merge the milestone PR or a plan PR is not the run stopping: keep the subscription to that PR, or the schedule, so the merge starts the next tick.
