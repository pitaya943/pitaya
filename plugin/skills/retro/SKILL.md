---
name: retro
description: Look back over recent work, find the mistakes that keep coming back, and propose for each one a rule and what should enforce it, from a test or lint rule to a hook, CI check or doc line. Also check whether any guardrail can now be retired. Proposes only; the Owner decides.
disable-model-invocation: true
argument-hint: "<optional: the period or PRs to look at>"
---

# Retro

## 1. Gather

1. Read `docs/agents/harness.md`: the level, the "Guardrails" list and the document language. If it's missing, suggest `/setup` once and continue.
2. Collect from the period (default: since the last retro, or the last 20 merged PRs):
   - verdicts, especially FAIL reasons and which fix round passed;
   - escalations to the Owner and how they were answered;
   - PR review comments and CI failures;
   - learning proposals from verdicts and hand-off notes, and `docs/agents/learnings.md`;
   - the PRs' **Decision log** rows, above all dead ends and failed attempts: they show where agents lost time;
   - `docs/decisions.md`, when the project keeps one.

## 2. Find what repeats

Group the findings by cause, not by symptom. Keep only causes seen at least twice; a one-off is noise. For each, note the occurrences with links.

## 3. Propose a rule and an enforcer

Make each repeated mistake impossible to repeat, at the **highest level that works** (adapted from pstack's `/correct`):

1. **Architecture:** one owner per piece of state, one supported way per task, hidden internals, one source of truth, dead code deleted.
2. **Types, lint or CI:** make the bad state unrepresentable; if bad code still compiles, a lint rule or CI check whose error names the fix. For a common pattern, fail only on new additions. A hook when it must never happen in a session.
3. **Tests:** fix or delete tests that pass when the behaviour breaks, or fail when only internals change.
4. **Docs or skills:** last, only for judgement calls nothing can enforce.

Every new check must fail on a **real past mistake** from the occurrences you listed, and run the same command locally and in CI. Keep a rule table in `AGENTS.md` or the harness file: each rule next to what enforces it.

Learnings and skill edits: keep a lesson only if it will still hold in **six months**; drop commit hashes, versions and counts. Read the skill or doc it would change first, and drop what it already says.

## 4. Check what can be retired

For each guardrail and hook in use, read its "When to remove" note. If the evidence it names is there (it hasn't fired in a long time, or something stronger now covers the same rule), propose removing it.

## 5. Present

Show the Owner one table in the document language, with one row per proposal: cause, occurrences, proposed rule, enforcer, cost, and "add" or "remove". Ask which to accept.

Apply only accepted proposals, each through a normal pull request. Add accepted learnings as new rows in `docs/agents/learnings.md`, and record decisions in `docs/decisions.md` when the project keeps one.

## Don't

- Don't change skills, rules, hooks or CI without the Owner's acceptance.
- Don't propose a rule for something that happened once.
