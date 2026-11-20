"""The sixth and last batch of fixes from the review of 0.1.4 (D63 c, D71): the Level 1 session layer.

F11: with no machine account the agent acts as the Owner, so a machine account is required before
agents act unattended. The merge hook's part of it is tested in `tests/templates/test_hooks.py`;
this file covers the skills and pages that have to say the same thing, the notes the verdict on
0.1.9 left (the `serial-resources` order after a reopen, the design's status line) and the final
status of every finding.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
PAGES = sorted(p for p in PLUGIN.rglob("*.md") if p.name != "CHANGELOG.md")
VERSION = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]

UNATTENDED = "docs/concepts/autonomy.md"
HEADING = "## Unattended work needs a machine account"
ANCHOR = "#unattended-work-needs-a-machine-account"


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


def flat(rel: str) -> str:
    return " ".join(read(rel).split())


def section(rel: str, heading: str) -> str:
    """The text under one heading, up to the next heading of the same or a higher level."""
    text = read(rel)
    assert heading in text, f"{rel} has no {heading!r}"
    level = len(heading) - len(heading.lstrip("#"))
    body = text.split(heading, 1)[1]
    end = re.search(rf"(?m)^#{{1,{level}}} ", body)
    return " ".join((body[:end.start()] if end else body).split())


def numbered(rel: str, heading: str, start: str) -> str:
    """One list item of a skill, found by how it starts."""
    lines = [l for l in read(rel).split(heading, 1)[1].splitlines() if l.lstrip().startswith(start)]
    assert lines, f"{rel}: no item starting {start!r} under {heading!r}"
    return lines[0]


# --- F11: one definition, and the requirement -----------------------------------

def test_one_page_defines_unattended_work_and_requires_a_machine_account():
    text = section(UNATTENDED, HEADING)
    # what counts as unattended: every way the docs let a session run with nobody approving its steps
    for starter in ("`/autopilot`", "a schedule", "GitHub Action", "another session", "permission prompts"):
        assert starter in text, starter
    assert "must name a machine account" in text
    # why: what the session holds when it acts as the Owner
    for reason in ("bypass", "`gh pr merge --admin`", "approve", "author", "`OWNER`"):
        assert reason in text, reason
    # what is left without one, and for whom that is enough
    assert "the hooks alone" in text
    assert "a person watches every step" in text


def test_the_definition_says_what_each_part_of_the_harness_does_about_it():
    text = section(UNATTENDED, HEADING)
    for part in ("`/setup`", "`/autopilot`", "`/build`", "`ask_on_merge.py`"):
        assert part in text, part


def test_setup_no_longer_takes_none_without_saying_what_it_costs():
    """The review's finding: `/setup` accepted "None" and said nothing."""
    text = read("skills/setup/SKILL.md")
    assert '"None" is a valid answer' not in text
    question = numbered("skills/setup/SKILL.md", "## 2. Ask", "1. **Owner and machine account.**")
    assert "required before agents act unattended" in question
    assert "from Level 2" in question
    assert "a person watches every step" in question
    assert "the hooks alone" in question          # what setup says in its output
    assert "harness file" in question             # and writes down
    assert "autonomy.md" in question


def test_setup_does_not_raise_the_level_or_turn_autopilot_on_without_one():
    level = numbered("skills/setup/SKILL.md", "## 3. Install and write", "1. **Level.**")
    assert "machine account" in level and "Level 2" in level and "Autopilot" in level


def test_setup_hands_over_different_steps_when_there_is_no_machine_account():
    text = section("skills/setup/SKILL.md", "## 4. Hand the Owner the repo settings")
    assert "With no machine account" in text
    assert "bypass" in text and "unattended" in text


def test_the_harness_template_says_what_none_means():
    line = next(l for l in read("skills/setup/harness-template.md").splitlines() if l.startswith("- Machine account:"))
    assert line.startswith("- Machine account: example-bot.")  # the value stays first: the merge hook reads it
    assert "Required before agents act unattended" in line
    assert '"none"' in line and "a person watches every step" in line
    assert "the hooks alone" in line
    assert "agents use the current session's account." not in line  # the old line stopped there


def test_autopilot_stops_without_a_machine_account():
    step = numbered("skills/autopilot/SKILL.md", "## Before the first tick", "1. ")
    assert "machine account" in step and "unattended" in step
    assert "GitHub login" in step      # named is not enough: the session has to be signed in as it
    assert "stop" in step


def test_build_stops_when_nobody_watches_and_there_is_no_machine_account():
    step = numbered("skills/build/SKILL.md", "## Before you start", "6. **Identity.**")
    assert "names none" in step
    assert "unattended" in step and "stop" in step
    assert "a person" in step  # with someone in the conversation the work goes on


def test_protect_main_says_who_holds_the_bypass():
    text = flat("docs/guardrails/protect-main.md")
    assert "With no machine account" in text
    assert "`gh pr merge --admin`" in text
    assert ANCHOR in text
    # The old row promised more than the ruleset gives when the agent is the Owner.
    assert "so only the Owner's approval can merge them. The Owner's own PRs merge through the bypass." not in text


