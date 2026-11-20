"""Fixes for the problems the W8 trial found at Level 1 (docs/trials/w8.md, P1-P6; D55)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
SKILLS = PLUGIN / "skills"


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


# P1: cloud sessions are told to push only to an assigned branch; pitaya's checks need its own names.

def test_build_insists_on_the_ticket_branch_name_and_asks_to_use_it():
    text = read("skills/build/SKILL.md")
    assert "assigned branch" in text and "ask the user" in text.lower()


def test_plan_insists_on_the_plan_branch_name():
    for rel in ("skills/plan/tickets.md", "skills/plan/milestones.md"):
        assert "assigned branch" in read(rel), rel


def test_readme_tells_cloud_users_to_allow_the_branch_names():
    section = read("README.md").split("## Cloud sessions", 1)[1].split("\n## ", 1)[0]
    assert "ticket/<id>-<slug>" in section and "plan/<slug>" in section


# P2: a cloud environment may forbid model identifiers in repository text.

def test_evidence_allows_a_withheld_model_with_the_reason():
    text = read("skills/evidence/SKILL.md")
    assert '"withheld"' in text and "in the session" in text


# P3: a worked example in a condition must be checked before it is written.

def test_plan_checks_worked_examples():
    assert "worked example" in read("skills/plan/SKILL.md")
    assert "worked example" in read("skills/plan/ticket-template.md")


# P4: the Owner may authorise extra fix rounds.

def test_extra_fix_rounds_need_the_owners_authorisation_and_a_link():
    text = read("docs/concepts/escalation.md")
    assert "extra round" in text.lower() and "authoris" in text
    assert "authoris" in read("skills/verify/verdict-template.md")


# P5: the session's tools may not create GitHub milestones.

def test_milestones_say_what_to_do_when_github_milestones_cant_be_created():
    assert "can't create" in read("skills/plan/milestones.md")


# P6: "How to verify" and "Scope" go stale after fix rounds.

def test_fix_rounds_refresh_the_pr_description():
    text = read("skills/build/SKILL.md").split("## Fix rounds", 1)[1]
    assert "How to verify" in text and "Scope" in text


def test_autopilot_asks_for_the_branch_names_and_passes_the_permission_on():
    text = read("skills/autopilot/SKILL.md")
    assert "assigned branch" in text and "every session you start" in text
