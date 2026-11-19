# Recipe: serial resources

Level: 2. Files: [`check_serial.py`](files/serial-resources/check_serial.py), [`serial-resources.yml`](files/serial-resources/serial-resources.yml).

## What it guards against

Two pull requests that are each correct but break once both merge, because they change the same shared resource: two database migrations with the same sequence number, two lockfile updates, two changes to one generated schema.

## When it's worth adding

When agents work in parallel and the project has such a resource, or after the first collision.

## How to add it

1. Name the project's serial resources (for example `migrations`, `lockfile`) and set them in `SERIAL_RESOURCES` in the workflow.
2. Tickets that change one list it under "## Serial resources". `/plan` writes this when the guardrail is listed in the harness file.
3. Copy `files/serial-resources/check_serial.py` to `.github/guardrails/check_serial.py`.
4. Copy `files/serial-resources/serial-resources.yml` to `.github/workflows/serial-resources.yml`.
5. After the first run, make `serial-resources` a required check.

The workflow collects the tickets of every other open PR and fails if any of them claims the same resource. It also fails on a resource name it doesn't know, so a typo can't slip past.

## How to prove it works

Open two ticket PRs whose tickets both list `migrations`. The second one's check fails and names the first. Merge or close the first, re-run the second, and it passes.

## Cost and false positives

- One API call per open PR, so it gets slower with many open PRs.
- A ticket that lists a resource it doesn't touch blocks others for nothing. `/plan` and the verifier should keep the lists honest.
- The check sees open PRs only. Two branches claiming the same resource before either has a PR aren't caught, so plan around it.

## Error message

```text
FAIL serial-resources: another open pull request is changing the same resource:
  migrations: also claimed by pr-41
To fix: wait until that pull request merges or closes, then update this branch and re-run.
```

## Afterwards

Add `serial-resources` under "Guardrails" in the harness file, with the resource names.

## When to remove it

When the resource can't conflict any more, for example migrations get timestamped names and a merge queue merges PRs one at a time.
