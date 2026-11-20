# Layout: a full project's repository

What a project at Level 3 or 4 looks like once pitaya is in place. Lower levels have a subset: Level 1 stops at the files `/setup` copies, and the recipes add the rest one by one. The marker on the right says which layer each part belongs to (see [Access](access.md#two-layers)): **C** is the control plane, the rules and the plan; **D** is the data plane, the product and what work leaves behind.

```text
my-project/
├── AGENTS.md                     C  /setup: the map, how to run the tests, done means, never
├── CLAUDE.md                     C  /setup: imports AGENTS.md
├── .claude/
│   ├── settings.json             C  /setup: secrets denied, hooks wired in
│   ├── hooks/
│   │   ├── no_push_main.py       C  /setup
│   │   ├── no_destructive.py     C  /setup
│   │   ├── ask_on_rule_files.py  C  /setup
│   │   ├── ask_on_merge.py       C  /setup
│   │   └── shell_words.py        C  /setup: the parser the four hooks share
│   └── skills/verify-<app>/      C  verify-app recipe: drives the real app
├── .github/
│   ├── workflows/
│   │   ├── tests.yml             C  /setup: runs the test script on every PR
│   │   └── <recipe>.yml          C  one per guardrail recipe: scope, read-only-paths, ...
│   ├── scripts/test.sh           C  /setup: the test command, the one place it is written
│   ├── guardrails/               C  the recipes' check scripts
│   └── CODEOWNERS                C  multi-account recipe only
├── docs/
│   ├── agents/
│   │   ├── harness.md            C  /setup: level, Owner, accounts, autonomy, tickets
│   │   ├── glossary.md           C  /plan: the project's words
│   │   ├── architecture.md       C  /plan: the module map
│   │   └── learnings.md          C  /retro: lessons, append only
│   ├── decisions.md              C  Owner and Chief: decisions, append only
│   ├── adr/<nnnn>-<slug>.md      C  big decisions with real options
│   ├── milestones/
│   │   ├── M<n>.md               C  /plan --roadmap: goal, exit criteria, Status
│   │   └── M<n>-design.md        C  /design: scenarios, interfaces, state owners
│   ├── tickets/T-<nnn>.md        C  /plan M<n>: Status, scope, done when, test IDs
│   ├── progress/                 D  progress-file recipe: log and feature list
│   ├── handoff/<branch>.md       D  /handoff
│   ├── evidence/<ticket>/        D  /build: screenshots and output; /verify's are on an evidence/ branch
│   └── reports/                  D  /report, when the Owner wants files
├── src/                          D  the product, changed only inside a ticket's scope
└── tests/                        D  the product's tests, red before green
```

## Branches

| Branch | Holds | Merged by |
| --- | --- | --- |
| `main` | Everything signed off | The Owner, always |
| `milestone/M<n>` | The active milestone's merged tickets, at every level | The Owner merges it into `main`: the sign-off |
| `ticket/<id>-<slug>` | One ticket's work | Into `milestone/M<n>`: the Owner below Level 3, the Chief from Level 3 |
| `plan/<slug>` | A roadmap, a design, a cut or a milestone's report: plan files only | The Owner, into `main`. Into a milestone branch: the report PR (`plan/M<n>-report`) merges like a sync PR, with no verifier, and at Level 4 the Chief merges a cut into the next milestone branch |
| `sync/<slug>` | `milestone/M<n>` with `main` merged in, and nothing else: how a milestone gets what `main` gained | Into `milestone/M<n>`, like a ticket PR: the Owner below Level 3, the Chief from Level 3 |
| `setup/<slug>` | What `/setup` installed or updated: rule files, hooks, the harness file | The Owner, into `main` |
| `evidence/<PR>-<short sha>` | A verifier's screenshots for one head of one pull request, under `docs/evidence/<ticket>/verify/` | Nobody: it has no pull request. The verdict links its files, and the Owner may delete it once the milestone is signed off |

## Where pitaya itself sits

In pitaya's own repository the split is different: `plugin/` is the product that ships to users, and everything else (`docs/design.md`, `tests/`, `scripts/`, `evals/`) is for developing it. The marketplace installs `plugin/` alone.
