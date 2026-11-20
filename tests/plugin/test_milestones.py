"""Milestones: a roadmap of large outcomes, each cut into tickets when it starts (D38)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN = REPO_ROOT / "plugin" / "skills" / "plan"
TEMPLATE = PLAN / "milestone-template.md"


def test_milestone_template_has_the_sections_autopilot_and_report_rely_on():
    text = TEMPLATE.read_text()
    assert re.search(r"^# M<n>: ", text, re.M)
    assert re.search(r"^Status: planned$", text, re.M)
    for heading in ("## Goal", "## Exit criteria", "## Tickets", "## Not in this milestone"):
        assert heading in text, heading


def test_ticket_template_names_its_milestone():
    assert re.search(r"^Milestone: M<n>$", (PLAN / "ticket-template.md").read_text(), re.M)


def test_plan_skill_has_both_levels():
    text = (PLAN / "SKILL.md").read_text()
    assert "--roadmap" in text and "milestones.md" in text
    assert (PLAN / "milestones.md").is_file()


def test_report_covers_a_milestone_and_its_sign_off():
    text = (REPO_ROOT / "plugin" / "skills" / "report" / "SKILL.md").read_text()
    assert "docs/milestones/" in text and "Status: done" in text


def test_harness_template_says_where_milestones_live():
    text = (REPO_ROOT / "plugin" / "skills" / "setup" / "harness-template.md").read_text()
    assert "docs/milestones/M<n>.md" in text
