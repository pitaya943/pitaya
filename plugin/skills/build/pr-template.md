<!-- PR description for /build. Write it in the document language from docs/agents/harness.md. Keep the headings; write "None" for an empty section. -->

## What was done

Ticket: <link or path>. Completion conditions: <n>, all met.
<For a file ticket with an issue mirror: "Closes #<n>". Its Status line changes to done in this PR.>

<two or three sentences on the change>

## How to verify

```bash
<command to run the tests>
```

Expected: <what passes, how many tests>.

## Evidence

<!-- One entry per completion condition, in the ticket's order: the command and its output, or a screenshot path under docs/evidence/<ticket>/. Then the red output from before the fix. -->

1. <condition> — <command and output>

Red before green:

```text
<failing output>
```

## Decision log

<!-- Keep this as you work, newest last, so whoever merges sees why the code looks the way it does. Add rows; never edit or delete one: correct a row with a new row. Log choices between real alternatives, dead ends and failed attempts with what they showed. "Evidence" is a pointer (a commit, file:line, a command's output above), not prose. "Result" is a state: kept, reverted, failed, open. Fill in "Options" only when there were two or more real ones, and name each, so /retro can later see what else was on the table; otherwise write "-". Skip the obvious. -->

| When | Decision | Options | Why this one | Evidence | Result |
| --- | --- | --- | --- | --- | --- |
| <time> | <what you chose, or tried> | <the alternatives you weighed, or -> | <the reason it beat them> | <commit, file:line or output> | <kept, reverted, failed, open> |

## Assertions stricter than the spec

<!-- Each assertion that checks more than the spec asks for, or "None". -->

## Scope

<!-- git diff --stat <base>...HEAD -->

## Open questions

<!-- Spec questions, follow-up work, and proposed learnings or glossary terms for docs/agents/. "None" if there are none. -->
