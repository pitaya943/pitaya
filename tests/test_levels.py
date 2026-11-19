"""plugin/docs/levels.md is generated from plugin/docs/components.json (D33).

Regenerate it with `python3 scripts/render_levels.py` after changing the
manifest; this test fails while the committed file is out of date. The recipes
README's "By level" table must agree with the manifest too.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugin"
LEVELS = PLUGIN / "docs" / "levels.md"
RENDER = REPO_ROOT / "scripts" / "render_levels.py"
MANIFEST = json.loads((PLUGIN / "docs" / "components.json").read_text())


def test_levels_md_is_up_to_date():
    proc = subprocess.run([sys.executable, str(RENDER), "--stdout"], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert LEVELS.read_text() == proc.stdout, "levels.md is stale: run python3 scripts/render_levels.py"


def test_every_component_appears_in_its_level_section():
    text = LEVELS.read_text()
    marks = list(re.finditer(r"^## Level (\d)\b", text, re.MULTILINE))
    assert [int(m.group(1)) for m in marks] == [0, 1, 2, 3]
    for i, m in enumerate(marks):
        body = text[m.start(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        for c in MANIFEST["components"]:
            if c["level"] == int(m.group(1)):
                assert f"`{c['id']}`" in body, c["id"]


def test_recipe_levels_match_the_recipes_readme():
    readme = (PLUGIN / "docs" / "guardrails" / "README.md").read_text()
    table = readme.split("## By level", 1)[1].split("\n## ", 1)[0]
    readme_levels = {}
    for row in table.splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if cells and cells[0].isdigit():
            for name in re.findall(r"\]\(([-\w]+)\.md\)", row):
                readme_levels[name] = int(cells[0])
    ours = {c["id"]: c["level"] for c in MANIFEST["components"] if c["kind"] == "recipe"}
    assert ours == readme_levels


def test_entry_points_link_to_the_inventory():
    for doc in ("README.md", "docs/suggestion.md", "docs/guardrails/README.md",
                "skills/setup/harness-template.md", "skills/setup/SKILL.md"):
        assert "levels.md" in (PLUGIN / doc).read_text(), doc
