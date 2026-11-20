# Changelog

Changes are grouped by what users copy or install: skills, templates and recipes.

## 0.1.9 (2026-11-20)

The fifth batch of fixes from the review of 0.1.4: duplication and maintenance (D69, D70). F26, F27, F28 and F32, plus the gaps the verdict on 0.1.7 found in the Level 4 cut and the report PR.

**If you upgrade:**

- Re-run `/setup`. It creates `.claude/hooks/shell_words.py`, which the four hooks now import, and `.github/scripts/test.sh` with the test command you pass; it reports the hooks, `tests.yml` and `AGENTS.md` as stale or different, as always. Update the four hooks together with the new module: a 0.1.9 hook without `shell_words.py` lets every call through and says so on stderr.
- Point your own copies at the script: `run: sh .github/scripts/test.sh` in `tests.yml`, and the same in `AGENTS.md` and the harness file's "Test command". The old allow rule `Bash(<your command>)` in `.claude/settings.json` is harmless; remove it if you like.
- If you copied `done-when.yml` or `no-weakened-tests.yml`: they no longer have `TEST_COMMAND`. Make the command in `.github/scripts/test.sh` write JUnit XML when `JUNIT` is set, for pytest `python -m pytest -q ${JUNIT:+--junitxml="$JUNIT"}`. On the pull request that brings the script in, `no-weakened-tests` fails once, because the base branch has no script to run; the Owner merges that one.
- Add the release tag where you add the marketplace, on your machine and in a cloud environment's setup script: `claude plugin marketplace add <owner>/pitaya#v0.1.9`. Without it you follow the default branch.
- Copy each recipe's workflow and check again if you use it: the shared "Find the ticket" step changed in all of them.

### Templates

- **`.claude/hooks/shell_words.py`, new (F27).** The four hooks each carried a copy of the code that splits a Bash command into the programs it runs, and the copies had drifted: `ask_on_rule_files.py` didn't look inside `bash -lc '...'` and didn't see past `sudo`, `env` or a leading `VAR=value`, so `sudo rm AGENTS.md` raised no question. The hooks now import one module. It isn't a hook and `.claude/settings.json` doesn't run it. The hooks write no `__pycache__` next to themselves.
- **`.github/scripts/test.sh`, new (F32).** The project's test command, in the one place it is written. `tests.yml`, `AGENTS.md` and the allow rule in `.claude/settings.json` now run `sh .github/scripts/test.sh` where each used to hold its own copy of the command. The script is under `.github/`, so the rule-file hook asks before an agent edits it and `read-only-paths` keeps ticket PRs from changing it. `/setup` never overwrites it: to change the command, edit the script.
- `tests.yml`: its action is pinned by commit, with the release in a comment, and the comment that suggests a setup step shows it pinned (F28).

### Recipes

- **`serial-resources` (F26).** Of two pull requests that claim one resource, the one with the lower number goes first and the later one waits. Before, each listed the other and both failed, so under autopilot two tickets waited on each other. The other pull requests' tickets are now found by the same lookup as the pull request's own, from the base branch: the workflow's second, different `find_ticket` is gone, and a pull request whose ticket is done or closed no longer holds a resource. The check's glob helper now reads `?` as the scope check does. The error message says the earlier pull request goes first. An earlier pull request whose issue ticket can't be read fails the check instead of dropping its claim.
- **The shared "Find the ticket" step (F27)** has one lookup, `ticket_of`, in all seven workflows; the pull request's own issue ticket, when it can't be read, fails with a reason; and every `gh pr list` asks for up to 1000 pull requests instead of gh's default of 30.
- **`done-when`, `no-weakened-tests` (F32):** the test jobs run `sh .github/scripts/test.sh` with `JUNIT` set; the `TEST_COMMAND` variable is gone. The base job of `no-weakened-tests` runs the base branch's copy of the script.
- **All workflows (F28):** actions are pinned by commit, with the release in a comment. `README.md` has a new section, "Pinned actions", on why, how to pin a step you add, and how Dependabot keeps the pins current.
- **`agent-merge`, the `verdict` check** (D69; the verdict on 0.1.7):
  - a Level 4 **cut** can't set its milestone to `Status: done`, with or without a rider: only the report PR closes a milestone, and it checks that no ticket is open. A pull request that mixed a report with a new, open ticket used to pass as a cut;
  - a cut changes no plan file that exists except its own milestone file, the glossary, the architecture map and `docs/decisions.md`. An existing report or ADR used to be open to it; a cut that supersedes an ADR now waits for the Owner;
  - the **report PR**'s open-ticket test reads the tickets from the merge result, so a report branch made before a ticket was added no longer passes; a report branch that conflicts with its base doesn't pass;
  - in a report PR only exactly `Status: done` counts as done, for the milestone and for its tickets: `Status: done, criteria waived` waits for the Owner. The ticket checks still read any `Status: done...` as done, so nobody builds on such a ticket;
  - only the Level 4 Autonomy value the harness template offers lets a cut merge (any case or quoting). A hand-written "Agents merge ticket PRs, never plan PRs, ..." used to count as Level 4.
