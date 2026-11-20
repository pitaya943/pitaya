# Autonomy

The `Autonomy` field in `docs/agents/harness.md` says who may merge what. Whatever it says, only the Owner merges `main`.

| Setting | Who merges ticket PRs | Who merges `main` | When it fits |
| --- | --- | --- | --- |
| **Only the Owner merges `main`** (default) | The Owner, after reading the verdict | The Owner | Almost always. A person sees every change before it lands |
| **Agents merge ticket PRs into milestone branches; only the Owner merges main** | An agent, into `milestone/M<n>`, once CI is green and the verdict is PASS | The Owner, one milestone at a time | Level 3, when waiting for a person is the bottleneck and the prerequisites below hold |
| **Agents merge ticket and plan PRs into milestone branches; only the Owner merges main** | As above. An agent also merges the cut of the next milestone, a plan PR into `milestone/M<n+1>`, with no verifier | The Owner, one milestone at a time | Level 4, with [deep verification](../guardrails/deep-verification.md): the Owner reads each cut at the milestone's sign-off, not before it |

To pass a cut, the `verdict` check reads this value from the harness file on the default branch, so the setting that counts there is the one the Owner merged. The `ask_on_merge.py` hook reads the copy in the session's checkout.

The milestone branch is the blast radius (D44): a milestone that went wrong is thrown away, and `main` never saw it. pstack trusts its agents entirely; Matt Pocock's skills put a person on every PR. This sits between them: agents run a milestone on their own, and a person signs off each one.

## Prerequisites for agent merging

Agents merging their own work is safe only when the checks a person would make are mechanical:

1. Level 1 is fully in place: the tests check is required on `main`, and the hooks are installed. The required approval on `milestone/*` drops from 1 to 0 only together with requiring the `verdict` status there (D37); `main` keeps its approval at every level. The milestone ruleset also requires branches to be up to date, so the checks ran on what the merge produces.
2. Level 2's merge checks are on, at least scope, read-only paths, no weakened tests and done-when, so an agent can't widen its task or remove the tests that judge it.
3. The verifier is a separate session, not the builder's session: a subagent or background agent shares its parent's session ID, whatever model it runs, so the `verdict` check treats it as the builder. A new session has its own ID, so it is separate whoever started it, the builder's session included, as long as none of the builder's conversation goes with it: its prompt is the command and the pull request, never a summary of the work or what to conclude. Builders and verifiers each record their session ID on the pull request, and the `verdict` check refuses a PASS from a builder's session. You trust the agents: the verdict guards against mistakes, not forgery ([what pitaya assumes](access.md#what-pitaya-assumes)).
4. Sensitive areas still go to the Owner: the agent escalates a ticket that touches one without a covering test, and the Owner sees every change when reviewing the milestone.
5. Someone reviews merged work afterwards, for example through `/report` and `/retro` on a fixed schedule.
6. Agents merge ticket and sync PRs only into milestone branches. A sync PR (`sync/<slug>`) brings `main` into the milestone and needs no verifier: the `verdict` check proves it holds nothing else. The same goes for a milestone's report PR (`plan/M<n>-report`), which sets `Status: done` and adds the report before the sign-off, and at Level 4 for a plan PR that cuts the next milestone. `main` changes only when the Owner merges a milestone, so the worst case is one milestone thrown away (D44).
7. Agents merge only through `/autopilot` or a builder that follows its merge rules: re-read the head commit and the verdict comments, require a PASS and no FAIL on that head for a ticket PR, and a green `verdict` status for the three kinds in point 6 that have no verdict comment (a sync PR, the report PR, and at Level 4 the cut). Sensitive areas and every other plan PR are left to the Owner.

If any of these stops holding, go back to the default.

## Unattended work needs a machine account

A session is **unattended** when nobody in the conversation approves its steps: one that `/autopilot`, a schedule, a GitHub Action or another session started, and any session that runs with permission prompts turned off. Before agents act unattended, the harness file must name a machine account, and the session must be signed in as it ([machine-account](../guardrails/machine-account.md)). From Level 2 the same holds for every agent session, attended or not: the ticket checks tell an agent's pull request by its author.

Without one, a session acts as the account it is signed in with, usually the Owner's, and wherever GitHub looks the agent is the Owner:

- **The ruleset's bypass is the agent's.** `gh pr merge --admin`, or a merge call the bypass applies to, lands a pull request on `main` with no approval and a red `tests` check.
- **The required approval gates nothing.** GitHub doesn't let an author approve its own pull request, which is what keeps a machine account from merging; here the author is the Owner's account, nobody else can approve, and the bypass becomes the ordinary way to merge.
- **The ticket checks pass it.** They apply to pull requests the machine account opened, so one opened from the Owner's account counts as a person's and needs no ticket.
- **Its comments are the Owner's.** A comment the agent posts has the Owner's login and `author_association` `OWNER`, which is exactly what makes a comment a decision ([who can answer](escalation.md#who-can-answer)).

What is left is the hooks alone, and a hook is a question, not a wall: while the harness file's "Machine account" line says "none", `ask_on_merge.py` asks before every merge, whatever the Autonomy line says, and it asks before `gh pr merge --admin` in every project. A question needs someone to answer it. So "none" fits only while a person watches every step and merges by hand; it is the Level 1 solo setup, and nothing more.

What each part does about it:

- `/setup` recommends a machine account in every project, asks for one from Level 2 and before it turns "Autopilot" on, and with "none" says in the harness file and in its output that merge protection is the hooks alone.
- `/autopilot` stops before its first tick when the harness file names no machine account, or the session isn't signed in as it.
- `/build` stops when it was started unattended and the harness file names none. With a person in the conversation it goes on, as that person's account.
- Turning permission prompts off is something the Owner does to a session, and no skill can see it: there the rule is the Owner's to keep.

## What doesn't change

Whatever the setting: nobody pushes directly to `main`, nobody force-pushes it, and the verifier never merges the work it verified.
