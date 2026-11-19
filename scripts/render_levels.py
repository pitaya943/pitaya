#!/usr/bin/env python3
"""Render plugin/docs/levels.md from plugin/docs/components.json (D33).

    python3 scripts/render_levels.py            # rewrite plugin/docs/levels.md
    python3 scripts/render_levels.py --stdout   # print it instead

tests/test_levels.py fails while the committed file differs from this output,
so the manifest stays the single source for what each level includes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugin"
MANIFEST = PLUGIN / "docs" / "components.json"
OUT = PLUGIN / "docs" / "levels.md"

KIND = {"skill": "Skill", "template": "Files", "filled": "File, filled in", "recipe": "Recipe"}
LEVELS = {
    0: ("Level 0: skills only", "Install the plugin. Nothing in the repository changes. Without a harness file, "
        "the skills use safe defaults: the current account, the Owner merges, two fix rounds."),
    1: ("Level 1: the default", "Includes everything in Level 0. Run `/setup`; it copies the files and fills in the "
        "harness file. The Owner then makes the GitHub settings in protect-main."),
    2: ("Level 2: parallel agents", "Includes everything in Level 1. Add the recipes you need, one at a time; each is "
        "a copyable check that becomes a required status."),
    3: ("Level 3: long-running autonomy", "Includes everything in Level 2. `agent-merge` comes last: it requires the "
        "main Level 2 checks and a second-model review."),
}


def link(doc: str) -> str:
    """A plugin-relative path, as seen from plugin/docs/."""
    return doc.removeprefix("docs/") if doc.startswith("docs/") else f"../{doc}"


def ids(refs: list[str]) -> str:
    return ", ".join(f"`{r}`" for r in refs) or "-"


def item(c: dict) -> str:
    out = f"[`{c['id']}`]({link(c['doc'])})"
    if c["kind"] == "template":
        out += ": " + ", ".join(f"[`{f}`](../templates/{f})" for f in c["files"])
    elif c["kind"] == "filled":
        out += ": " + ", ".join(f"`{f}`" for f in c["files"])
    return out


def render(manifest: dict) -> str:
    lines = [
        "# What each level includes",
        "",
        "<!-- Generated from components.json. Edit the manifest, not this file. -->",
        "",
        "Every part of the harness by level: skills, files in your repository, guardrail recipes and the GitHub "
        "settings the Owner makes. Each level includes everything in the levels below it. **Requires** must be in "
        "place first; **Works better with** is optional. For what each part achieves and what it can't do, see "
        "[`suggestion.md`](suggestion.md).",
        "",
        "Every skill ships with the plugin, so all of them are installed from Level 0. A skill is listed at the "
        "level where it joins the recommended workflow.",
        "",
    ]
    for level, (title, intro) in LEVELS.items():
        lines += [f"## {title}", "", intro, "",
                  "| Kind | Component | Requires | Works better with | What it adds |",
                  "| --- | --- | --- | --- | --- |"]
        for c in manifest["components"]:
            if c["level"] == level:
                lines.append(f"| {KIND[c['kind']]} | {item(c)} | {ids(c.get('requires', []))} | "
                             f"{ids(c.get('recommends', []))} | {c['summary']} |")
        lines.append("")
    lines += ["## What the project needs", "",
              "Some components need something from the project itself, not from another component.", "",
              "| Need | Meaning | Needed by |", "| --- | --- | --- |"]
    for need, text in manifest["needs"].items():
        users = [c["id"] for c in manifest["components"] if need in c.get("needs", [])]
        lines.append(f"| `{need}` | {text} | {ids(users)} |")
    lines += [
        "",
        "## Choosing your own set",
        "",
        "Start from a level, then add or remove single components. "
        "[`select_components.py`](../skills/setup/scripts/select_components.py) adds whatever a component requires, "
        "refuses to remove something still required, warns about missing recommendations, and prints the steps in "
        "order. It only prints a plan; it copies nothing and changes no settings. Run it from the plugin's folder:",
        "",
        "```bash",
        "python3 skills/setup/scripts/select_components.py --level 1 --add scope --remove decisions",
        "```",
        "",
        "That run starts from Level 1, adds `scope` and the `machine-account` it requires, leaves out the decision "
        "log, and labels the result `Level 1 + scope, machine-account without decisions`. `/setup` records that label "
        "in the harness file.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stdout", action="store_true", help="print instead of writing the file")
    args = parser.parse_args()
    text = render(json.loads(MANIFEST.read_text()))
    if args.stdout:
        sys.stdout.write(text)
    else:
        OUT.write_text(text)
        print(f"wrote {OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
