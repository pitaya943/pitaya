# Recipe: agent merge

Level: 3. Files: [`check_verdict.py`](files/agent-merge/check_verdict.py), [`agent-merge.yml`](files/agent-merge/agent-merge.yml).

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

1. Give the verifier its own account, one the builder can't post as. Set the repository variable `VERIFIER_ACCOUNTS` to its login.
2. Copy `files/agent-merge/check_verdict.py` to `.github/guardrails/` and `files/agent-merge/agent-merge.yml` to `.github/workflows/`.
3. In the ruleset on `main`, require the `verdict` status that the workflow sets, alongside the other required checks, and lower **Required approvals** from 1 to 0: the verdict now does the approval's job.
4. Change "Autonomy" in `docs/agents/harness.md` to "Agents merge after CI is green and the verdict is PASS". The `ask_on_merge.py` hook reads that line and stops asking before merges.

The workflow runs when a PR changes and when a comment is posted. Each time, it sets a `verdict` status on the PR's **current head commit**: success only when the latest verdict comment for that exact commit is PASS. A new push moves the head, so an earlier PASS no longer counts.

## How to prove it works

Get a PASS verdict on a PR, then push one more commit. The `verdict` status turns red, and the merge button is blocked until `/verify` runs again on the new head. Posting a "## Verification: PASS" comment from the builder's account changes nothing.

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
