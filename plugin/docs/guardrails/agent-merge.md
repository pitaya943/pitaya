# Recipe: agent merge

Level: 3. Files: [`check_verdict.py`](files/agent-merge/check_verdict.py), [`agent-merge.yml`](files/agent-merge/agent-merge.yml).

## What it guards against

Agents merging ticket PRs into a milestone branch on a stale or missing verdict: a PASS given for an earlier commit, or no verification at all. Without a mechanical gate, "agents merge after PASS" depends on agents remembering. Agents never merge `main`: the Owner merges each milestone (D44).

## When it's worth adding

Only when waiting for a person to merge is the bottleneck, and the prerequisites in [autonomy](../concepts/autonomy.md) hold:

- Level 1 in place;
- Level 2's scope, read-only-paths, no-weakened-tests and done-when checks required;
- a verifier that's a fresh session, never the builder's own context or its subagent;
- milestones with their own branches, so `main` changes only when the Owner merges a milestone;
- agents and code you trust (see [What it trusts](#what-it-trusts)).

Otherwise keep the default: only the Owner merges.

## How to add it

1. Use milestone branches: protect `milestone/*` as in [protect-main](protect-main.md#milestone-branches), and keep `main` at one required approval, so only the Owner merges a milestone into `main`.
2. Copy `files/agent-merge/check_verdict.py` to `.github/guardrails/` and `files/agent-merge/agent-merge.yml` to `.github/workflows/`. The verdict comes from `MACHINE_ACCOUNT`, the account `/verify` posts as; set `VERIFIER_ACCOUNTS` only if the verifier uses another account (then add [multi-account](multi-account.md)).
3. In the `protect-milestones` ruleset, require the `verdict` status, with **GitHub Actions** as its source, alongside the other required checks, and in the same edit lower **Required approvals** from 1 to 0. Never the second without the first: below Level 3 the approval is what keeps a machine account from merging its own PR. **Require branches to be up to date** must be on in that ruleset too: it is a prerequisite here, not an option, because a carried PASS (below) was given before the base moved, and only the checks that re-run on the updated branch judge the combination.
4. Change "Verification" in `docs/agents/harness.md` to "a separate session": the Level 1 default, a subagent started by the builder's own `/verify`, posts its verdict from the builder's session, which the check refuses. A new session has its own ID and is separate whoever started it, provided none of the builder's conversation goes into its prompt ([prerequisite 3](../concepts/autonomy.md#prerequisites-for-agent-merging)).
5. Change "Autonomy" in `docs/agents/harness.md` to "Agents merge ticket PRs into milestone branches; only the Owner merges main". The `ask_on_merge.py` hook reads that value and stops asking before merges, except before `gh pr merge --admin` and while the harness file names no machine account; `main` stays protected by its required approval.

The workflow runs when a PR changes and when a verdict comment or review is posted, edited or deleted, one run at a time per pull request (a run still waiting when a newer one arrives is dropped; every run reads everything again). It checks out only the base and runs the base's copy of `check_verdict.py`. It sets a `verdict` status on the PR's **current head commit**: success when a verifier gave PASS for that exact commit and no FAIL, or in the cases below where the check proves a pull request needs none (a carried PASS, a sync PR, a report PR, a Level 4 cut).

**What counts as a verdict.** A comment from the verifier's account that starts with the heading `## Verification: PASS` or `## Verification: FAIL` and has a `Head commit:` line with the full 40-character commit. A comment that quotes a verdict further down isn't one, and a 7-character prefix isn't a commit. A PASS also needs a `Session:` line with a real ID (`unavailable` doesn't count), and that session must not be one a `Builder session:` line on the pull request names: the builder's hand-off and fix-round comments carry theirs, so a verdict posted from a session that built the work doesn't pass it, whether that session ran the checklist itself or through a subagent. An edited PASS doesn't count.

**A FAIL is one-way.** A FAIL on a commit is final for that commit. Each FAIL the workflow sees is recorded in a `verdict-fail` status on its commit and read back on every later run, so a FAIL still counts when its comment is edited or deleted afterwards; an edited FAIL counts by itself too. The way forward is a fix, a push and a PASS on the new head.

**What carries.** A new push moves the head, so an earlier PASS no longer counts, with one exception: GitHub's "Update branch", a merge of the base and nothing else. The check proves it rather than trusting the commit message. It fetches the PR's commits as data, and passes the head only if two things hold: its tree equals the tree git gets by merging the current base into the PASS head, and every commit added since the PASS is a true merge, with two parents and the tree git gets by merging them. A change folded into that merge, or any commit after it, gives another tree and needs a new verdict. The second proof is for what the tree can't show: `git merge -s ours` keeps the tree and still records a commit as merged, so its changes would be dropped when it's merged for real later. Pressing "Update branch" several times is fine: each press adds one true merge. Without this, every ticket merged into the milestone would send every other open ticket back to verification. Two things stop a carry: a FAIL on the PASS head, and `Risk: high` in the ticket. Nobody verified the combined result of a carried PASS, only the checks that re-run on the updated branch did, and a high-risk ticket is where that isn't enough: it needs a new `/verify` after every update.

**Sync PRs.** A sync PR (`sync/<slug>` into `milestone/<id>`, the plan skill's `milestones.md`) passes without a verdict when its tree is exactly the milestone merged with the newest default-branch commit it contains and every commit it adds is a true merge, because all of that was merged into the default branch already.

**Plan PRs.** No verifier judges a plan PR, so a verdict comment never passes one. A milestone PR, and a plan PR into the default branch, always stay red: the Owner merges those. A plan PR into a milestone branch passes in two cases, each proved from its diff:

- The **report PR** (`plan/M<n>-report` into `milestone/M<n>`, the `report` skill; the check accepts any `plan/` branch, the name is the skills' convention): it changes nothing but `docs/reports/M<n>.md` and the `Status:` line of `docs/milestones/M<n>.md`, which may only become exactly `done` (`done, criteria waived` is another claim, and waits for the Owner; a ticket marked that way isn't done here either, while the ticket checks, which read any `Status: done...` as done, still refuse to build on it: each reads the line the safe way for its own question), for the milestone the base branch is named after, and no ticket file with `Milestone: M<n>` is still open once the PR merges: the check reads the tickets from the merge result, so a report branch made before a ticket was added is judged like a fresh one. A report PR that changes the report alone passes too: a milestone sent back gets a new report that way. The Owner reads both changes in the milestone PR, whose merge is the sign-off.
- A **cut** at Level 4: the Autonomy line of `docs/agents/harness.md` on the default branch has the Level 4 value, "Agents merge ticket and plan PRs into milestone branches; ..." (any case or quoting; a hand-written sentence that only mentions plan PRs doesn't count). The PR changes only plan files and deletes nothing. It adds plan files and fills in its own milestone, without setting it to `done`, with or without a rider: closing a milestone is the report PR's. Of the plan files that exist it may change only its own milestone file, the glossary, the architecture map and `docs/decisions.md`; a ticket, another milestone's file, a design, a report or an ADR that exists stays as the Owner read it, so a cut that supersedes an ADR (which edits the old one's status) waits for the Owner. The Owner reviews the cut at that milestone's sign-off.

Any other plan PR into a milestone branch, such as one that re-plans an open ticket, stays red and waits for the Owner, who merges it with the bypass or plans it on the default branch instead. A FAIL on the head blocks either kind like any other pull request.

**The status belongs to the commit**, not to the pull request: if the same commit is the head of two pull requests, they share one `verdict`, and the last run wins. `main` never relies on it (its ruleset requires the Owner's approval), and whoever merges reads the verdict comments again first (`/autopilot` does).

## What it trusts

pitaya assumes cooperating agents ([access](../concepts/access.md#what-pitaya-assumes)); this recipe guards against mistakes, not forgery. Use it only with agents and code you trust.

- **One machine account.** Builders, verifiers and `/autopilot` all post as one machine account, so the commenter's login can't tell them apart. The `Builder session:` and `Session:` lines catch the honest mistake, a session passing its own work. A session that writes a false ID isn't stopped. The stricter defence is a separate verifier account in `VERIFIER_ACCOUNTS`, whose token builders never hold ([multi-account](multi-account.md)).
- **The workflow file.** `pull_request_target` and `issue_comment` events run the base's or the default branch's copy of `agent-merge.yml`, but GitHub runs a `pull_request_review` event with the pull request's own copy, which holds `statuses: write`. `.github/` is read-only in ticket PRs, the agents' token has no Workflows or Commit statuses permission ([machine-account](machine-account.md)), and the verifier reports any change under `.github/` as a `gate-change` row; nothing more is built.
- **Timing.** A FAIL is recorded by the run that sees it. One posted and deleted again before any run read it leaves no record.
- **Plan PRs without a verifier.** Nobody verifies a report PR or a Level 4 cut before it merges into the milestone branch; the check only proves how little they can hold. A report that overstates, or a cut that plans the wrong tickets, is caught at the Owner's sign-off, not before. With issue-only tickets the check can't see an open ticket, so a report PR passes while one is.
- **Issue tickets.** With issue-only tickets the scope, the test IDs and the `Risk:` line are read from an issue body that any account with write access can edit, the agents' included. Keep tickets as files when agents merge.

## How to prove it works

Get a PASS verdict on a ticket PR into a milestone branch, then push one more commit. The `verdict` status turns red, and the merge button is blocked until `/verify` runs again on the new head. A "## Verification: PASS" comment from anyone but the verifier, an edited one, or one whose `Session:` is the builder's, changes nothing. Then post a FAIL on a head and delete the comment: the `verdict-fail` status stays on the commit, and a PASS on that same head doesn't turn `verdict` green. Last, open a plan PR into the milestone branch that changes a ticket: `verdict` stays red, with or without a PASS comment.

## Cost and false positives

- Every push needs a fresh verification before merging, and so does every "Update branch" on a `Risk: high` ticket.
- A FAIL can't be taken back, not even one posted by mistake: push a new commit and verify that.
- Builders and verifiers each need a new session. A subagent or a background agent shares the session ID of whatever started it, so one session that starts both a builder and a verifier that way gets every PASS refused. `/autopilot` starts new sessions for both, and stops where it can't.
- Ticket PRs reach the milestone branch without a person reading them. The Owner reads the milestone as a whole, through `/report M<n>` and its exit criteria, before it reaches `main`. A milestone that went wrong is thrown away, so the worst case costs one milestone.

## Error message

```text
FAIL agent-merge: no PASS verdict for head a1b2c3d.
To fix: run /verify on the current head, in a session that didn't build it (a new push voids earlier verdicts, except a merge of the base alone). The verdict comment starts with the heading, and names the full 40-character head commit and the verifier's session.
```

## Afterwards

Add `agent-merge` under "Guardrails" in the harness file, and schedule regular `/report` and `/retro` runs so someone reads what merged.

## When to remove it

When agents go back to "only the Owner merges", or when the Owner reads every verdict before merging anyway.
