# Recipe: second-model review

Level: 4. No files to copy: a verification setting, and for the external options an account and a secret.

## What it guards against

Shared blind spots. A fresh subagent of the same model reads the work cold, but it shares the builder's training, so it tends to miss the same things the builder missed.

## When it's worth adding

At Level 4, for pull requests tagged `Risk: high` and for the milestone audit (see [deep-verification](deep-verification.md)), which uses it. Also on its own, for pull requests that would be expensive to get wrong.

## How to add it

The second model is a swappable adapter: the "Second model" line in `docs/agents/harness.md` names it, and `/verify` and `/report` call whatever it names. Whatever it is, **only findings our own run reproduces count**: an outside model proposes, a run proves.

| Value | What it uses | Setup | Cost and caveats |
| --- | --- | --- | --- |
| `claude:<model>` (default) | A subagent on a different Claude model from the builders' | None | The cheapest; the same vendor, so some blind spots stay shared |
| `cursor-cli:<model>` | Cursor's CLI in print mode, `agent -p --model <model>`, which can run other vendors' models | Install the CLI; sign in, or set `CURSOR_API_KEY` for CI | A Cursor plan. Print mode can write files, so run it in a throwaway worktree, and give it a timeout: some versions have hung in print mode. The code goes to Cursor |
| `bugbot` | Cursor Bugbot, a GitHub app that reviews pull requests on each push or when someone comments `bugbot run` | Install it from the Cursor dashboard; needs Cursor and GitHub organization admin rights | A Cursor plan. Its check doesn't block merging on findings by default, so our verdict does: the verifier reproduces each Bugbot comment or drops it |
| `grok-action` | A GitHub Action that reviews pull requests with xAI's Grok, such as a community review action configured with `XAI_API_KEY` | Add the action in a workflow of its own, and the key as a repository secret (below) | xAI API usage. Community actions, not an official xAI bot: read the action before adding it. The code goes to xAI |

A third-party review action is someone else's code holding your API key, so keep what it can reach small. Give it a workflow of its own, with nothing else in it: `permissions:` set to `contents: read` and `pull-requests: read` (add `pull-requests: write` only if it must comment), the action pinned by commit ([Pinned actions](README.md#pinned-actions)), and no other secret than its own key. Never add it as a step in a workflow that runs your checks, where it would share their token.

Then record the value in the harness file and keep the checklist the same: the point is a second pair of eyes, not a different standard.

## How to prove it works

On one past pull request that touched a sensitive area, run the second model and compare what it found with the first verifier's verdict. Over a few pull requests, count the problems only the second model found and our run reproduced. If it finds none, this recipe isn't paying for itself.

## Cost and false positives

- A second model's time and cost for each high-risk pull request, plus a plan or API usage for the external options.
- Outside models raise style points and guesses; the reproduce-or-drop rule keeps them out of the verdict.
- Two models can still be wrong together.

## Error message

There's no check to fail. The verdict's "Interrogate" section names the second model and lists its findings and what was dropped.

## Afterwards

Record the "Second model" value in the harness file, and under "Guardrails" which pull requests get it.

## When to remove it

When a few months of comparisons show the second model finds nothing the first one misses.
