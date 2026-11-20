# Sharpen the brief, then explore

Adapted from pstack's `/sharpen`, `/how` and `/why`. Do this before cutting a roadmap, and before cutting a milestone whose goal is still vague.

## Sharpen

Make the task deeper, not bigger. Answer four questions in a few lines each, then rewrite the request as a brief:

1. **What would a top professional do beyond the ask?** The checks, edge cases and quality bar someone who does this for a living would add without being told.
2. **What is the rawest starting material?** The real data, logs, spec or user story, rather than a summary of them.
3. **Which specific methods and tools?** Name them: the library, the protocol, the test approach.
4. **What besides the agent would verify the result?** A command, a dataset, a person, a running app. If nothing can, say so: that's a risk for the plan.

Choices an experiment can settle, prototype and recommend. Choices of preference or product direction stay with the Owner: list them as questions. Show the brief to the Owner before drafting milestones or tickets; it becomes the roadmap's goal.

## Explore how and why

For an existing codebase, two read-only passes before planning:

- **How:** start one read-only subagent to explain how the parts the request touches work today: entry points, data flow, where state lives. Use its answer to name modules the way the code does.
- **Why:** read the commits and pull request discussions that introduced those parts and later changed them. Note decisions the plan must respect, cite where each comes from, and mark what's inferred. When the history doesn't say, write that down instead of guessing.

Put anything the plan depends on into `docs/agents/architecture.md` or the glossary, as `/plan` already does.
