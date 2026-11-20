# Recipe: agent merge

Level: 3. Files: [`check_verdict.py`](files/agent-merge/check_verdict.py), [`agent-merge.yml`](files/agent-merge/agent-merge.yml), [`CODEOWNERS`](files/agent-merge/CODEOWNERS).

## What it guards against

Agents merging their own work on a stale or missing verdict: a PASS given for an earlier commit, a verdict the builder wrote for itself, or no verification at all. Without a mechanical gate, "agents merge after PASS" depends on agents remembering.

## When it's worth adding

Only when waiting for a person to merge is the bottleneck, and the prerequisites in [autonomy](../concepts/autonomy.md) hold:

- Level 1 in place;
- Level 2's scope, read-only-paths, no-weakened-tests and done-when checks required;
- a verifier that's a separate session or model;
- sensitive areas still go to a person.

Otherwise keep the default: only the Owner merges.

## How to add it

1. Give the verifier its own account, one the builder can't act as: its token lives only where verifier sessions run, never in the builder's environment. Set the repository variable `VERIFIER_ACCOUNTS` to its login; it must differ from `MACHINE_ACCOUNT`, or the check refuses. With agent-merge on, `/verify` posts its verdict as a pull request review from that account: "Approve" for PASS, "Request changes" for FAIL. Other accounts can dismiss a review but can't change it, and each review records the commit it was given on.
2. Copy `files/agent-merge/check_verdict.py` to `.github/guardrails/` and `files/agent-merge/agent-merge.yml` to `.github/workflows/`.
3. Replace `.github/CODEOWNERS` with `files/agent-merge/CODEOWNERS` (the Owner's login in place of `@example-owner`), and add one line per sensitive area from the harness file. Keep **Require review from Code Owners** on: PRs that touch rules, CI, tickets, milestones, decisions or a sensitive area still need the Owner's approval, so a plan PR or a rule change can't merge on a verdict.
4. In the ruleset on `main`, require the `verdict` status that the workflow sets, alongside the other required checks, and lower **Required approvals** from 1 to 0: for every other path, the verdict now does the approval's job.
5. Change "Autonomy" in `docs/agents/harness.md` to "Agents merge after CI is green and the verdict is PASS". The `ask_on_merge.py` hook reads that line and stops asking before merges.

The workflow runs when a PR changes and when a review is submitted, edited or dismissed. It runs in the base branch's context (`pull_request_target`) and checks out only the base, so nothing in the PR can change the check or the status. It sets a `verdict` status on the PR's **current head commit**: success only when a verifier approved that exact commit and none requested changes on it. A new push moves the head, so an earlier PASS no longer counts. Plan PRs never pass. In the ruleset, pick **GitHub Actions** as the source of the required `verdict` and other checks, so a status posted by any other token doesn't count.

## How to prove it works

Get a PASS verdict on a PR, then push one more commit. The `verdict` status turns red, and the merge button is blocked until `/verify` runs again on the new head. An approving review from the builder's account, or a "## Verification: PASS" comment from anyone, changes nothing.

## Cost and false positives

- Every push needs a fresh verification before merging.
- The verifier needs its own account.
- Unreviewed code can reach `main`. A person only reads it afterwards, through `/report` and `/retro`. That's the real cost, and why this isn't the default.

## Error message

```text
FAIL agent-merge: the latest verdict for head a1b2c3d is no verdict.
To fix: run /verify on the current head (a new push voids earlier verdicts) and fix what it reports; only a PASS for this exact commit lets the pull request merge.
```

## Afterwards

Add `agent-merge` under "Guardrails" in the harness file, and schedule regular `/report` and `/retro` runs so someone reads what merged.

## When to remove it

When agents go back to "only the Owner merges", or when the Owner reads every verdict before merging anyway.
