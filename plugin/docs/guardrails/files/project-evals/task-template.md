<!-- pitaya template 0.1.3 · docs/guardrails/files/project-evals/task-template.md -->
# Eval task: <short name>

Drawn from: <the real failure or success this comes from, with a link>

## Starting state

- Repository: <a commit, tag or branch to start from>
- Setup: <commands to get it running>
- Harness: <level and settings that matter>

## Prompt

<exactly what the agent is told, for example "Run /build on ticket.md">

## Grading

Outcomes only, each checkable without reading the transcript first. Tests and scripts come before judgement.

- [ ] <outcome, for example: all ticket tests pass in a clean checkout>
- [ ] <outcome, for example: no test was deleted or skipped>
- [ ] <outcome, for example: the PR has evidence for every condition>

## Notes

<what to look for in the transcript, known traps>
