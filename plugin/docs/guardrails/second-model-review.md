# Recipe: second-model review

Level: 3. No files to copy: a verification setting and a habit.

## What it guards against

Shared blind spots. A fresh subagent of the same model reads the work cold, but it shares the builder's training, so it tends to miss the same things the builder missed.

## When it's worth adding

For pull requests that touch a sensitive area from the harness file, change a public interface or data model, or would be expensive to get wrong. It's also needed before [agent-merge](agent-merge.md).

## How to add it

1. In `docs/agents/harness.md`, set "Verification" to name a different model, or a different vendor's agent, for those pull requests. For example: "a separate session with a different model for PRs touching sensitive areas; a fresh subagent otherwise".
2. `/verify` then gives the pointers as a prompt for that session instead of dispatching a subagent, and the verdict's "Model" line shows which model judged.
3. Keep the checklist the same. The point is a second pair of eyes, not a different standard.

## How to prove it works

On one past PR that touched a sensitive area, run the second model's verification and compare its verdict with the first. Over a few PRs, count the problems only the second model found. If it finds none, this recipe isn't paying for itself.

## Cost and false positives

- A second model's time and cost for each of those PRs.
- Two models can disagree on style. The checklist keeps the verdict to behaviour and evidence.
- Two models can still be wrong together.

## Error message

There's no check to fail. The verdict comment names the model; if it names the builder's model for a PR that needed a second one, the Owner sends it back.

## Afterwards

Record under "Guardrails" in the harness file which pull requests get a second model, and which model.

## When to remove it

When a few months of comparisons show the second model finds nothing the first one misses.
