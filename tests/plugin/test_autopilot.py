"""/autopilot: the Level 3 orchestrator that runs one milestone and stops at the Owner's gates (D39)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
SKILL = PLUGIN / "skills" / "autopilot"


def text() -> str:
    return (SKILL / "SKILL.md").read_text()


def test_it_is_a_user_invoked_skill_listed_in_the_plugin():
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert "./skills/autopilot" in plugin["skills"]
    assert "disable-model-invocation: true" in text()


def test_it_is_a_level_3_component_with_its_prerequisites():
    comps = {c["id"]: c for c in json.loads((PLUGIN / "docs" / "components.json").read_text())["components"]}
    c = comps["skill:autopilot"]
    assert c["level"] == 3
    assert {"skill:build", "skill:verify", "skill:report", "protect-main", "machine-account", "scope"} <= set(c["requires"])
    assert "agent-merge" in c.get("recommends", [])


def test_it_runs_one_active_milestone():
    t = text()
    assert "docs/milestones/" in t and "Status: active" in t


def test_it_stops_at_every_owner_gate():
    t = text().lower()
    for gate in ("plan pr", "sensitive area", "fix rounds", "sign-off", "budget", "stop"):
        assert gate in t, gate


def test_it_never_merges_what_the_owner_must_merge():
    t = text()
    assert re.search(r"Never merge a plan PR", t)
    assert re.search(r"Never .*bypass", t)


def test_it_dispatches_orchestrators_to_fresh_sessions_only():
    # R3: orchestrators never run each other in one context. /autopilot hands each
    # build, verify and report to a fresh session or agent instead.
    t = text()
    for other in ("build", "verify", "report"):
        for line in t.splitlines():
            if f"/pitaya:{other}" in line:
                assert "fresh" in line, line


def test_state_comes_from_the_repository_not_memory():
    assert "stateless" in text().lower()


def test_wake_options_are_documented():
    wake = (SKILL / "wake.md").read_text()
    for option in ("subscribe", "/loop", "schedule", "GitHub Action"):
        assert option in wake, option


def test_harness_template_has_autopilot_settings():
    harness = (PLUGIN / "skills" / "setup" / "harness-template.md").read_text()
    assert re.search(r"^- Autopilot: off\.", harness, re.M)
