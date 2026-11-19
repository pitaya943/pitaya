"""The shipped skill set matches docs/design.md (section 5).

* Each expected skill exists, is listed in plugin.json, and has the right kind:
  user-invoked skills set ``disable-model-invocation: true``; model-invoked
  skills don't (design principle R3).
* Every skill reads the project config first and copes without it (R4).
* User-invoked skills never tell the agent to run another user-invoked skill.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_skills  # noqa: E402

# Grows step by step (docs/design.md, section 13).
USER_INVOKED = {"setup", "plan", "build", "verify", "report", "handoff", "retro"}
MODEL_INVOKED = {"tdd", "evidence", "ask-owner", "learning"}
EXPECTED = USER_INVOKED | MODEL_INVOKED
CONFIG = "docs/agents/harness.md"


def frontmatter(name: str) -> dict:
    fields, errors = check_skills.parse_frontmatter((REPO_ROOT / "skills" / name / "SKILL.md").read_text())
    assert errors == []
    return fields


def test_expected_skills_are_listed():
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    listed = {p.removeprefix("./skills/") for p in plugin["skills"]}
    assert EXPECTED <= listed


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_skill_kind(name):
    disabled = frontmatter(name).get("disable-model-invocation", False)
    assert disabled is (name in USER_INVOKED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_reads_project_config_first(name):
    text = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
    assert CONFIG in text
    assert "/setup" in text or name == "setup"  # points at setup when the config is missing


@pytest.mark.parametrize("name", sorted(USER_INVOKED))
def test_user_invoked_skills_do_not_invoke_each_other(name):
    text = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
    for other in USER_INVOKED - {name, "setup"}:  # suggesting /setup for missing config is allowed
        assert not re.search(rf"(?:run|invoke|call|use)\s+`?/{other}\b", text, re.I), other
