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
3. For a milestone (`/report M<n>`), the range is the tickets listed in `docs/milestones/M<n>.md`. Check each exit criterion with evidence, and say which ones aren't met. When `docs/milestones/M<n>-design.md` exists, also check every scenario: the test it names passes, or it's listed as not met. At Level 4, add the swarm and the decision-log audit in [milestone-level4.md](milestone-level4.md). If all are met, propose the closing plan PR that sets the milestone to `Status: done` and adds the report as `docs/reports/M<n>.md`; the Owner's merge of the milestone PR is the sign-off. In the milestone PR's description, write `Closes #<n>` for the issue mirror of every done ticket in the milestone: ticket PRs merge into the milestone branch, where GitHub ignores closing keywords, so the sign-off merge into `main` is what closes them.

## Gather, don't remember

Use only sources anyone can open:

- the merged PRs and their descriptions;
- the tickets and their done-when conditions;
- the verifier's verdict comments and the CI results;
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
- Don't overstate. Passing tests mean the spec is met, not that the spec is right.

Markdown by default; HTML if the Owner asks for it.

## Deliver

Show the report in the conversation, then ask where it should live: a comment on a tracking issue, or a file under `docs/reports/` added through a pull request (for a milestone, the closing plan PR, which may add `docs/reports/*.md`).

If "Learning" is on in the harness file, end by offering the `learning` review.
