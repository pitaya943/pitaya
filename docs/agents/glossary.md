<!-- pitaya template 0.1.0 · docs/agents/glossary.md -->
# Glossary

The project's own words, so people, agents and code use the same name for the same thing. Use these terms in tickets, code, tests and PRs. When a word under "Avoid" comes up, use the term instead.

`/plan` adds terms when planning settles a new one. Ticket PRs propose changes in their description instead of editing this file.

| Term | Meaning | Avoid |
| --- | --- | --- |
| harness | The skills, files and checks that let agents develop under human review | framework, SOP |
| level | One of four steps of protection (0 to 3); each includes the one before | tier, stage |
| recipe | A guardrail document in eight sections, with copyable files | guide, playbook |
| guardrail | A protection added from a recipe, usually a check or a setting | gate (a gate blocks everything; there is none) |
| harness file | `docs/agents/harness.md` in a user's project, the config every skill reads first | config file, settings |
| template | A file in `plugin/templates/` that `/setup` copies into a project | scaffold, boilerplate |
| ticket | One verifiable vertical slice of work, with done-when conditions | task, story |
| verdict | The verifier's PASS or FAIL comment for one head commit | review, approval |
| machine account | The GitHub account agents act and commit as | bot user |
| Owner | The person who approves plans and, by default, merges `main` | admin, maintainer |
| component | One selectable part of the harness in `components.json`: a skill, a group of template files, the harness file or a recipe | module, plugin, feature |
| preset | A level used as a starting selection: every component at or below it | profile, bundle |
| ticket mirror | A GitHub issue that links to a `docs/tickets/T-<nnn>.md` file, for discussion and notifications; the file stays the source of truth | linked issue, copy |
