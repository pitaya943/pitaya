"""Levels form one spectrum (D45): Level 0 is closest to Matt Pocock's skills, Level 4 to pstack.

Each level up gives agents more authority and adds the safeguards that authority
needs, so a project picks a level by how much control it wants to keep. There is
no custom selection: the levels are the sets.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"


def components() -> dict[str, dict]:
    return {c["id"]: c for c in json.loads((PLUGIN / "docs" / "components.json").read_text())["components"]}


def test_custom_selection_is_gone():
    assert not (PLUGIN / "skills" / "setup" / "scripts" / "select_components.py").exists()
    for rel in ("docs/levels.md", "docs/suggestion.md", "skills/setup/SKILL.md",
                "skills/setup/harness-template.md", "README.md"):
        text = (PLUGIN / rel).read_text()
        assert "select_components" not in text and "custom selection" not in text.lower(), rel


def test_levels_name_who_holds_authority():
    text = (PLUGIN / "docs" / "levels.md").read_text()
    for marker in ("Matt Pocock", "pstack", "Agent authority"):
        assert marker in text, marker


def test_level_4_is_the_most_autonomous():
    comps = components()
    assert comps["second-model-review"]["level"] == 4
    assert comps["project-evals"]["level"] == 4
    assert comps["skill:autopilot"]["level"] == 3
    assert comps["agent-merge"]["level"] == 3


def test_suggestion_has_a_level_4_section():
    text = (PLUGIN / "docs" / "suggestion.md").read_text()
    assert "## Level 4" in text