def test_the_machine_account_recipe_is_required_before_unattended_work():
    assert "Level: 2. At Level 1 too, before agents act unattended." in read("docs/guardrails/machine-account.md")
    when = section("docs/guardrails/machine-account.md", "## When it's worth adding")
    assert "Before agents act unattended" in when and "required" in when
    guards = section("docs/guardrails/machine-account.md", "## What it guards against")
    assert "bypass" in guards
    how = section("docs/guardrails/machine-account.md", "## How to add it")
    assert "GitHub App" in how                    # the review's other form of a separate identity
    assert "token of the Owner's own account" in how  # and the one that isn't one
    remove = section("docs/guardrails/machine-account.md", "## When to remove it")
    assert "watches every step" in remove


def test_the_levels_page_states_the_requirement():
    text = section("docs/levels.md", "## What the levels assume")
    assert "**Unattended agents need a machine account.**" in text
    assert "concepts/autonomy.md" + ANCHOR in text


@pytest.mark.parametrize("rel, words", [
    ("docs/concepts/access.md", ("With no machine account", "the hooks alone")),
    ("docs/concepts/escalation.md", ("With no machine account", "the agent's own comments")),
    ("docs/suggestion.md", ("before agents act unattended",)),
    ("README.md", ("unattended", "machine account")),
    ("docs/concepts/roles.md", ("unattended",)),
])
def test_the_pages_that_touch_it_say_the_same(rel, words):
    text = flat(rel)
    for word in words:
        assert word in text, (rel, word)
    assert "autonomy.md" + ANCHOR in text or rel == UNATTENDED, rel


OPTIONAL = [
    r'"None" is a valid answer',
    r"ideally acting as a machine account",
    r"If it's \"none\", agents use the current session's account\.",
    r"If there's a machine account:",
]


@pytest.mark.parametrize("pattern", OPTIONAL)
def test_no_page_still_calls_the_machine_account_optional_without_the_condition(pattern):
    hits = [p.relative_to(PLUGIN).as_posix() for p in PAGES if re.search(pattern, p.read_text())]
    assert hits == []


def test_every_page_that_names_unattended_work_and_none_points_at_the_definition():
    """A page that tells the reader what "none" means, or what an unattended session needs,
    links the one definition instead of restating a rule that can drift."""
    seen = []
    for page in PAGES:
        text = page.read_text()
        rel = page.relative_to(PLUGIN).as_posix()
        if rel != UNATTENDED and re.search(r"(?i)no machine account|act unattended", text):
            seen.append(rel)
            assert "autonomy.md" in text, rel
    assert len(seen) >= 6, seen  # fails when the wording changes and this test would pass empty


# --- still open from the verdicts on 0.1.6: what a separate session is --------------

def test_a_new_session_is_separate_whoever_started_it():
    text = flat(UNATTENDED)
    assert "or anything that session started" not in text  # it read as "a new session too", which the check never said
    prerequisite = next(l for l in read(UNATTENDED).splitlines() if l.startswith("3. The verifier is a separate session"))
    assert "subagent or background agent" in prerequisite and "shares its parent's session ID" in prerequisite
    assert "A new session" in prerequisite and "its own ID" in prerequisite
    assert "whoever started it" in prerequisite
    assert "conversation" in prerequisite  # what must not travel with it


def test_the_agent_merge_recipe_agrees_on_what_separate_means():
    text = flat("docs/guardrails/agent-merge.md")
    assert "whoever started it" in text


# --- the verdict on 0.1.9: serial-resources after a reopen ---------------------------

def test_serial_resources_says_what_a_reopened_pull_request_does_to_the_order():
    text = section("docs/guardrails/serial-resources.md", "## Cost and false positives")
    assert "reopened" in text
    assert "re-run" in text
    assert "Require branches to be up to date" in text  # what still keeps the two from merging unchecked


def test_autopilot_reruns_the_later_check_when_it_finds_a_reopened_earlier_pr():
    text = flat("skills/autopilot/tick.md")
    assert "reopened" in text


# --- the record ------------------------------------------------------------------

def test_the_decision_log_covers_the_batch():
    decisions = (REPO_ROOT / "docs" / "decisions.md").read_text()
    row = next((l for l in decisions.splitlines() if l.startswith("| D71 |")), None)
    assert row, "no D71"
    for word in ("F11", "D63", "#49", "tag", "unattended", "serial-resources", "`--admin`"):
        assert word in row, word


FINDINGS = [f"N{n:02d}" for n in range(1, 5)] + [f"F{n:02d}" for n in range(1, 33)]


def test_every_finding_has_a_final_status():
    """The last batch: nothing in the review's table is still open or waiting for a batch."""
    trial = (REPO_ROOT / "docs" / "trials" / "w8.md").read_text()
    table = trial.split("## Review of 0.1.4", 1)[1]
    rows = {m.group(1): m.group(0) for m in re.finditer(r"(?m)^\| ([NF]\d\d) \|.*$", table)}
    assert sorted(rows) == sorted(FINDINGS)
    for finding, row in rows.items():
        status = row.rstrip("|").split("|")[-1].strip()
        assert re.match(r"(fixed in 0\.1\.\d+|deferred \(D59\)|the accidental cases fixed in 0\.1\.6)", status), row
        assert "open:" not in row and "batch 6" not in row, row
    assert "0.1.10" in rows["F11"] and "D71" in rows["F11"]


def test_the_trial_record_closes_the_review_and_lists_what_m3_must_try():
    trial = " ".join((REPO_ROOT / "docs" / "trials" / "w8.md").read_text().split())
    assert "Fixed in 0.1.10 (D63 c, D71): F11" in trial
    assert "The review's six batches are done" in trial
    for live in ("`ask_on_merge.py`", "signed in as the machine account", "reopened"):
        assert live in trial, live
