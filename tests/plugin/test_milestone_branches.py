"""Milestone branches (D44): agents merge tickets into milestone/M<n>; only the Owner merges main."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


def test_milestones_doc_describes_the_branch_flow():
    text = read("skills/plan/milestones.md")
    assert "milestone/M<n>" in text
    assert "no milestone branches" not in text.lower()


def test_build_targets_the_active_milestone_branch():
    text = read("skills/build/SKILL.md")
    assert "milestone/M<n>" in text


def test_autopilot_merges_into_milestone_branches_only():
    text = read("skills/autopilot/SKILL.md")
    assert "milestone/M<n>" in text
    assert "Never merge into `main`" in text


def test_autopilot_starts_the_next_cut_after_sign_off():
    text = read("skills/autopilot/SKILL.md")
    assert "/pitaya:plan M<n+1>" in text


def test_protect_main_has_a_milestone_ruleset():
    text = read("docs/guardrails/protect-main.md")
    assert "milestone/*" in text


def test_harness_autonomy_alternative_names_milestone_branches():
    text = read("skills/setup/harness-template.md")
    assert "Agents merge ticket PRs into milestone branches" in text


def test_agent_merge_recipe_targets_milestone_branches():
    text = read("docs/guardrails/agent-merge.md")
    assert "milestone/*" in text
