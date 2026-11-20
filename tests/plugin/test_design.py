"""P2 of the Level Max plan (D47): design a milestone before cutting it, and verify the real app.

- /design M<n> (adapted from pstack's /architect, plus BDD) writes the milestone's
  behaviour scenarios, interfaces, data flow, notifications and state owners.
- /plan M<n> cuts tickets from those scenarios: every scenario is covered.
- The verify-app recipe gives a project its own skill that drives the real app.
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


def test_design_is_a_user_invoked_level_2_skill():
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert "./skills/design" in plugin["skills"]
    assert "disable-model-invocation: true" in read(SKILLS / "design" / "SKILL.md")
    comps = {c["id"]: c for c in json.loads((PLUGIN / "docs" / "components.json").read_text())["components"]}
    assert comps["skill:design"]["level"] == 2


def test_design_template_has_every_part_of_a_global_design():
    text = read(SKILLS / "design" / "design-template.md")
    for heading in ("## Scenarios", "## Interfaces", "## Data flow", "## Notifications", "## State owners",
                    "## Shapes considered", "## Open questions"):
        assert heading in text, heading
    assert re.search(r"S-\d+", text) and "Given" in text and "When" in text and "Then" in text


def test_design_skill_compares_two_shapes_and_picks_by_ownership():
    text = read(SKILLS / "design" / "SKILL.md")
    assert "two shapes" in text and "one owner" in text
    assert "docs/milestones/M<n>-design.md" in text


def test_plan_cuts_tickets_from_scenarios():
    text = read(SKILLS / "plan" / "milestones.md")
    assert "M<n>-design.md" in text and "scenario" in text.lower()
    assert re.search(r"Scenarios?: S-<n>", read(SKILLS / "plan" / "ticket-template.md"))


def test_report_checks_every_scenario():
    assert "scenario" in read(SKILLS / "report" / "SKILL.md").lower()


def test_verify_app_recipe_and_its_templates():
    text = read(GUARDRAILS / "verify-app.md")
    assert "never executed is a draft" in text.lower() or "never been run" in text.lower()
    skill = read(GUARDRAILS / "files" / "verify-app" / "SKILL-template.md")
    for section in ("## Launch", "## Doctor", "## Drive", "## Evidence", "## Cleanup"):
        assert section in skill, section
    feature = read(GUARDRAILS / "files" / "verify-app" / "feature-template.md")
    assert [h for h in re.findall(r"^## (.+)$", feature, re.M)] == [
        "Sub-features", "How to get to it (user POV)", "Driving it", "Gotchas"]


def test_verifier_drives_the_real_app_when_the_project_has_a_verify_skill():
    text = read(SKILLS / "verify" / "checklist.md")
    assert "Real app" in text and ".claude/skills/verify-" in text
