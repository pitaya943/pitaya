<!-- Design for one milestone, written by /design, saved as docs/milestones/M<n>-design.md. Use the document language from docs/agents/harness.md. Tickets are cut from the scenarios; /report M<n> checks every one. -->

# M<n> design: <title>

## Scenarios

<!-- One per observable behaviour, numbered. Each names the test that will prove it. -->

| ID | Given | When | Then | Proved by |
| --- | --- | --- | --- | --- |
| S-1 | <state before> | <action> | <observable result> | <test ID or command> |
| S-2 | <...> | <...> | <error path or edge> | <...> |

## Interfaces

<!-- Signatures, types, endpoints, events: what callers see. One supported way per task. -->

## Data flow

<!-- Where data enters, how it moves and is transformed, where it is stored. A diagram is welcome. -->

## Workflow

<!-- The order in which parts act for the main scenarios. -->

## Notifications

<!-- Events, messages, logs or alerts the milestone emits, who receives them and when. "None" if none. -->

## State owners

| State | Owner (one) | Who reads it |
| --- | --- | --- |
| <state> | <module> | <modules> |

## Shapes considered

1. **<shape A>:** <one paragraph>
2. **<shape B>:** <one paragraph>

**Chosen:** <A or B>, because <one owner per state, one way per task, least caller knowledge>.

## Open questions

<!-- Preference or product choices for the Owner, each with options and a recommendation. "None" if none. -->
