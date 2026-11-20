---
name: report
description: Summarize a batch of merged work for the Owner, built only from what the repository and GitHub show. Conclusions first, every claim linked to evidence, unfinished work stated plainly, and steps the Owner can run to check it.
disable-model-invocation: true
argument-hint: "<what to cover: a milestone, a list of PRs or tickets, or a date range>"
---

# Report

## Before you start

1. Read `docs/agents/harness.md` for the document language and whether "Learning" is on. If it's missing, suggest `/setup` once and write in the language of the conversation.
2. Settle the range with the user if the argument doesn't make it exact: which PRs or tickets, from when to when.
3. For a milestone (`/report M<n>`), the range is the tickets listed in `docs/milestones/M<n>.md`, read on `milestone/M<n>` when that branch exists and on `main` when it doesn't (the plugin's `docs/concepts/states.md`). Check each exit criterion with evidence, and say which ones aren't met. When `docs/milestones/M<n>-design.md` exists, also check every scenario: the test it names passes, or it's listed as not met. At Level 4, add the swarm and the decision-log audit in [milestone-level4.md](milestone-level4.md). Closing the milestone is under [Deliver](#deliver).

## Gather, don't remember

Use only sources anyone can open:

- the merged PRs and their descriptions;
- the tickets and their done-when conditions;
- the verifier's verdict comments, with every Attention row in them, and the CI results;
- each PR's decision log: the choices and dead ends worth the Owner's attention;
- `docs/decisions.md`, when the project keeps one.

Never write from memory of the sessions. If something isn't in those sources, it doesn't go in the report, or it goes in as "unverified".

## Write

Use [report-template.md](report-template.md), in the document language.

- **Conclusion first.** The Owner hasn't followed any ticket; open with what changed for users and whether it's ready.
- **Every claim links to evidence:** a PR, a verdict comment, a CI run, or a command with its output.
- **Numbers can be recomputed.** "47 tests pass" comes with the command that produced it.
- **How to verify** is a list of steps the Owner can run with any model or by hand: commands, expected output, manual checks.
- **Decisions the agents made** that no spec or ticket stated get their own section, even if it's "None".
- **What isn't done** is said plainly: never "could be improved later".
- **Attention** collects every Attention row from the verdicts in range into one table, with the PR and a link to the verdict, so the Owner sees at sign-off each `gate-change`, `role`, `unproven-claim` and `undisclosed` row without opening every PR. Copy the rows; don't judge or drop them. The verdict comments stay the record.
- An `undisclosed` row goes first and is named in the Conclusion: it is the sign that the trust in the agents may not hold, and the Owner decides whether to add stricter defences (the plugin's `docs/levels.md`, "What the levels assume").
- Don't overstate. Passing tests mean the spec is met, not that the spec is right.

Markdown by default; HTML if the Owner asks for it.

## Deliver

Show the report in the conversation, then ask where it should live: a comment on a tracking issue, or a file under `docs/reports/` added through a pull request (a plan PR may add `docs/reports/*.md`).

**A milestone** doesn't get that question. When every ticket is done and every exit criterion and scenario is met, close it from inside, so the Owner's sign-off and the status change are one merge. Look before each step, because an earlier run may have done it:

1. Open the **report PR** unless one is open: branch `plan/M<n>-report` from `milestone/M<n>` (the branch `/autopilot` names, when it started you; in a session with an assigned branch, the "Branches" section of `AGENTS.md` grants the name, and without it you ask the user or, unattended, open a `needs-owner` issue), into `milestone/M<n>`. It changes the `Status:` line of `docs/milestones/M<n>.md` to `Status: done`, adds or replaces `docs/reports/M<n>.md`, and nothing else. It merges like a sync PR: the Owner below Level 3, agents from Level 3, where the `verdict` check passes it without a verifier because it holds only those two changes.
2. Once the report PR is merged, open the milestone PR, `milestone/M<n>` into `main`, with the report as its description; if it is already open (the Owner sent the milestone back, and this report replaces an earlier one), replace its description instead. Not before the merge: a milestone PR merged without the status would leave `main` saying `active`. Under `/autopilot` this step is the tick's, so end after step 1. Otherwise it is yours: wait for the Owner's merge, or tell the user that running `/report M<n>` again afterwards opens it, which is all that run then does. Write `Closes #<n>` in the milestone PR for the issue mirror of every done ticket in the milestone: ticket PRs merge into the milestone branch, where GitHub ignores closing keywords, so the sign-off merge into `main` is what closes them.
3. The Owner's merge of the milestone PR is the sign-off, and it brings `Status: done` to `main`. No plan PR follows it.

If something isn't met, say so in the report and don't open the report PR: the milestone isn't done. First look for a `needs-owner` issue about the same shortfall. If none exists, raise one with the `ask-owner` skill, linking the report, so the next session finds it instead of writing the report again. If the Owner has answered one, follow the answer: new tickets (the plan skill's `milestones.md`, "Closing a milestone"); changed exit criteria, which the Owner changes through a plan PR; or sign-off as it is, in which case open the report PR with a report that names what isn't met and links the answer.

If "Learning" is on in the harness file, end by offering the `learning` review.
