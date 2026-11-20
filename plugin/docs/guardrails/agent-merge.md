# Recipe: agent merge

Level: 3. Files: [`check_verdict.py`](files/agent-merge/check_verdict.py), [`agent-merge.yml`](files/agent-merge/agent-merge.yml).

## What it guards against

Agents merging ticket PRs into a milestone branch on a stale or missing verdict: a PASS given for an earlier commit, or no verification at all. Without a mechanical gate, "agents merge after PASS" depends on agents remembering. Agents never merge `main`: the Owner merges each milestone (D44).

## When it's worth adding

Only when waiting for a person to merge is the bottleneck, and the prerequisites in [autonomy](../concepts/autonomy.md) hold:

- Level 1 in place;
- Level 2's scope, read-only-paths, no-weakened-tests and done-when checks required;
- a verifier that's a fresh session, never the builder's own context;
- milestones with their own branches, so `main` changes only when the Owner merges a milestone.

Otherwise keep the default: only the Owner merges.

## How to add it

1. Use milestone branches: protect `milestone/*` as in [protect-main](protect-main.md#milestone-branches), and keep `main` at one required approval, so only the Owner merges a milestone into `main`.
2. Copy `files/agent-merge/check_verdict.py` to `.github/guardrails/` and `files/agent-merge/agent-merge.yml` to `.github/workflows/`. The verdict comes from `MACHINE_ACCOUNT`, the account `/verify` posts as; set `VERIFIER_ACCOUNTS` only if the verifier uses another account (then add [multi-account](multi-account.md)).
3. In the `protect-milestones` ruleset, require the `verdict` status, with **GitHub Actions** as its source, alongside the other required checks, and in the same edit lower **Required approvals** from 1 to 0. Never the second without the first: below Level 3 the approval is what keeps a machine account from merging its own PR.
4. Change "Autonomy" in `docs/agents/harness.md` to "Agents merge ticket PRs into milestone branches; only the Owner merges main". The `ask_on_merge.py` hook reads that value and stops asking before merges; `main` stays protected by its required approval.

The workflow runs when a PR changes and when a verdict comment or review is posted, edited or deleted. It runs in the base branch's context (`pull_request_target`, and the default branch's copy for comments and reviews) and checks out only the base, so nothing in the PR can change the check or the status. It sets a `verdict` status on the PR's **current head commit**: success only when the verifier gave PASS for that exact commit and no FAIL. A new push moves the head, so an earlier PASS no longer counts, with one exception: GitHub's "Update branch", a merge of the base and nothing else. The check proves it rather than trusting the commit message. It fetches the PR's commits as data, and passes the head only if two things hold: its tree equals the tree git gets by merging the current base into the PASS head, and every commit added since the PASS is a true merge, with two parents and the tree git gets by merging them. A change folded into that merge, or any commit after it, gives another tree and needs a new verdict. The second proof is for what the tree can't show: `git merge -s ours` keeps the tree and still records a commit as merged, so its changes would be dropped when it's merged for real later. Pressing "Update branch" several times is fine: each press adds one true merge. Without this, every ticket merged into the milestone would send every other open ticket back to verification. A sync PR (`sync/<slug>` into `milestone/<id>`, the plan skill's `milestones.md`) passes without a verdict when its tree is exactly the milestone merged with the newest default-branch commit it contains and every commit it adds is a true merge, because all of that was merged into the default branch already. Edited verdict comments don't count. Plan and milestone PRs never pass.

## How to prove it works

Get a PASS verdict on a ticket PR into a milestone branch, then push one more commit. The `verdict` status turns red, and the merge button is blocked until `/verify` runs again on the new head. A "## Verification: PASS" comment from anyone but the verifier, or an edited one, changes nothing.

## Cost and false positives

- Every push needs a fresh verification before merging.
- Ticket PRs reach the milestone branch without a person reading them. The Owner reads the milestone as a whole, through `/report M<n>` and its exit criteria, before it reaches `main`. A milestone that went wrong is thrown away, so the worst case costs one milestone.

## Error message

```text
FAIL agent-merge: no PASS verdict for head a1b2c3d.
To fix: run /verify on the current head (a new push voids earlier verdicts, except a merge of the base alone) and fix what it reports.
```

## Afterwards

Add `agent-merge` under "Guardrails" in the harness file, and schedule regular `/report` and `/retro` runs so someone reads what merged.

## When to remove it

When agents go back to "only the Owner merges", or when the Owner reads every verdict before merging anyway.
