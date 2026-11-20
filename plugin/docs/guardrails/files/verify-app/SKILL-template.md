---
# pitaya template 0.1.1 · docs/guardrails/files/verify-app/SKILL-template.md
name: verify-<app>
description: Drive <app> the way a user would and capture evidence that a feature works. Used by /verify and /report when a change touches a user-facing feature. Covers <surface: the web UI, the CLI, the HTTP API>.
---

<!-- Copy to .claude/skills/verify-<app>/SKILL.md, fill in every section, and run it end to end once before calling it done. -->

# Verify <app>

## Launch

- Start: `<command>` (throwaway data only; never a shared or production system).
- Ready when: `<signal, such as a health URL answering 200 or a log line>`.
- Stop: `<command>`.

## Doctor

One read-only health check to run before the first drive and after any failed one: `<command and expected output>`.

## Drive

How to act as a user, with the real selectors, commands or requests: `<harness, such as Playwright, the CLI, curl>`. Each feature's recipe is in `features/README.md`, next to this file.

## Evidence

- What counts: a screenshot, a response body, a CLI transcript, a log excerpt, saved under `docs/evidence/<ticket>/`.
- Every claim names the feature and the step it proves.

## Cleanup

Stop only what Launch started. Never delete evidence.

## Helpers

<!-- Scripts under this directory, each executable and called from a section above. "None" if none. -->
