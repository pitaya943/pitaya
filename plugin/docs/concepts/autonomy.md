# Autonomy

The `Autonomy` field in `docs/agents/harness.md` says who may merge what. Whatever it says, only the Owner merges `main`.

| Setting | Who merges ticket PRs | Who merges `main` | When it fits |
| --- | --- | --- | --- |
| **Only the Owner merges `main`** (default) | The Owner, after reading the verdict | The Owner | Almost always. A person sees every change before it lands |
| **Agents merge ticket PRs into milestone branches; only the Owner merges main** | An agent, into `milestone/M<n>`, once CI is green and the verdict is PASS | The Owner, one milestone at a time | Level 3, when waiting for a person is the bottleneck and the prerequisites below hold |

The milestone branch is the blast radius (D44): a milestone that went wrong is thrown away, and `main` never saw it. pstack trusts its agents entirely; Matt Pocock's skills put a person on every PR. This sits between them: agents run a milestone on their own, and a person signs off each one.

## Prerequisites for agent merging

Agents merging their own work is safe only when the checks a person would make are mechanical:

1. Level 1 is fully in place: the tests check is required on `main`, and the hooks are installed. The required approval drops to 0 only together with requiring the `verdict` status (D37).
2. Level 2's merge checks are on, at least scope, read-only paths, no weakened tests and done-when, so an agent can't widen its task or remove the tests that judge it.
3. The verifier is a separate session or a different model, not a subagent of the builder.
4. Sensitive areas still go to the Owner: the agent escalates a ticket that touches one without a covering test, and the Owner sees every change when reviewing the milestone.
5. Someone reviews merged work afterwards, for example through `/report` and `/retro` on a fixed schedule.
6. Agents merge ticket PRs only into milestone branches. `main` changes only when the Owner merges a milestone, so the worst case is one milestone thrown away (D44).
7. Agents merge only through `/autopilot` or a builder that follows its merge rules: re-read the head commit, require PASS on it, and leave plan PRs and sensitive areas to the Owner.

If any of these stops holding, go back to the default.

## What doesn't change

Whatever the setting: nobody pushes directly to `main`, nobody force-pushes it, and the verifier never merges the work it verified.
