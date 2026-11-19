# Autonomy

The `Autonomy` field in `docs/agents/harness.md` says who may merge into `main`.

| Setting | Who merges | When it fits |
| --- | --- | --- |
| **Only the Owner merges `main`** (default) | The Owner, after reading the verdict | Almost always. A person sees every change before it lands |
| **Agents merge after CI is green and the verdict is PASS** | An agent | Level 3 only, when waiting for a person is the bottleneck and the prerequisites below hold |

## Prerequisites for agent merging

Agents merging their own work is safe only when the checks a person would make are mechanical:

1. Level 1 is fully in place: the `ci` check is required on `main`, and the hooks are installed.
2. Level 2's merge checks are on, at least scope, read-only paths, no weakened tests and done-when, so an agent can't widen its task or remove the tests that judge it.
3. The verifier is a separate session or a different model, not a subagent of the builder.
4. Sensitive areas still go to the Owner: a PR that touches one needs a person's merge.
5. Someone reviews merged work afterwards, for example through `/report` and `/retro` on a fixed schedule.

If any of these stops holding, go back to the default.

## What doesn't change

Whatever the setting: nobody pushes directly to `main`, nobody force-pushes it, and the verifier never merges the work it verified.
