"""Every guardrail recipe follows the eight-section format (docs/design.md, section 9.1)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugin"
GUARDRAILS = PLUGIN_ROOT / "docs" / "guardrails"
VERSION = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]

SECTIONS = [
    "## What it guards against",
    "## When it's worth adding",
    "## How to add it",
    "## How to prove it works",
    "## Cost and false positives",
    "## Error message",
    "## Afterwards",
    "## When to remove it",
]
# recipe id -> level
RECIPES = {
    "protect-main": 1,
    "machine-account": 2,
    "scope": 2,
    "read-only-paths": 2,
    "no-weakened-tests": 2,
    "done-when": 2,
    "commit-author": 2,
    "append-only": 2,
    "serial-resources": 2,
    "evidence": 2,
    "progress-file": 3,
    "agent-merge": 3,
    "second-model-review": 4,
    "project-evals": 4,
    "multi-account": 2,
    "verify-app": 2,
}


@pytest.mark.parametrize("recipe", RECIPES)
def test_recipe_has_every_section_in_order(recipe):
    text = (GUARDRAILS / f"{recipe}.md").read_text()
    positions = [text.find(s) for s in SECTIONS]
    assert all(p >= 0 for p in positions), [s for s, p in zip(SECTIONS, positions) if p < 0]
    assert positions == sorted(positions)


@pytest.mark.parametrize("recipe, level", RECIPES.items())
def test_recipe_states_its_level(recipe, level):
    assert f"Level: {level}" in (GUARDRAILS / f"{recipe}.md").read_text()


@pytest.mark.parametrize("recipe", RECIPES)
def test_index_links_every_recipe(recipe):
    assert f"]({recipe}.md)" in (GUARDRAILS / "README.md").read_text()


def copyable_files() -> list[Path]:
    root = GUARDRAILS / "files"
    return sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else []


@pytest.mark.parametrize("path", copyable_files(), ids=lambda p: p.relative_to(GUARDRAILS).as_posix())
def test_copyable_file_header_names_this_version(path):
    if path.suffix == ".json":
        return  # JSON can't carry a comment; its recipe names the version instead
    head = "\n".join(path.read_text().splitlines()[:3])
    match = re.search(r"pitaya template (\S+)", head)
    assert match and match.group(1) == VERSION


@pytest.mark.parametrize("path", copyable_files(), ids=lambda p: p.relative_to(GUARDRAILS).as_posix())
def test_copyable_file_is_referenced_by_its_recipe(path):
    recipe = path.relative_to(GUARDRAILS / "files").parts[0]
    assert path.name in (GUARDRAILS / f"{recipe}.md").read_text()


@pytest.mark.parametrize("path", [p for p in copyable_files() if p.suffix == ".py"],
                         ids=lambda p: p.name)
def test_check_scripts_say_when_to_remove_and_how_to_fix(path):
    text = path.read_text()
    assert "When to remove" in text
    assert "To fix:" in text