- `second-model-review`: a third-party review action goes in a workflow of its own, with read-only permissions, pinned by commit, and no other secret than its own key (F28).
- `verify-app`: the skill template says that a verifier's screenshots go to `evidence/<PR>-<short sha>`, never on the pull request's branch.

### Skills

- `setup`: passes the test command to the install, which writes it into `.github/scripts/test.sh`; the harness file records `sh .github/scripts/test.sh`. With no test command yet it passes `false`, so the script and the `tests` check fail until someone fills it in. Setup steps added to `tests.yml` are pinned by commit, and the script is run once before the PR.
- `build`: a push rejected because the branch moved isn't always a takeover. After "Update branch" on the pull request the builder merges the fetched branch in and pushes again; it stops only at another builder's commits.
- `autopilot`: a pull request whose only red check is `serial-resources` waits for the earlier pull request and gets no CI retry. `tick.md` describes a cut as the check now judges it, and says that only the `build` skill's rule keeps a slow builder and its takeover apart on one branch: no check does.

### Docs

- `README.md`: the install commands name the release tag, `<owner>/pitaya#v0.1.9`, and say how to upgrade (F28).
- `concepts/states.md`, `concepts/layout.md`, `concepts/access.md`, `guardrails/read-only-paths.md`, `levels.md`: the test script, the shared hook module, and the serial-resources wait.
- The harness template's Autonomy note says that either agent-merge value also covers sync PRs and the report PR, and that the Level 4 value is read word for word.

## 0.1.8 (2026-11-20)

