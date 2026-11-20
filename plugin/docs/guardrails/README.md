# Guardrail recipes

Recipes add protection when a project needs it, a level at a time. Level 1 comes with `/setup`; Levels 2 and 3 come from here. [`../suggestion.md`](../suggestion.md) explains what each level achieves, and [`../levels.md`](../levels.md) lists everything each level includes, with what each recipe requires first.

## Recipe format

Every recipe has the same eight sections:

1. **What it guards against:** the concrete incident without it.
2. **When it's worth adding:** the signal to look for.
3. **How to add it:** steps, plus copyable files under `files/<recipe>/`. Once copied, they're yours.
4. **How to prove it works:** an action that makes it fail, and what you should see.
5. **Cost and false positives:** what it slows down, what normal work it blocks, how to handle that.
6. **Error message:** what it prints when it fails. It always ends with "To fix:".
7. **Afterwards:** what to record in `docs/agents/harness.md`.
8. **When to remove it:** the evidence that it's no longer needed.

The copyable checks use only Python's standard library and git, one standalone file per check. Each starts with a `pitaya template <version>` header, so you can tell later whether your copy is stale.

## By symptom

| You saw this | Add |
| --- | --- |
| An agent pushed to `main`, merged its own PR, or a change merged without review | [protect-main](protect-main.md) (with one required approval) |
| You can't tell which agent did what | [machine-account](machine-account.md) |
| An agent changed files its ticket didn't mention, or two agents overwrote each other | [scope](scope.md) |
| An agent edited the rules, the spec or CI to get its work through | [read-only-paths](read-only-paths.md) |
| A test disappeared or was skipped and CI stayed green | [no-weakened-tests](no-weakened-tests.md) |
| A ticket was called done but one of its conditions had no passing test | [done-when](done-when.md) |
| Commits show up under a person's name or an unknown email | [commit-author](commit-author.md) |
| An old decision or changelog entry was edited | [append-only](append-only.md) |
| Two PRs were each fine but broke `main` once both merged (migrations, lockfile) | [serial-resources](serial-resources.md) |
| A PR said "done" and showed nothing | [evidence](evidence.md) |
| Long work lost track between sessions, or requirements shrank | [progress-file](progress-file.md) |
| The verifier missed what the builder missed | [second-model-review](second-model-review.md) |
| Waiting for a person to merge is the bottleneck | [agent-merge](agent-merge.md) |
| A harness change made agents better or worse, and nobody could tell which | [project-evals](project-evals.md) |

## By level

| Level | Recipe |
| --- | --- |
| 1 | [protect-main](protect-main.md) (the steps `/setup` hands to the Owner) |
| 2 | [machine-account](machine-account.md), [commit-author](commit-author.md), [scope](scope.md), [read-only-paths](read-only-paths.md), [no-weakened-tests](no-weakened-tests.md), [done-when](done-when.md), [append-only](append-only.md), [serial-resources](serial-resources.md), [evidence](evidence.md), [multi-account](multi-account.md) |
| 3 | [progress-file](progress-file.md), [agent-merge](agent-merge.md) |
| 4 | [second-model-review](second-model-review.md), [project-evals](project-evals.md) |

## Adding a guardrail is rule work

Installing a recipe changes `.github/` and the harness file, which agents don't change on their own. Either the Owner opens that pull request, or it's a ticket whose "## Scope" lists the exact files, so the ticket-based checks, including the one being installed, can pass on it.

## How the checks find the ticket

Ticket-based checks read the ticket in CI. Each workflow's "Find the ticket" step looks in two places:

- `docs/tickets/<id>.md` on the **base** branch, when the PR branch is named `ticket/<id>-<slug>`;
- otherwise, the GitHub issue whose number is in the branch name, `ticket/<number>-<slug>`.

Pull requests opened by agent accounts, the logins in the repository variable `MACHINE_ACCOUNT` (comma separated, any case; Settings → Secrets and variables → Actions → Variables), must use a ticket branch, or the check fails, so an agent can't avoid the checks by naming its branch differently. When the variable is empty, the check fails rather than guessing. People's pull requests from a branch without a ticket are skipped, with a note. A milestone PR (`milestone/<id>` into `main`) is skipped too: its tickets passed these checks on their way into the milestone, and the Owner reviews it as a whole.

When `docs/tickets/` exists on the base branch, tickets are files: a branch naming an issue number doesn't fall back to that issue, so an agent can't open its own issue and use it as a wider ticket. A ticket whose `Status:` is `done` (or a closed issue) can't be claimed, and neither can a ticket another open PR already works on.

A branch named `plan/<slug>` is a plan PR: it adds ticket files for the Owner to merge. The step skips the ticket checks for it, but fails it if it changes anything besides `docs/tickets/*.md`, `docs/milestones/*.md`, `docs/agents/glossary.md`, `docs/agents/architecture.md` and `docs/decisions.md`.

When a ticket file is found, the step also outputs its path, `ticket_path`. The scope and read-only checks use it for one exception: the PR may change its own ticket's `Status:` line, to mark it done, and nothing else in any ticket file (`docs/tickets/**` is read-only by default).

Reading from the base branch matters: a PR can't widen its own scope by editing its ticket file. An issue body has no such protection, because anyone with write access can edit it. If agents have write access and you need the stronger guarantee, keep tickets as files; an issue can still mirror each one for discussion (the `plan` skill's `tickets.md` describes the modes).
