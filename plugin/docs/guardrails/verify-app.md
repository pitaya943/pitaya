# Recipe: verify the real app

Level: 2. Files: [`SKILL-template.md`](files/verify-app/SKILL-template.md), [`feature-template.md`](files/verify-app/feature-template.md).

Adapted from pstack's `/create-verification-skill` and `/maintain-verification-skill`.

## What it guards against

"All tests pass, but the feature is broken": the tests check the parts, nobody drives the whole app the way a user would, and a verifier with no recipe can't either.

## When it's worth adding

When the project has a user-facing surface (a UI, a CLI, an API) and a change has once passed every test while the feature didn't work. From Level 2, where several builders change the same app.

## How to add it

1. **Interview the repository.** Find the surface, the run command, a way to drive it (Playwright, the CLI, HTTP requests), what counts as observable evidence, and how to run it in isolation with throwaway data. Ask the Owner only for what you can't observe.
2. **Generate the skill.** Copy `files/verify-app/SKILL-template.md` to `.claude/skills/verify-<app>/SKILL.md` and fill in Launch, Doctor, Drive, Evidence, Cleanup and Helpers.
3. **Seed the feature map.** Add `features/README.md` as the index and one file per feature from `files/verify-app/feature-template.md`, starting with the 3 to 5 features users rely on most.
4. **Run it end to end once:** launch, doctor, drive one feature, capture evidence, clean up, and check the evidence survived. A verification skill that was never executed is a draft, not a deliverable. Anything you could only do in a stand-in environment is listed as unverified.
5. Add it through a pull request: it lives under `.claude/`, which is rule work.

## How to prove it works

Break a user-facing feature in a way its unit tests don't cover (a wrong route, a missing button handler). `/verify` drives the feature with the skill and reports FAIL with the evidence.

## Cost and false positives

- Launching and driving the app adds minutes to each verification of a user-facing change.
- The feature map goes stale as the app changes. Audit it now and then: for each feature, compare the recipe with the source, drive every feature once, fix what drifted in the skill's own directory only, report broken app behaviour instead of documenting it, and open at most one PR. The outcome is clean, changed or blocked.

## Error message

The verifier's FAIL names the feature, the step that failed and the evidence: "FAIL: <feature>, step <n>: expected <x>, saw <y> (docs/evidence/<ticket>/<file>)". The verifier's own screenshots are not on the pull request's branch: the verdict links them on its `evidence/<PR>-<short sha>` branch (the `verify` skill).

## Afterwards

Record `verify-app` under "Guardrails" in the harness file, with the skill's path.

## When to remove it

When the project no longer has a user-facing surface, or when an end-to-end suite in CI drives every feature in the map.
