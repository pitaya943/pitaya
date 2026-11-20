"""select_components.py: pick a level preset, then add or remove components (D33).

It only prints a plan. It never copies files or changes settings: adding a
guardrail stays rule work for the Owner or a ticket.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
SCRIPT = PLUGIN / "skills" / "setup" / "scripts" / "select_components.py"
MANIFEST = json.loads((PLUGIN / "docs" / "components.json").read_text())
LEVEL = {c["id"]: c["level"] for c in MANIFEST["components"]}


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=30)


def plan(*args: str) -> dict:
    proc = run(*args, "--json")
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_each_preset_is_every_component_up_to_that_level():
    for level in range(4):
        got = plan("--level", str(level))
        assert set(got["selected"]) == {c for c, lv in LEVEL.items() if lv <= level}
        assert got["label"] == f"Level {level}"
        assert got["added_for"] == {}


def test_adding_a_component_pulls_in_what_it_requires():
    got = plan("--level", "1", "--add", "scope")
    assert {"scope", "machine-account"} <= set(got["selected"])
    assert got["added_for"] == {"machine-account": ["scope"]}
    assert got["label"] == "Level 1 + scope, machine-account"


def test_dependencies_come_before_what_needs_them():
    got = plan("--level", "1", "--add", "agent-merge")
    order = got["selected"]
    for cid in order:
        for ref in next(c for c in MANIFEST["components"] if c["id"] == cid).get("requires", []):
            assert order.index(ref) < order.index(cid), (ref, cid)


def test_missing_recommendations_are_warnings():
    got = plan("--level", "1", "--add", "scope")
    assert any("read-only-paths" in w for w in got["warnings"])
    proc = run("--level", "1", "--add", "scope")
    assert proc.returncode == 0
    assert "recommends read-only-paths" in proc.stdout


def test_needs_are_listed_with_their_description():
    got = plan("--level", "1", "--add", "done-when")
    assert "junit-xml" in got["needs"]
    assert got["needs"]["junit-xml"] == MANIFEST["needs"]["junit-xml"]


def test_removing_a_template_component_becomes_an_install_skip():
    got = plan("--level", "1", "--remove", "decisions")
    assert "decisions" not in got["selected"]
    assert got["label"] == "Level 1 without decisions"
    assert got["install_args"] == ["--skip", "docs/decisions.md"]


def test_removing_something_still_required_is_refused():
    proc = run("--level", "2", "--remove", "machine-account")
    assert proc.returncode == 2
    assert "machine-account" in proc.stderr
    assert "scope" in proc.stderr  # names who needs it
    assert "To fix:" in proc.stderr


def test_removing_it_together_with_its_dependents_works():
    keep = ["--remove", "machine-account"] + [
        a for d in ("commit-author", "scope", "read-only-paths", "no-weakened-tests", "done-when",
                    "append-only", "serial-resources", "evidence", "multi-account") for a in ("--remove", d)]
    got = plan("--level", "2", *keep)
    assert "machine-account" not in got["selected"]


def test_unknown_ids_are_refused():
    proc = run("--level", "1", "--add", "no-such-thing")
    assert proc.returncode == 2
    assert "no-such-thing" in proc.stderr


def test_steps_separate_what_setup_copies_from_recipes_and_owner_settings():
    got = plan("--level", "1", "--add", "scope")
    kinds = {s["id"]: s["how"] for s in got["steps"]}
    assert kinds["agents-map"] == "copied by /setup"
    assert kinds["harness-file"] == "filled in by /setup"
    assert kinds["scope"].startswith("follow docs/guardrails/scope.md")
    assert kinds["skill:tdd"] == "skill, installed with the plugin"


def test_it_writes_nothing(tmp_path):
    before = sorted(p for p in tmp_path.rglob("*"))
    proc = subprocess.run([sys.executable, str(SCRIPT), "--level", "3"], capture_output=True,
                          text=True, timeout=30, cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert sorted(p for p in tmp_path.rglob("*")) == before