The fourth batch of fixes from the review of 0.1.4: skill logic and autopilot (D62's answer to Q9, D68). Only skills, concept pages and two templates changed. No check, hook or workflow changed beyond its version header, so `/setup` reports the copies as stale while their content is the same.

**If you upgrade with autopilot running:** start `/pitaya:autopilot M<n>` once by hand, so the tracking issue gets a `Run started` line, and add `wake` to the command a schedule or a GitHub Action uses (`/pitaya:autopilot M<n> wake`). A session started with `wake` continues a run, and starts one only after the Owner merged the pull request the run was waiting for. Re-run `/setup` to see the new "Branches" line of `AGENTS.md`: it grants `evidence/<PR>-<short sha>`.

### Skills

- `verify`: the verifier pushes nothing to the pull request's branch. Its screenshots used to go there, which moved the head and voided the PASS it had just posted. They now go to a branch of their own, `evidence/<PR>-<short sha>`, made from the head it judged, with no pull request; the verdict links them.
- Fix rounds have one definition, the "Fix rounds" table in `concepts/states.md`, and `build`, `verify`, `autopilot`, `ask-owner` and `concepts/escalation.md` point to it:
  - a pull request's round is the number of FAIL verdicts on it; FAIL number "Fix rounds" + 1 (by default the third) escalates. `verify` used to recommend escalating "in the last round", which read as one fix where the harness promised two;
  - under `/autopilot` every fix round is a fresh session, and the verdict's "Next step" says so; when a person runs the work, round 1 may stay in the builder's session;
  - a red CI is not a round. Under `/autopilot` a red CI with no builder at work gets a CI retry, recorded by a comment on the pull request; after 2 in one round the tick escalates. Before, a persistently red CI restarted builders until the budget ran out.
- `autopilot`:
  - **start lines.** Before it starts a verifier, a fix round or a CI retry, a tick posts `Autopilot: <what> started for <head>` on the pull request; a claimed branch is listed under `Started:` on the tracking issue. A later tick starts nothing a start line says is at work (`tick.md`, "Sessions at work"). This replaces the rule that skipped a pull request "whose latest comment from autopilot is less than ten minutes old", which matched nothing, because autopilot never commented on pull requests;
  - **expiry.** A start line expires after 2 hours by default. An expired claim with no pull request is taken over by a fresh session on the same branch, so a builder, report or planning session that died no longer needs the Owner to delete a branch;
  - **the run.** A run goes from a `Run started` line on the tracking issue to the next `Stopped:` or `Waiting:`. The budget is counted from GitHub: the hours since that comment was created and the ticket pull requests merged since. A wait for the Owner's merge ends the run with `Waiting:`, and the tick that finds the merge starts the next, so the budget now covers one stretch of work between two of the Owner's merges. Before, every scheduled wake-up was a fresh session and so a new run, and the budget never ran out;
  - a ticket with an open `needs-owner` issue is left alone until the Owner answers, where before nothing stopped a tick from escalating it again; the same session that expires twice is escalated instead of started a third time;
  - **starting skills.** A new session's prompt is one slash command. A session that needs a second skill (the cut designs, then plans) and a subagent or background agent get the path of the skill's `SKILL.md` to read and follow, because the model can't invoke a user-invoked skill. `skills/README.md` states the rule that way;
  - it no longer asks for branch names when `AGENTS.md` grants them, and no longer "passes the permission on" to the sessions it starts: each reads the same grant.
- `build`: continues on a ticket branch that already exists, pushes after each commit, and stops when a push is rejected because another builder took the ticket over.
- `build`, `plan`: in a session with an assigned branch, use the "Branches" grant in `AGENTS.md` without asking. Only when it is missing, ask the user; when nobody is there, open a `needs-owner` issue and stop instead of waiting.
- `design`: an unattended session goes on to the cut by reading the plan skill's file.
- `setup`: commits on `setup/pitaya` (never on `main`), pushes and opens a pull request unless the user says not to.
- `report`, `verify`: say that the `AGENTS.md` grant covers the branches they push.

### Templates

- `AGENTS.md`: the "Branches" grant lists `evidence/<PR>-<short sha>`.
- The harness template: the "Fix rounds" line says where a round runs, and the "Autopilot" line names two new settings, CI retries per fix round (default 2) and claim expiry (default 2 hours).

### Docs

- `concepts/states.md`: the "Fix rounds" table; where a session at work, a claim's time and the run are stored.
- `concepts/layout.md`, `concepts/access.md`, the README's "Cloud sessions": the evidence branch, and what an unattended session does without the grant.

## 0.1.7 (2026-11-20)

The third batch of fixes from the review of 0.1.4: the branch and merge model (D62's answers to Q4 and Q8, D67). Level 4 could not run as written, and a milestone had two definitions of done.

**If you upgrade with a milestone in flight:** a milestone whose milestone PR was merged under 0.1.6 still says `Status: active` on `main`, because the plan PR that used to set it afterwards is gone. A plan PR into `main` sets it (`plan/milestones.md` allows this one repair; below Level 4 the next cut's plan PR can carry it), or change the line yourself.

### Recipes

- `agent-merge`, the verdict check. Copy `check_verdict.py` and `agent-merge.yml` again. A plan PR into a milestone branch used to stay red whatever happened, which blocked Level 4's cut behind a required status no verifier could ever turn green. It now passes without a verdict in two cases, each proved from the diff:
  - the **report PR** (`plan/M<n>-report` into `milestone/M<n>`): only the `Status:` line of `docs/milestones/M<n>.md`, set to `done`, and `docs/reports/M<n>.md`, and no ticket file with `Milestone: M<n>` still open;
  - a **cut** at Level 4: the Autonomy line of the harness file on the default branch lets agents merge plan PRs, and the PR changes only plan files, deletes nothing, adds tickets without changing one that exists, and changes no milestone file but its own.

  Any other plan PR into a milestone branch, a plan PR into the default branch and every milestone PR stay red: the Owner merges those. A FAIL on the head still blocks. This loosens a check: the recipe's "What it trusts" says what nobody verifies before the sign-off.
- The shared "Find the ticket" step, in all seven workflows: only the wording of one message changed (a plan PR into a milestone branch is for its report or a cut).
- `deep-verification`: set the Level 4 Autonomy value on the default branch, where the verdict check reads it; "How to prove it works" starts with a cut.

### Skills

- `report`: closing a milestone is two PRs in a fixed order. `/report M<n>` opens the report PR, which sets `Status: done` and adds the report inside the milestone branch; once it is merged, the milestone PR is opened. The Owner's merge of the milestone PR is the sign-off and brings `Status: done` to `main` in the same event. The "closing plan PR" after the sign-off is gone. A milestone that falls short gets a `needs-owner` issue, not a report PR.
- `plan`: `/plan M<n>` no longer sets the previous milestone to done, and cuts a milestone only once the one before it is done on `main`. "Closing a milestone" in `milestones.md` has the new steps.
- `autopilot`:
  - it reads a milestone's `Status:` and tickets on `milestone/M<n>` when that branch exists and on `main` only when it doesn't, so it finds a Level 4 cut, which exists only on the branch;
  - a milestone that is closing (`Status: done` on its branch, not yet on `main`) is finished before anything else, and `tick.md` has a new section, "Closing the milestone", where each step first looks for what an earlier tick left, so two wake-ups don't write two reports or open two milestone PRs;
  - with no active milestone the next cut comes first (`tick.md`, "The next cut"): below Level 4 a planning session opens the plan PR and the Owner merges it, at Level 4 autopilot merges it; a tick that ends waiting for the Owner's merge keeps a wake-up for it, where before every wake-up was cancelled once the tickets were done;
  - it claims the report and the cut by pushing their branch before it starts the session, as it does for tickets;
  - the only plan PRs it merges are the report PR and, at Level 4, the cut.
- `help` reads the milestone's state by the same rule and lists the report PR among what waits for the Owner below Level 3.
- `design`, `plan`: an unattended session, one `/autopilot` started, doesn't wait for an Owner who isn't in the conversation: it writes down what it would have asked and what it assumed, for the Owner to judge in the plan PR, or at Level 4 at the sign-off. New work for a Level 4 milestone goes in a plan PR into its branch.

### Docs

- `concepts/states.md` defines the four milestone phases by where `Status:` is read: planned, active, closing (done on the branch) and done (done on `main`). `concepts/autonomy.md` lists the Level 4 setting, which it had left out. `concepts/layout.md`, `access.md`, `roles.md` and the guardrails README say the same thing about who merges a plan PR.

## 0.1.6 (2026-11-20)

The second batch of fixes from the review of 0.1.4: the threat model written down where it applies (D59), mistakes surfaced for the Owner (D60), and the cheap guards (D62 to D65). pitaya assumes cooperating agents: read "What the levels assume" in `docs/levels.md` before using Level 3 or 4.

### Recipes

- `agent-merge`, the verdict check. Copy `check_verdict.py` and `agent-merge.yml` again; verdicts posted in the old form stop counting.
  - A verdict comment must start with the `## Verification:` heading and name the full 40-character head commit. Before, a comment that quoted a verdict counted, and so did a 7-character prefix.
  - A PASS needs a `Session:` line, and doesn't count when that session is one a `Builder session:` line on the pull request names: a verdict posted from a session that built the work doesn't pass it. This catches an honest mistake, not a false ID. Set the harness file's "Verification" to "a separate session" when you add agent-merge.
  - A FAIL is one-way. An edited FAIL still counts, and the workflow records each FAIL it sees in a `verdict-fail` status on the commit and reads it back, so deleting the comment no longer erases it. The workflow fails closed when it can't read or write that record.
  - A `Risk: high` ticket's PASS doesn't carry over "Update branch", and "Require branches to be up to date" on `milestone/*` is now a prerequisite, not an option (`protect-main` says so too).
  - Runs are serialised per pull request (a `concurrency` group), so an older run can't write its status after a newer one. The recipe says the status belongs to the commit, and has a new section, "What it trusts".
- The shared "Find the ticket" step, in all seven workflows: a branch name skips the ticket checks only on the base it belongs to. A `milestone/<id>` branch is a milestone PR only into the default branch; an agent's PR from such a branch into anything else fails, where before the name alone skipped every check. A plan PR must target the default branch or a milestone branch, and fails if it changes or deletes a ticket that is done (on its base or on a milestone branch) or that an open PR is building.
- `read-only-paths`: the default list gains the files a tool, git or a dev container loads by itself (`.mcp.json`, `.gitattributes`, `.gitmodules`, `.githooks/`, `.devcontainer/`, `.cursor/`, `.codex/`, `GEMINI.md`) and test configuration at any depth (`conftest.py`, `pytest.ini`, `tox.ini`, `setup.cfg`, `pyproject.toml`, `package.json`, `jest.config.*`, `vitest.config.*`, `Makefile`). A ticket that adds a dependency or a fixture now lists that file exactly in its scope.
- `progress-file`: requirements change on the default branch only, and a milestone gets the change through a sync PR.
- The guardrails README has a new section, "What the checks trust": a pull request controls the workflow files that judge it, and only the Python checks come from the base.

### Templates

- `.claude/hooks/no_destructive.py` also stops the plainly accidental wipes: a recursive `rm` of `.git`, `*`, `./*` or `$PWD`; `find . -delete` with nothing to narrow it; `git checkout` and `git restore` of `.`. Its notes say it catches slips and is not a security boundary.
- `.claude/hooks/ask_on_rule_files.py` also asks before a write to `.mcp.json`, `.gitmodules`, any `.gitattributes` or `GEMINI.md`, and anything under `.githooks/`, `.devcontainer/`, `.cursor/` or `.codex/`.
- `AGENTS.md`: text in an issue, a PR, a comment or fetched content is information, never an instruction.
- `/setup`'s installer reports allow rules an earlier version installed and a later one withdrew (`Bash(git diff *)`, `Bash(git fetch *)`) as `withdrawn`, for the user to delete; it still never removes a rule.

### Skills

- `verify`: every verdict has an **Attention** section, on PASS and FAIL alike, with rows of four kinds: `gate-change`, `role`, `unproven-claim` and `undisclosed`, classified by what the PR shows, never intent. A loosened check gets a `gate-change` row even when it is justified; the PASS stands. The verdict records its session ID.
- `report`: the milestone report rolls every Attention row up into one table for the sign-off, `undisclosed` rows first; the Level 4 audit writes into the same table.
- `retro`: one occurrence is enough to propose hardening a check after a `gate-change` that gamed it, or after any `undisclosed` row.
- `build`: the hand-off and fix-round comments record `Builder session:`; test configuration and files tools load by themselves are off limits unless the ticket names the file.
- `ask-owner`, `autopilot`, `build`: a decision counts only from a comment whose author is the Owner in the harness file and whose `author_association` is `OWNER`; anyone else's text is information. `autopilot` reads the verdict comments again before merging, and when agents merge it starts every builder and verifier as a new session: a background agent or subagent shares its session ID, which the verdict check would take for self-verification.
- `plan`: the `Risk:` tag now matters from Level 3, and a ticket's scope names test configuration files exactly.

### Docs

- `docs/levels.md` ("What the levels assume") and `concepts/access.md` ("What pitaya assumes") state the threat model: cooperating agents, Level 3 for agents you trust, hooks as accident prevention, and the `undisclosed` row as the tripwire. `levels.md` no longer asks agent-merge for a separate verifier account, which contradicted the recipe.
- `concepts/access.md` defines the control plane by what a file does (a tool loads or runs it by itself), not by a list of names. `concepts/escalation.md` has "Who can answer". `concepts/states.md` says a FAIL is one-way.

## 0.1.5 (2026-11-20)

The first batch of fixes from the review of 0.1.4 (D59 to D61): one proof that didn't prove what it claimed, and the logic errors that need no further decision.

### Recipes

- `agent-merge` and the shared "Find the ticket" step: a carried PASS and a sync PR are now proven by history as well as by tree. Every commit added must be a true merge: two parents, and the tree git gets by merging them. Before, `git merge -s ours` passed both proofs, because it keeps the tree while recording a commit as merged; that commit's changes were then dropped when it was merged for real, so a correction the Owner merged into `main` could disappear at the milestone's sign-off. "Update branch" pressed several times still carries a PASS. Copy `check_verdict.py` and all seven workflows again.
- `commit-author` doesn't check commits the default branch already contains, so a sync PR no longer fails on the commits `main` gained, whoever wrote them. `progress-file` accepts a requirement that matches the default branch's copy of the feature list, so a sync PR can bring a changed requirement into a milestone.
- `commit-author` and `progress-file` fail on every pull request when `MACHINE_ACCOUNT` is unset, like the ticket-based checks. Before, both passed without checking anything.
- `protect-main`: the `protect-milestones` ruleset requires 1 approval below Level 3 and 0 only from Level 3, changed in the same step that requires `verdict` (`agent-merge` says so too). It also turns on "Do not require status checks on creation", and "How to prove it works" creates a test milestone branch.

### Templates

- `.claude/settings.json`: `git diff` and `git fetch` are no longer allowed without a prompt. `git diff` prints any file once a path is outside the work tree, with or without `--no-index`, and `git fetch --upload-pack` runs a program and can be abbreviated, so denying option names doesn't hold for them. `git status`, `git log` and `git show` stay allowed, with deny rules for `--output` (the one option that makes them write a file) and, in case a project allows more itself, `--no-index`, `--upload-pack` and `--ext-diff`. `/setup` only adds rules: after re-running it, delete `Bash(git diff *)` and `Bash(git fetch *)` from your allow list by hand.
- `AGENTS.md`: the "Branches" grant lists `sync/<slug>`.

### Docs

- `sync/<slug>` is in `concepts/layout.md`, `concepts/states.md`, the guardrails README and `/help`.
- `concepts/states.md` and `concepts/roles.md` no longer contradict the rest: ticket PRs target the milestone branch at every level, and only the Owner merges `main`.

## 0.1.4 (2026-11-20)

The two W8 part 2 fixes that change the merge gate (D58).

### Recipes

- `agent-merge`: a PASS carries over GitHub's "Update branch" and nothing else. The check fetches the PR's commits as data and passes a head only if its tree equals the current base merged into the PASS head; a change folded into that merge, or any later commit, needs a new verdict. A FAIL on the PASS head stops the carry. Sync PRs need no verdict when they only merge the default branch into a milestone.
- The shared "Find the ticket" step recognises sync PRs (`sync/<slug>` into `milestone/<id>`): it passes one only when its tree is exactly the milestone merged with the newest default-branch commit it contains, and fails any other change or a conflict.

### Skills

- `plan/milestones.md`: bring `main` into a milestone through a sync PR, never by pushing to the milestone branch or with "Update branch" on a PR from `main`. `autopilot` opens a sync PR when `main` moved.

## 0.1.3 (2026-11-20)

Fixes for the problems the W8 trial found at Level 2 (D57). The two that change the merge gate (P14, P20) follow in 0.1.4.

### Skills

- `build` fetches its base before branching and checks the ticket file is on it (a cloud checkout's remote refs can be stale), and reads the learning proposals in the verdicts of PRs already merged into the milestone.
- `verify`: checklist item 6 checks error messages by mutation (change one character; a substring or prefix match fails the item). Verdicts say "Verify round: n of at most m" and the exact next step, and fix rounds are named as such.
- `report`: the closing plan PR adds `docs/reports/M<n>.md`, and the milestone PR lists `Closes #<n>` for every done ticket's issue mirror.
- `plan`: the ticket template states the Test ID format.
- `setup`: the hand-over gives the milestone ruleset the same bypass as `main`.

### Templates

- `AGENTS.md`: a "Branches" section grants pitaya's branch names once for every session, so cloud sessions don't need the permission pasted each time.
- `tests.yml`: the setup comment names `actions/setup-python` v7 and `actions/setup-node` v5.

### Recipes

- `done-when` accepts pytest-path Test IDs (`tests/test_x.py::test_y`) and treats an ID without parameters as all of a parametrized test's cases.
- Plan PRs may add `docs/reports/*.md`.
- `protect-main`: the `protect-milestones` ruleset has a bypass list.
- The setup comments in `no-weakened-tests` and `done-when` name `actions/setup-python` v7.

### Docs

- `concepts/escalation.md`: verify rounds and fix rounds alternate, verify 1, fix 1, verify 2, fix 2, verify 3, escalate.

## 0.1.2 (2026-11-20)

Fixes for the problems the W8 trial found at Level 1 (D55).

### Skills

- `build`, `plan` and `autopilot` insist on pitaya's branch names (`ticket/<id>-<slug>`, `plan/<slug>`, `milestone/M<n>`). In a session with an assigned branch, as cloud sessions have, they ask the user to allow those names instead of using the assigned branch; `autopilot` passes the permission to the sessions it starts.
- `evidence`: when the environment forbids model identifiers in repository text, the model line says "withheld" with the reason, and the Owner gets the model in the session.
- `plan`: every worked example in a condition is computed or run before it's written; the ticket template says so under "Done when".
- `plan/milestones.md`: when the tools can't create GitHub milestones for the issue mirror, the plan PR says so and lists them for the Owner.
- `build`: each fix round also updates the PR description's "How to verify" and "Scope".
- Milestone branches at every level (D56): `build` creates a missing `milestone/M<n>` from `main` instead of falling back to `main`; `plan/milestones.md` says who creates it after the Owner's merge; `help` reports a missing branch or a milestone ticket PR aimed at `main`.
- `verify`: the verdict's "Round" line links the Owner's authorisation for a round beyond "Fix rounds".

### Docs

- `concepts/states.md` no longer says milestone branches start at Level 3; they exist at every level, as D44 decided.
- `concepts/escalation.md`: the Owner may authorise an extra fix round; it runs in a fresh session, and its verdict links the authorisation.
- README: cloud sessions start by allowing pitaya's branch names.

## 0.1.1 (2026-11-20)

### Skills

- Every `gh` command in the skills names the GitHub tool alternative, for sessions where `gh` can't reach GitHub, such as cloud sessions (D54).

### Docs

- README: a "Cloud sessions" section. Cloud sessions load the plugins their environment's setup script installs, so the install is the same two commands in the setup script (D54).
- `skills/README.md` no longer links to `docs/design.md`, which isn't shipped.

## 0.1.0 (2026-11-20)

### Skills

- `/verify` doesn't open `docs/handoff/`; `/handoff` writes notes on the branch only as a last resort and removes them before review. `autopilot/tick.md` defers to `docs/concepts/states.md`. A test now checks that every path a role's skill uses is R or W in that role's column of `access.md` (D50).

- New skill `help` (D49): read only; says where the project stands, what waits on whom and the next command, or how to do something. PR decision logs gain an `Options` column, filled in when there were two or more real options. `plan/adr-template.md`: big decisions with real options get a record in `docs/adr/`, linked from `docs/decisions.md`.

- Level 4 (D48): tickets carry a Risk tag; `/verify` interrogates high-risk PRs (`verify/interrogate.md`, reproduce or drop); `/report M<n>` adds a scenario swarm and a decision-log audit (`report/milestone-level4.md`); `/design` runs an arena for contested designs (`design/arena.md`); `/autopilot` cuts the next milestone inside its branch.

- New Level 2 skill `design` (D47): scenarios first, then interfaces, data flow, notifications and state owners; tickets are cut from the scenarios, and `/report M<n>` checks each one. `/verify` drives the real app when the project has a verification skill.

- Adapted from pstack (D46): `/plan` sharpens the brief and explores how and why first (`plan/sharpen.md`); PRs carry an append-only decision log, failures included; `/verify` checks blast radius and reads the decision log; `/retro` follows the correct ladder (architecture, types/lint/CI, tests, docs) and keeps only lessons that hold for six months; `/report` draws on decision logs.

- Milestone branches (D44): `/plan` creates `milestone/M<n>` once a cut is approved; `/build` branches from it and targets it; `/autopilot` merges ticket PRs only into it, opens the milestone PR into `main` and stops for the Owner's sign-off, then starts the next cut. `/verify` posts the verdict as a comment from the machine account.

- `/autopilot` claims a ticket by pushing its branch before starting a builder.

- `/verify` posts the verdict as a review from the verifier account when agent-merge is on.

- New Level 3 skill `autopilot`: runs the active milestone in stateless ticks, dispatching fresh builder and verifier sessions, merging when the harness allows, stopping at Owner gates and a budget. `wake.md` lists how to wake it (PR events, `/loop`, a schedule, a GitHub Action).

- Milestones (`plan/milestones.md`, `milestone-template.md`): `/plan --roadmap` writes `docs/milestones/M<n>.md`; `/plan M<n>` cuts the active one into tickets; `/report M<n>` checks its exit criteria for the Owner's sign-off. Tickets carry `Milestone: M<n>`.

- Tickets have three modes (`plan/tickets.md`): `docs/tickets/T-<nnn>.md` files with an issue mirror (recommended), files only, issues only. File tickets carry `Status: open`; `/build`'s PR sets it to `done`.

- `setup`, `plan`, `build`, `verify`, `report`, `handoff`, `retro`, `autopilot`, `tdd`, `evidence`, `ask-owner` and `learning`.

### Templates

- Hooks look inside `sh -c` and `eval`; `ask_on_merge.py` reads only the Autonomy value and also catches `gh -R ... pr merge`, GraphQL merge and auto-merge mutations and auto-merge tools; `no_push_main.py` handles `--repo`; `ask_on_rule_files.py` covers all of `.github/` and inline scripts that name a rule file. `settings.json` also denies nested `.env` files.

- New hook `ask_on_merge.py` asks before an agent merges a PR unless the harness file lets agents merge. `AGENTS.md` says so under "Never".


- Workflows use `actions/checkout@v6` and `actions/setup-python@v7` (Node 24).
- Level 1: `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, three hooks (`no_push_main`, `no_destructive`, `ask_on_rule_files`), `.github/workflows/tests.yml`, `docs/decisions.md`, and the memory files `docs/agents/glossary.md`, `learnings.md` and `architecture.md`.

- Clarified from the W6 trial: hand-off notes state whether the working copy is clean and list every check that must pass; mutation evidence when a condition can't go red; mutation hygiene (no bytecode caches, clean `git status`); the verifier's checklist for behaviour-pinning tickets and reverted out-of-scope commits.
- `install_templates.py --skip PATH` leaves out a template the project already covers.

### Docs

- New concept pages (D49): `access.md` (who reads and writes what, the control and data planes, which crossings matter, what is enforced and what is prose), `states.md` (ticket, milestone, verdict and autopilot state machines and where each state lives) and `layout.md` (a full project's files and branches).
- `docs/levels.md`: every skill, template and recipe, listed by the level it belongs to, with what each requires and works better with. Generated from `docs/components.json`.
- `retro` and `handoff` are part of Level 1 (they were listed under Level 3 in `suggestion.md`).
- `docs/components.json`: every component with its level, `requires`, `recommends` and project `needs`; it generates `levels.md`.
- Levels 0-4 form one spectrum from close control (like Matt Pocock's skills) to the most agent authority (like pstack); `levels.md` opens with who holds authority at each level. There is no custom selection.
- `templates/docs/agents/README.md` explains why `harness.md` is filled in by `/setup` rather than copied. Template `README.md` files are never copied.

### Recipes

- `docs/adr/**` is read-only by default, plan PRs may add `docs/adr/*.md`, and the agent-merge CODEOWNERS file owns `/docs/adr/` (D49).
- `second-model-review` becomes a swappable adapter: a different Claude model, Cursor CLI, Cursor Bugbot or a Grok action. New Level 4 recipe `deep-verification`.

- New Level 2 recipe `verify-app`: a project skill that drives the real app, with templates for the skill and its feature map.

- `protect-main` adds a `protect-milestones` ruleset for `milestone/*`. `agent-merge` gates merges into milestone branches; it reads verdict comments from the machine account (edited ones don't count, any FAIL on the head is final) and refuses plan and milestone PRs. New `multi-account` recipe holds CODEOWNERS for repositories with several agent accounts.

- `append-only` accepts lines only after the last existing one. `serial-resources` maps resources to paths and fails undeclared changes. `protect-main` requires up-to-date branches (or a merge queue) from Level 2. `progress-file` runs on every PR, keeps its files in `docs/progress/`, and lets Owner accounts change requirements.

- Every workflow runs the base branch's copy of its check. `no-weakened-tests` and `done-when` run the PR's tests in a separate job; an empty base report fails. `agent-merge` reads the verdict from the verifier account's pull request review on the current head, runs with `pull_request_target`, and refuses plan PRs and a verifier equal to `MACHINE_ACCOUNT`. Token permissions and the required-check source are spelled out.

- The shared "Find the ticket" step: every account in `MACHINE_ACCOUNT` (comma separated, any case) must use an open ticket, and it fails closed when the variable is unset; milestone PRs (`milestone/*`) are left to the Owner; file tickets never fall back to issues; done tickets, closed issues and tickets another open PR works on can't be claimed. New `multi-account` recipe: CODEOWNERS and code-owner review, only for repositories with more than one agent account.

- Workflows pass step outputs to scripts through `env:`, never inline, so a branch or file name can't inject shell code.

- `docs/milestones/**` is read-only for ticket PRs; plan PRs may change `docs/milestones/*.md`.

- `protect-main` requires 1 approval, dismissed on new pushes; `agent-merge` lowers it to 0 because the `verdict` status replaces it.

- Plan PRs (`plan/<slug>` branches) skip the ticket checks and may change only ticket and planning files; anything else fails the shared "Find the ticket" step.

- `scope` and `read-only-paths` take `--ticket-path`; a PR may change only its own ticket file's `Status:` line. `docs/tickets/**` is read-only by default. The shared "Find the ticket" step outputs `ticket_path`.

- Adding a guardrail is rule work: the Owner opens it, or it's a ticket listing the exact files.
- Every workflow uses `actions/checkout@v6` and `actions/setup-python@v7`.
- Level 1: `protect-main`.
- Level 2: `machine-account`, `commit-author`, `scope`, `read-only-paths`, `no-weakened-tests`, `done-when`, `append-only`, `serial-resources`, `evidence`, each check with a copyable script and workflow.
- Level 3: `progress-file` (start-up routine and a feature list where agents may only flip "passes"), `agent-merge` (a `verdict` status tied to the current head commit), `second-model-review`, `project-evals`.
