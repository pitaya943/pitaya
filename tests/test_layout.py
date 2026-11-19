"""The shipped plugin lives in plugin/ and holds only what users need (decision D32).

The marketplace installs plugin/ alone, so development files (tests, the
design, CI, this repository's own AGENTS.md) must stay outside it, and
everything a user needs must be inside it.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugin"

SHIPPED = {".claude-plugin", "skills", "templates", "docs", "README.md", "CHANGELOG.md", "LICENSE"}
SHIPPED_DOCS = {"suggestion.md", "concepts", "guardrails"}


def test_marketplace_installs_the_plugin_folder():
    market = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert [p["source"] for p in market["plugins"]] == ["./plugin"]


def test_plugin_folder_holds_only_shipped_parts():
    top = {p.name for p in PLUGIN.iterdir() if p.name != "__pycache__"}
    assert top == SHIPPED
    assert {p.name for p in (PLUGIN / "docs").iterdir()} == SHIPPED_DOCS


def test_no_tests_ship():
    # templates/ legitimately holds AGENTS.md, CLAUDE.md and .github/ for users' projects,
    # so the check is on test files, which never belong in the plugin.
    shipped_tests = [p for p in PLUGIN.rglob("*") if p.name == "tests" or p.name.startswith("test_")]
    assert shipped_tests == []


def test_root_keeps_development_files_only():
    for name in ("skills", "templates", "CHANGELOG.md"):
        assert not (REPO_ROOT / name).exists(), name
    assert (REPO_ROOT / "docs" / "design.md").is_file()
    assert not (REPO_ROOT / "docs" / "guardrails").exists()
    assert not (REPO_ROOT / "docs" / "suggestion.md").exists()


def test_plugin_license_matches_the_repository_license():
    assert (PLUGIN / "LICENSE").read_text() == (REPO_ROOT / "LICENSE").read_text()
