# Recipe: multi-account hardening

Level: 2. Files: [`CODEOWNERS`](files/multi-account/CODEOWNERS), [`CODEOWNERS-agent-merge`](files/multi-account/CODEOWNERS-agent-merge).

## What it guards against

One agent account approving another's work. With a single machine account, GitHub's own rule that an author can't approve their pull request keeps the Owner's approval on `main`. Once there are two agent accounts, for example a separate verifier, either can approve the other's pull request, and that approval counts toward the ruleset.

## When it's worth adding

Only when more than one agent account has Write access to the repository. With one machine account, which is the default, skip it.

## How to add it

1. List every agent account in the repository variable `MACHINE_ACCOUNT`, comma separated, so the ticket-based checks treat each as an agent.
2. Copy `files/multi-account/CODEOWNERS` to `.github/CODEOWNERS` and replace `@example-owner` with the Owner's login.
3. In the `protect-main` ruleset, turn on **Require review from Code Owners**. Now only the Owner's approval lets a pull request into `main`.
4. With [agent-merge](agent-merge.md) on milestone branches, use `files/multi-account/CODEOWNERS-agent-merge` instead: it keeps rules, CI, tickets, milestones, decisions and the sensitive paths you add with the Owner.
5. Give each agent account its own token, and keep the verifier's token out of the builders' environment.

## How to prove it works

From a second agent account, approve a pull request the machine account opened. The merge box still says a review from a code owner is required.

## Cost and false positives

A `CODEOWNERS` file names a real login, so it lives in the repository. The Owner's own pull requests can't be approved by themselves, so they merge through the ruleset bypass, as before.

## Error message

GitHub shows "Review required: at least one approving review from a code owner is required" on the pull request.

## Afterwards

Record "multi-account" under "Guardrails" in the harness file, with the list of agent accounts.

## When to remove it

When only one agent account remains.
