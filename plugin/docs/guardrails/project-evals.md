# Recipe: project evals

Level: 4. Files: [`task-template.md`](files/project-evals/task-template.md).

## What it guards against

Changing the harness on impressions. A new skill version, a longer AGENTS.md, a different model or a new hook can make agents better or worse, and without measurements nobody knows which.

## When it's worth adding

When you're about to change how agents work in the project (instructions, skills, hooks or models), and you've collected a few real failures worth not repeating.

## How to add it

1. Create `evals/` in the project.
2. For each task, copy `files/project-evals/task-template.md` and fill it in from a real failure or success. Start with 20 to 50 small tasks; Anthropic's guidance on agent evals suggests that size.
3. Grade outcomes, not the path taken. Use tests and scripts before judgement.
4. Run the set before and after each change, each run in a clean checkout. Log the scores in `evals/results.md`.
5. Read the transcripts of the tasks that changed result. The numbers say whether; the transcripts say why.

## How to prove it works

Make a change you expect to hurt, such as removing a line from a skill that a task depends on, and run the set. The score should drop on that task. If it doesn't, the task doesn't measure what you think.

## Cost and false positives

- Building the set takes time, and each run costs agent time and money.
- A small set gives noisy scores: rerun a task before trusting a single change in its result.
- A task that's too easy passes every time and tells you nothing; retire it.

## Error message

There's no CI check by default. The output is a row in `evals/results.md`: date, task, harness version, model, score and notes.

## Afterwards

Note in the harness file that harness changes are measured against `evals/`, and link the latest results from `/report`.

## When to remove it

Never entirely while the harness keeps changing. Retire individual tasks that always pass.
