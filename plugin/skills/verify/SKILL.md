---
name: verify
description: Verify one pull request cold. A fresh subagent that never saw the builder's conversation re-runs everything from a clean checkout, works through a checklist, and posts PASS or FAIL as a PR comment. Takes a PR number or URL.
disable-model-invocation: true
argument-hint: "<PR number or URL>"
---

# Verify a pull request

Verification is only worth something if it's independent. The verifier judges from the ticket, the spec, the diff and what it runs itself: never from the builder's conversation, and never from claims in the PR description.

## 1. Prepare (you, the coordinator)

1. Read `docs/agents/harness.md`. If it's missing, suggest `/setup` once, then continue with defaults: the document language is the conversation's, and there are no sensitive areas. Unattended (nobody in the conversation), the harness file must name a machine account and you must act as it: otherwise stop and say so (the plugin's `docs/concepts/autonomy.md`, "Unattended work needs a machine account").
2. Fetch the PR: its number, base branch, head commit and linked ticket. If there's no ticket, ask the user for the completion conditions. Don't infer them from the diff.
3. Count earlier verdicts on the PR (with agent-merge, also a commit's `verdict-fail` status whose comment is gone) to get this verify round's number. A verify round checks; a fix round changes code. They alternate: verify 1, fix 1, verify 2, and so on.
4. Note this session's ID for the verdict: `${CLAUDE_SESSION_ID}`. If that shows a placeholder instead of an ID, use the ID your tool gives the session (a cloud session's ID is in its link); if there is none, the verdict says `unavailable: <reason>`. Write it in the same form the PR's `Builder session:` lines use (a cloud session has a local ID and a `session_...` one; the check compares text). With the agent-merge guardrail (Level 3) the verdict is posted from a session that built none of the PR: a PASS doesn't count when its session is one a `Builder session:` line on the PR names, or when its session is `unavailable`. So if this session built it, a subagent isn't enough there: stop and hand the PR to a separate session.

## 2. Dispatch a fresh verifier

Start **one new subagent** with a fresh context. If this session wrote the code, this step isn't optional: you can't verify your own work (and with agent-merge, step 1.4 already sent you to a separate session). If the harness file's "Verification" asks for a separate session, give the user the pointers below as a prompt for that session instead.

Give it only pointers, not your opinions:

- the PR number, the base branch and the head commit;
- the ticket reference and the path to the harness file;
- the round number;
- the path to [checklist.md](checklist.md) and [verdict-template.md](verdict-template.md) in this skill's directory.

Tell it to:

- work in a clean checkout of the head commit (a new worktree or a fresh clone), never in this session's working tree;
- follow the checklist, and return the filled-in verdict;
- not modify product code or tests, and push nothing to the PR's branch: a push moves the head, and the verdict counts for one head only, so it would void itself. Its own screenshots go under `docs/evidence/<ticket>/verify/` on a branch of their own, `evidence/<PR>-<short sha>`, made from the head it judged and pushed with no pull request; the verdict links them there. In a session with an assigned branch, the "Branches" section of `AGENTS.md` grants that name; without the grant, leave the screenshots out and say so in the verdict.

## 3. Post the verdict

1. Read the returned verdict. Check that every checklist row has evidence, and that it has an Attention section: rows, or "None". A row without evidence counts as fail, and you send it back to the same verifier once to fill the gap.
2. Post the verdict as one PR comment, in the template, acting as the machine account from the harness file when there is one. The comment starts with the heading line, and names the full 40-character head commit and this session's ID: the agent-merge check reads exactly that. Never edit a verdict after posting it: an edited PASS doesn't count and a FAIL can't be taken back, so post a new one. (Only when the harness lists the multi-account guardrail with a separate verifier account, post it as a review from that account instead: `gh pr review <n> --approve` or `--request-changes`, or the GitHub tool's review call.)
3. Tell the user the result in one line, with the PR link.

## After the verdict

- PASS: whoever the harness file's "Autonomy" names merges. By default that's the Owner, so don't merge.
- FAIL: a builder fixes it, in the fix round with the FAIL's number. The plugin's `docs/concepts/states.md`, "Fix rounds", is the one definition: under `/autopilot` every fix round is a fresh session; otherwise round 1 may stay in the builder's session. Each new round is verified by a new subagent, or with agent-merge by a new session.
- FAIL number `Fix rounds` + 1 (the harness file's field; by default the third FAIL): recommend escalating to the Owner. Every earlier FAIL gets its fix round.
- Either way, end your reply with the exact next step from the verdict's "Next step" line, so a reader can't mistake one failed verify round for two.

## Don't

- Don't give PASS just because CI is green. CI is one row of the checklist.
- Don't leave a loosened check out of Attention because it was justified. A PASS with a `gate-change` row is still a PASS; the row is how the Owner sees it.
- Don't propose fix code in the verdict. Describe the problem, how to reproduce it, and what was expected.
- Don't write the model name from memory (`evidence` skill).
