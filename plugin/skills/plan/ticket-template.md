<!-- Ticket body written by /plan. Use the document language from docs/agents/harness.md. Delete optional sections that don't apply.
File tickets (docs/tickets/T-<nnn>.md) start with the title and the Status line; add the Issue line when the ticket has an issue mirror. Issue-only tickets start at "## Goal". -->

# T-<nnn>: <title>

Status: open
Milestone: M<n>
Risk: low
Issue: #<n>

## Goal

<one or two sentences: what someone can do once this is merged>

## Done when

<!-- Check every worked example (an input and its expected result) by computing or running it before writing it here. -->

1. <condition>, checked by `<test ID or command>`
2. <condition>, checked by `<test ID or command>`

## Scenarios

<From Level 2: the design's scenarios this ticket makes true, such as "Scenarios: S-<n>, S-<m>"; each is also a done-when condition. Delete below Level 2.>

## Depends on

<"None", or one "Blocked by <ticket>" line per ticket: "Blocked by T-002" for file tickets, "Blocked by #<n>" for issue-only tickets>

## Scope

- `<path or glob>`

## Assumptions

<what the plan assumed and the Owner may correct; "None" if none>

<!-- Level 2 fields: only when the matching guardrail is listed under "Guardrails" in the harness file.

## Test IDs

<one test ID per done-when condition, in order, as JUnit reports it (`classname::name`, for pytest `tests.test_cli::test_x`) or as a pytest path (`tests/test_cli.py::test_x`). An ID without `[...]` covers every parametrized case of that test; all of them must pass.>

## Serial resources

<shared resources only one ticket may change at a time, such as a migration or a lockfile>

## Append-only files

<files this ticket may only add lines to>

## Screenshots

<required or not required>
-->
