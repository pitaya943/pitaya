---
name: design
description: Design a milestone before it is cut into tickets. Write its behaviour scenarios (Given / When / Then), then work backwards to the interfaces, data flow, notifications and state owners that make them true, comparing two shapes and picking by ownership. Level 2 and up; the tickets come from the scenarios.
disable-model-invocation: true
argument-hint: "M<n>"
---

# Design a milestone

Adapted from pstack's `/architect`, with behaviour-driven scenarios. The design is the milestone's contract: tickets are cut from its scenarios, parallel builders share its interfaces, and `/report` checks every scenario at the end.

## Before you start

1. Read `docs/agents/harness.md`. If it's missing, suggest `/setup` once and continue.
2. Read `docs/milestones/M<n>.md` (goal, exit criteria, what's left out), `docs/agents/architecture.md`, the glossary and `learnings.md`.
3. Explore how and why the code the milestone touches works today, as in the `plan` skill's `sharpen.md`.

## Write it

Use [design-template.md](design-template.md); save it as `docs/milestones/M<n>-design.md`, in the document language.

1. **Scenarios first.** One scenario per behaviour a user or caller can observe, numbered `S-1`, `S-2`, and so on: Given (the state), When (the action), Then (the observable result). Cover each exit criterion, the error paths and the edges. A scenario nobody could test isn't a scenario.
2. **Work backwards.** From the scenarios, derive what must exist: the interfaces (signatures, types, endpoints, events), the data flow, the workflow between parts, the notifications, and which part owns each piece of state.
3. **Compare two shapes.** Trace every system the change touches, sketch two shapes, and pick the one where each piece of state has one owner, each task has one supported way, and callers know least. Record both and why one won. If workarounds keep piling up, redesign instead of patching. At Level 4, when the two shapes come out close or the Owner asks for alternatives, run the arena in [arena.md](arena.md).
4. **Map scenarios to tests.** Name, for each scenario, the test that will prove it (a test ID or a command). These become the tickets' done-when conditions.
5. **Open questions.** Choices of preference or product direction go to the Owner, with options. Don't decide them.

## Hand over

Show the Owner the scenarios and the chosen shape, and change them until the Owner agrees. Then commit the design on a `plan/<slug>` branch with the milestone's ticket cut (the `plan` skill, `milestones.md`), so one plan PR carries both. The Owner's merge approves the design and the cut together. In an unattended session (one `/autopilot` started) there is nobody to show: write each open question and the answer you assumed into the design, and go on to the cut. The Owner then judges the design in the plan PR, or at Level 4 at the milestone's sign-off.

## Don't

- Don't write product code or tests while designing.
- Don't add behaviour the milestone's goal doesn't ask for, or anything under its "Not in this milestone".
- Don't change a public interface or data model the request didn't authorize: ask the Owner with the `ask-owner` skill.
