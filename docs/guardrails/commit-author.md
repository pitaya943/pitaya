# Recipe: commit author

Level: 2. Files: [`check_commit_author.py`](files/commit-author/check_commit_author.py), [`commit-author.yml`](files/commit-author/commit-author.yml).

## What it guards against

Commits made under the wrong identity: an agent committing as a person, as another agent, or with an email GitHub can't link to any account. Without it, the history no longer tells you which agent did what.

## When it's worth adding

Together with [machine-account](machine-account.md), once more than one agent or identity commits to the repository.

## How to add it

1. Set up the [machine account](machine-account.md) and its commit identity.
2. Set the repository variable `MACHINE_ACCOUNT` (Settings → Secrets and variables → Actions → Variables) to its login.
3. Copy `files/commit-author/check_commit_author.py` to `.github/guardrails/check_commit_author.py`.
4. Copy `files/commit-author/commit-author.yml` to `.github/workflows/commit-author.yml`. Put the Owner's login in `--also-allow` if the Owner uses GitHub's "Update branch" button on agent PRs.
5. After the first run, make `commit-author` a required check.

It compares GitHub's own `author.login` for each commit, not the email written in the commit, so copying an address doesn't pass. It runs on PRs opened by the machine account; PRs the Owner opens are skipped.

## How to prove it works

On an agent's branch, make one commit with a different author (`git -c user.name=someone -c user.email=someone@example.com commit ...`) and push it. The check fails, names the commit, and says it isn't linked to an account.

## Cost and false positives

- One API call per PR.
- A commit made in GitHub's web interface by someone else fails, unless their login is in `--also-allow`.
- Fixing a wrong author means recreating the commits. Do it on a new branch, never by rewriting a shared one.

## Error message

```text
FAIL commit-author: commits not authored by example-bot:
  1a2b3c4: authored by example-owner
To fix: set the commit author to example-bot with its GitHub noreply email, then recreate these commits on a new branch (don't rewrite a shared branch) and open a new PR.
```

## Afterwards

Add `commit-author` under "Guardrails" in `docs/agents/harness.md`.

## When to remove it

When only one agent works in the repository, or when the ruleset requires signed commits from the machine account, which proves the same thing.
