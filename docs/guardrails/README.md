# Guardrail recipes

Recipes add protection when a project needs it, a level at a time. Level 1 comes with `/setup`; Levels 2 and 3 come from here. [`../suggestion.md`](../suggestion.md) explains what each level achieves.

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
| An agent pushed to `main`, or a change merged without review | [protect-main](protect-main.md) |
| You can't tell which agent did what | [machine-account](machine-account.md) |
| An agent changed files its ticket didn't mention, or two agents overwrote each other | [scope](scope.md) |
| An agent edited the rules, the spec or CI to get its work through | [read-only-paths](read-only-paths.md) |
| A test disappeared or was skipped and CI stayed green | [no-weakened-tests](no-weakened-tests.md) |
| A ticket was called done but one of its conditions had no passing test | [done-when](done-when.md) |

## By level

| Level | Recipe |
| --- | --- |
| 1 | [protect-main](protect-main.md) (the steps `/setup` hands to the Owner) |
| 2 | [machine-account](machine-account.md), [scope](scope.md), [read-only-paths](read-only-paths.md), [no-weakened-tests](no-weakened-tests.md), [done-when](done-when.md) |
| 2 (next) | commit-author, append-only, serial-resources, evidence |
| 3 (later) | second-model review, progress file, agent merging, project evals |

## How the checks find the ticket

Ticket-based checks read the ticket in CI. Each workflow's "Find the ticket" step looks in two places:

- `docs/tickets/<id>.md` on the **base** branch, when the PR branch is named `ticket/<id>-<slug>`;
- otherwise, the GitHub issue whose number is in the branch name, `ticket/<number>-<slug>`.

Reading from the base branch matters: a PR can't widen its own scope by editing its ticket file. An issue body has no such protection, because anyone with write access can edit it. If agents have write access and you need the stronger guarantee, keep tickets as files.
