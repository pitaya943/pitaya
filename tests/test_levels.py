"""plugin/docs/levels.md lists exactly what each level includes.

It is the one inventory users read to see which skills, files and recipes
belong to a level. These tests keep it in step with what actually ships:

* every skill, every copied template and every recipe appears in exactly one
  level, and nothing listed is missing from the plugin;
* the harness file, which /setup fills in rather than copies, is listed at
  Level 1 by its template;
* each recipe's level agrees with the "By level" table in the recipes README.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugin"
LEVELS = PLUGIN / "docs" / "levels.md"
RECIPES_README = PLUGIN / "docs" / "guardrails" / "README.md"

LEVEL_HEADING = re.compile(r"^## Level (\d)\b", re.MULTILINE)
SKILL_LINK = re.compile(r"\]\(\.\./skills/([-\w]+)/SKILL\.md\)")
TEMPLATE_LINK = re.compile(r"\]\(\.\./templates/([^)\s]+)\)")
RECIPE_LINK = re.compile(r"\]\(guardrails/([-\w]+)\.md\)")
HARNESS_TEMPLATE = "](../skills/setup/harness-template.md)"


def sections() -> dict[int, str]:
    text = LEVELS.read_text()
    marks = list(LEVEL_HEADING.finditer(text))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[int(m.group(1))] = text[m.start():end]
    return out


def listed(pattern: re.Pattern) -> dict[str, list[int]]:
    found: dict[str, list[int]] = {}
    for level, body in sections().items():
        for item in pattern.findall(body):
            found.setdefault(item, []).append(level)
    return found


def shipped_skills() -> set[str]:
    return {p.parent.name for p in (PLUGIN / "skills").glob("*/SKILL.md")}


def copied_templates() -> set[str]:
    root = PLUGIN / "templates"
    return {p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and p.name != "README.md"}


def shipped_recipes() -> set[str]:
    return {p.stem for p in (PLUGIN / "docs" / "guardrails").glob("*.md") if p.name != "README.md"}


def test_levels_0_to_3_each_have_a_section():
    assert sorted(sections()) == [0, 1, 2, 3]


def test_every_skill_is_listed_once():
    found = listed(SKILL_LINK)
    assert set(found) == shipped_skills()
    assert {k: v for k, v in found.items() if len(v) > 1} == {}


def test_every_copied_template_is_listed_once():
    found = listed(TEMPLATE_LINK)
    assert set(found) == copied_templates()
    assert {k: v for k, v in found.items() if len(v) > 1} == {}


def test_every_recipe_is_listed_once():
    found = listed(RECIPE_LINK)
    assert set(found) == shipped_recipes()
    assert {k: v for k, v in found.items() if len(v) > 1} == {}


def test_harness_file_is_listed_at_level_1_by_its_template():
    assert HARNESS_TEMPLATE in sections()[1]
    assert "docs/agents/harness.md" in sections()[1]


def test_recipe_levels_match_the_recipes_readme():
    readme = RECIPES_README.read_text()
    table = readme.split("## By level", 1)[1].split("\n## ", 1)[0]
    readme_levels = {}
    for row in table.splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if cells and cells[0].isdigit():
            for name in re.findall(r"\]\(([-\w]+)\.md\)", row):
                readme_levels[name] = int(cells[0])
    ours = {name: levels[0] for name, levels in listed(RECIPE_LINK).items()}
    assert ours == readme_levels


def test_entry_points_link_to_the_inventory():
    for doc in ("README.md", "docs/suggestion.md", "docs/guardrails/README.md",
                "skills/setup/harness-template.md"):
        assert "levels.md" in (PLUGIN / doc).read_text(), doc


def test_levels_are_counted_consistently():
    # Each section says it includes the levels below it, so the list stays cumulative.
    for level, body in sections().items():
        if level > 0:
            assert f"everything in Level {level - 1}" in body[:600], level


def test_no_item_is_listed_twice_in_one_section():
    for level, body in sections().items():
        items = SKILL_LINK.findall(body) + TEMPLATE_LINK.findall(body) + RECIPE_LINK.findall(body)
        dupes = [k for k, n in Counter(items).items() if n > 1]
        assert dupes == [], (level, dupes)
