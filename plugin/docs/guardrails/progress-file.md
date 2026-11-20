# Recipe: progress file

Level: 3. Files: [`progress.md`](files/progress-file/progress.md), [`features.json`](files/progress-file/features.json), [`check_feature_list.py`](files/progress-file/check_feature_list.py), [`progress-file.yml`](files/progress-file/progress-file.yml).

## What it guards against

Long work falling apart between sessions: a new session redoing finished work, building on a broken state, declaring the whole job done after one feature, or quietly deleting requirements until what exists satisfies them.

## When it's worth adding

When one piece of work spans many sessions, or agents work for hours without a person in the loop. For work that fits in a few sessions, `/handoff` is enough.

## How to add it

1. Copy `files/progress-file/progress.md` to `docs/progress/progress.md`. Every session follows its start-up routine and adds a log entry before it ends.
2. Have the Owner write the requirements into `docs/progress/features.json`, shaped like `files/progress-file/features.json` (the JSON template carries no version header; this recipe is version 0.1.3). Every feature starts with `"passes": false`.
3. Add one line to `AGENTS.md`: "For long-running work, follow the start-up routine in `docs/progress/progress.md`, and work on one feature from `docs/progress/features.json` at a time."
4. Copy `files/progress-file/check_feature_list.py` to `.github/guardrails/` and `files/progress-file/progress-file.yml` to `.github/workflows/`. Then make `progress-file` a required check.

The files live in `docs/progress/`, not `docs/agents/`: the read-only check protects `docs/agents/**`, and sessions must be able to add to the log and flip `"passes"`. With the scope check on, `/plan` adds `docs/progress/progress.md` and `docs/progress/features.json` to each ticket's Scope. The check runs on every pull request, so it can be required; it passes at once when the feature list didn't change.

This follows Anthropic's harness for long-running agents, which keeps the requirements in JSON rather than Markdown because models are less likely to rewrite structured data.

## How to prove it works

In a PR opened by the machine account, change one feature's description, or delete a feature. The check fails and names it. Flip only `"passes"` to `true`, and it passes.

## Cost and false positives

- A start-up routine at the beginning of every session, about a minute.
- The Owner writes the requirements up front.
- A requirement that really was wrong needs the Owner's own PR to change it. That's intended, but it adds a step.

## Error message

```text
FAIL progress-file: the feature list changed beyond "passes":
  F-2: removed
To fix: restore the features as they were and change only "passes". If a requirement really is wrong or missing, ask the Owner to change the list in their own pull request.
```

## Afterwards

Add `progress-file` under "Guardrails" in `docs/agents/harness.md`, and mention `docs/progress/progress.md` in the AGENTS.md map.

## When to remove it

When the work isn't long-running any more, or when sessions reliably keep requirements intact without it.
