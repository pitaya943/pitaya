# Recipe: machine account

Level: 2. No files to copy: an account and a few settings.

## What it guards against

Not knowing who did what. With several agents sharing a person's account, every push, PR and comment looks like that person's, and an agent inherits the person's rights, including merging `main`.

## When it's worth adding

When a second agent works in the repository, or when agents act without a person watching each step.

## How to add it

1. Create a GitHub account for the agents (one per role or team of agents, if you want them told apart).
2. Invite it as a collaborator with **Write**. Never Admin, and never on the ruleset's bypass list.
3. Give the agent environment a token for that account: a fine-grained token limited to this repository, with Contents, Pull requests and Issues set to read and write, and nothing else. In particular no Workflows (it could change CI), Commit statuses (it could forge a required status), Actions or Administration permission. In the ruleset, pick **GitHub Actions** as the source of each required check, so only statuses that CI sets count.
4. Set the commit author in the agent's checkout: the account's login as the name, and its GitHub noreply address as the email (`<numeric id>+<login>` at `users.noreply.github.com`). `/build` does this when the harness file names a machine account.
5. Put the login under "Machine account" in `docs/agents/harness.md`.

## How to prove it works

- In the agent's environment, `gh api user --jq .login` (or the GitHub tool's "get me" call) prints the machine account's login.
- A commit the agent pushes shows that account as author on GitHub.
- A direct push to `main` from that account is rejected, by [protect-main](protect-main.md).

## Cost and false positives

One more account and token to manage, and to rotate when it expires. The token must not land in the repository, logs or PRs.

## Error message

When the agent finds it's signed in as someone else, `/build` stops and says so: "the GitHub login is not the machine account named in the harness file". To fix: sign the agent environment in with the machine account's token.

## Afterwards

Record the login under "Machine account" in the harness file. Add the [commit-author](commit-author.md) check to enforce the identity at merge time, and set the repository variable `MACHINE_ACCOUNT` to the login: the ticket-based checks require its PRs to name an open ticket, and fail closed when the variable is empty. Keep to one machine account for every agent role: then GitHub's rule that an author can't approve its own PR keeps the Owner's approval on `main`. More accounts need [multi-account](multi-account.md).

## When to remove it

When one person works with one agent again, and nobody needs to tell agents apart.
