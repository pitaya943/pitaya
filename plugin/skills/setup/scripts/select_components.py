#!/usr/bin/env python3
"""Choose harness components: a level preset, plus or minus single parts.

Reads the plugin's docs/components.json and prints a plan. It writes nothing
and changes no settings: copying templates stays with install_templates.py,
and adding a guardrail stays rule work for the Owner or a ticket.

    python3 select_components.py --level 1
    python3 select_components.py --level 1 --add scope --remove decisions
    python3 select_components.py --level 2 --json

How it decides:

* A level is a preset: every component whose level is at or below it.
* `--add ID` adds a component, and everything it requires, recursively. What
  was pulled in this way is reported with the components that needed it.
* `--remove ID` takes one out. If a selected component still requires it, the
  run fails and names that component, instead of silently dropping either.
* Missing recommendations are warnings, not errors.
* Steps come out in dependency order: nothing before what it requires.

Output: a readable plan, or JSON with `--json`. Exit 0 on success, 2 on an
unknown id or a removal something still needs. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = PLUGIN_ROOT / "docs" / "components.json"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def closure(start: set[str], comps: dict[str, dict]) -> set[str]:
    """`start` plus everything it requires, recursively."""
    out, todo = set(), list(start)
    while todo:
        cid = todo.pop()
        if cid not in out:
            out.add(cid)
            todo.extend(comps[cid].get("requires", []))
    return out


def ordered(selected: set[str], comps: dict[str, dict], rank: dict[str, int]) -> list[str]:
    """Dependency order; among ready components, the manifest's own order (stable and readable)."""
    done: list[str] = []
    left = set(selected)
    while left:
        ready = [c for c in left if set(comps[c].get("requires", [])) <= set(done)]
        nxt = min(ready, key=rank.__getitem__)  # the manifest has no cycles (tested)
        done.append(nxt)
        left.remove(nxt)
    return done


def how(c: dict) -> str:
    return {
        "skill": "skill, installed with the plugin",
        "template": "copied by /setup",
        "filled": "filled in by /setup",
    }.get(c["kind"]) or f"follow {c['doc']}"


def select(manifest: dict, level: int, add: list[str], remove: list[str]) -> dict:
    comps = {c["id"]: c for c in manifest["components"]}
    rank = {c["id"]: i for i, c in enumerate(manifest["components"])}
    unknown = [c for c in add + remove if c not in comps]
    if unknown:
        fail(f"unknown component: {', '.join(unknown)}\n"
             f"To fix: use an id from {DEFAULT_MANIFEST.name}, for example {', '.join(list(comps)[:3])}.")

    preset = {cid for cid, c in comps.items() if c["level"] <= level}
    wanted = (preset | set(add)) - set(remove)
    selected = closure(wanted, comps)

    clashes = sorted(set(remove) & selected)
    if clashes:
        lines = []
        for r in clashes:
            needers = sorted(c for c in selected if r in comps[c].get("requires", []) and c not in remove)
            lines.append(f"can't remove {r}: it is required by {', '.join(needers)}.")
        fail("\n".join(lines) + "\nTo fix: remove those components as well, or keep "
             + ", ".join(clashes) + ".")

    added_for = {
        cid: sorted(c for c in selected if cid in comps[c].get("requires", []))
        for cid in sorted(selected - wanted, key=rank.__getitem__)
    }
    order = ordered(selected, comps, rank)
    extra = [c for c in add if c not in preset] + list(added_for)
    label = f"Level {level}"
    if extra:
        label += " + " + ", ".join(dict.fromkeys(extra))
    removed = [r for r in remove if r in preset]
    if removed:
        label += " without " + ", ".join(removed)

    warnings = [f"{cid} recommends {r}, which isn't selected"
                for cid in order for r in comps[cid].get("recommends", []) if r not in selected]
    needs = {n: manifest["needs"][n] for cid in order for n in comps[cid].get("needs", [])}
    templates = [c for c in manifest["components"] if c["kind"] == "template"]
    install_args: list[str] = []
    if any(c["id"] in selected for c in templates):
        for c in templates:
            if c["id"] not in selected:
                for f in c["files"]:
                    install_args += ["--skip", f]

    return {
        "label": label,
        "selected": order,
        "added_for": added_for,
        "warnings": warnings,
        "needs": needs,
        "install_args": install_args,
        "copies_templates": any(c["id"] in selected for c in templates),
        "steps": [{"id": cid, "how": how(comps[cid]), "summary": comps[cid]["summary"]} for cid in order],
    }


def show(plan: dict) -> None:
    print(f"Selection: {plan['label']}")
    print("This only prints a plan: it copies nothing and changes no settings.\n")
    print("Steps, in order:")
    for i, step in enumerate(plan["steps"], 1):
        print(f"  {i:>2}. {step['id']:<20} {step['how']}")
    if plan["added_for"]:
        print("\nAdded because something requires it:")
        for cid, by in plan["added_for"].items():
            print(f"  {cid} (required by {', '.join(by)})")
    if plan["needs"]:
        print("\nThe project needs:")
        for name, text in plan["needs"].items():
            print(f"  {name}: {text}")
    if plan["warnings"]:
        print("\nWarnings:")
        for w in plan["warnings"]:
            print(f"  {w}")
    print()
    if plan["copies_templates"]:
        args = " ".join(f'"{a}"' if " " in a else a for a in plan["install_args"])
        print(f"Install the templates with: install_templates.py --level 1 --test-command \"<cmd>\" {args}".rstrip())
    else:
        print("No templates to copy (skills only).")
    print(f"Write this selection under \"Level\" in docs/agents/harness.md: {plan['label']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Choose harness components: a level preset, plus or minus single parts.")
    parser.add_argument("--level", type=int, choices=(0, 1, 2, 3), required=True, help="the preset to start from")
    parser.add_argument("--add", action="append", default=[], metavar="ID", help="add a component and what it requires")
    parser.add_argument("--remove", action="append", default=[], metavar="ID", help="leave a component out")
    parser.add_argument("--json", action="store_true", help="print the plan as JSON")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)

    plan = select(json.loads(args.manifest.read_text()), args.level, args.add, args.remove)
    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        show(plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
