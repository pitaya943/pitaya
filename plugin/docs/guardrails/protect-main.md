# Recipe: protect main

Level: 1. No files to copy: these are repository settings only the Owner can change. `/setup` hands over these steps.

## What it guards against

An agent, or anyone, changing `main` directly: pushing unreviewed commits, force-pushing over history, or deleting the branch. Without it, the Level 1 tests workflow can go red and nothing stops the merge.

## When it's worth adding

Always, from the first day an agent has write access.

## How to add it

In the repository: **Settings → Rules → Rulesets → New ruleset → New branch ruleset**.

| Field | Setting |
| --- | --- |
| Ruleset name | `protect-main` |
| Enforcement status | **Active** |
| Bypass list | **Repository admin**, mode **For pull requests only** (the Owner, for emergencies). Agent accounts never go here |
| Target branches | **Add target → Include default branch**. An empty target list protects nothing |
| Restrict deletions | On |
| Block force pushes | On |
| Require a pull request before merging | On, with **Required approvals: 1** and **Dismiss stale pull request approvals when new commits are pushed** on. Agents open PRs as the machine account, so the Owner can approve them; that approval is what stops an agent with Write access from merging its own green PR. The Owner's own PRs merge through the bypass. Set approvals to 0 only if no agent account can open PRs, or at Level 3 with [agent-merge](agent-merge.md), where the `verdict` status takes its place |
| Require status checks to pass | On. Add the `tests` check from the Level 1 workflow (it appears in the list after it has run once) |
| Require branches to be up to date | Off at Level 1; on if merges often break `main` |

Then check **Settings → Collaborators**: agent accounts have **Write**, never Admin.

## How to prove it works

Anyone with read access can list the rules that apply to `main`:

```bash
gh api repos/<owner>/<repo>/rules/branches/main --jq '.[].type'
```

Expected: `deletion`, `non_fast_forward`, `pull_request` and `required_status_checks`. An empty list means the ruleset targets no branch.

The agent can also try `git push origin HEAD:main` on a throwaway commit: it must be rejected. Do this only once the rules are listed, so a misconfigured ruleset doesn't let the commit through.

## Cost and false positives

Every change needs a PR and a green `tests` run, which adds a few minutes. Urgent fixes go through the Owner's bypass.

## Error message

GitHub rejects the push with a "Repository rule violations found" message that names the rule. The Level 1 `no_push_main` hook usually stops the attempt earlier and says what to do instead: push a branch and open a pull request.

## Afterwards

Under "Guardrails" in `docs/agents/harness.md`, add: `protect-main: ruleset on main (PR required, no force push, no deletion, tests required)`.

## When to remove it

Don't, while agents can write to the repository. Revisit the settings (for example, required approvals) when more people join.
