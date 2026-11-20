"""P3 of the Level Max plan (D48): Level 4, the most agent authority with the most verification.

- Tickets carry a Risk tag; high risk is set by rule and the Owner may override.
- /verify interrogates high-risk PRs at Level 4: adversaries from a second model,
  and only findings a run reproduces survive.
- The second model is a swappable adapter: a different Claude model by default,
  or Cursor CLI, Cursor Bugbot or a Grok action.
- /report runs a swarm over the scenarios and an audit of the decision logs at
  Level 4 milestones.
- /design runs an arena for contested designs at Level 4.
- /autopilot at Level 4 cuts the next milestone itself, inside its branch.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
SKILLS = PLUGIN / "skills"
GUARDRAILS = PLUGIN / "docs" / "guardrails"


def read(path: Path) -> str:
    return path.read_text()


def test_tickets_carry_a_risk_tag_with_rules():
    assert re.search(r"^Risk: low$", read(SKILLS / "plan" / "ticket-template.md"), re.M)
    text = read(SKILLS / "plan" / "tickets.md")
    for rule in ("sensitive area", "public interface", "migration", "more than one module"):
        assert rule in text, rule
    assert "Owner" in text and "override" in text


def test_interrogate_only_keeps_run_proven_findings():
    text = read(SKILLS / "verify" / "interrogate.md")
    assert "Risk: high" in text and "Level 4" in text
    assert "reproduce" in text and "Dropped" in text
    assert "worktree" in text
    checklist = read(SKILLS / "verify" / "checklist.md")
    assert "Interrogate" in checklist and "interrogate.md" in checklist


def test_second_model_is_a_swappable_adapter():
    text = read(GUARDRAILS / "second-model-review.md")
    for option in ("claude:", "cursor-cli:", "bugbot", "grok-action"):
        assert option in text, option
    assert "only findings" in text.lower()
    harness = read(SKILLS / "setup" / "harness-template.md")
    assert re.search(r"^- Second model: claude:", harness, re.M)


def test_level_4_milestones_get_a_swarm_and_a_log_audit():
    text = read(SKILLS / "report" / "milestone-level4.md")
    assert "swarm" in text.lower() and "scenario" in text.lower()
    assert "Attention" in text and "decision log" in text.lower()
    assert "milestone-level4.md" in read(SKILLS / "report" / "SKILL.md")


def test_contested_designs_go_to_an_arena():
    text = read(SKILLS / "design" / "arena.md")
    for step in ("rubric", "judge", "base", "graft", "converge"):
        assert step in text.lower(), step
    assert "arena.md" in read(SKILLS / "design" / "SKILL.md")


def test_level_4_autopilot_cuts_the_next_milestone_inside_its_branch():
    text = read(SKILLS / "autopilot" / "SKILL.md")
    assert "Level 4" in text and "milestone/M<n+1>" in text
    harness = read(SKILLS / "setup" / "harness-template.md")
    assert "Agents merge ticket and plan PRs into milestone branches; only the Owner merges main" in harness


def test_deep_verification_is_a_level_4_component():
    comps = {c["id"]: c for c in json.loads((PLUGIN / "docs" / "components.json").read_text())["components"]}
    assert comps["deep-verification"]["level"] == 4
    assert "second-model-review" in comps["deep-verification"]["requires"]
