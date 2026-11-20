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
    0: ("Level 0: skills only", "Install the plugin. Nothing in the repository changes. Closest to Matt Pocock's "
        "skills: the agent works in your session and you decide and merge everything. Without a harness file, the "
        "skills use safe defaults: the current account, the Owner merges, two fix rounds."),
    1: ("Level 1: the default", "Includes everything in Level 0. Run `/setup`; it copies the files and fills in the "
        "harness file. The Owner then makes the GitHub settings in protect-main."),
    2: ("Level 2: parallel agents", "Includes everything in Level 1. Add the recipes one at a time; each is a "
        "copyable check that becomes a required status."),
    3: ("Level 3: milestone autonomy", "Includes everything in Level 2. Agents merge ticket PRs into the milestone "
        "branch and `/autopilot` runs a milestone; the Owner signs off each milestone and approves each cut."),
    4: ("Level 4: max", "Includes everything in Level 3. Closest to pstack: the most agent authority, with the most "
        "verification. The Owner's gate is the milestone sign-off."),
}

# Who holds authority at each level: the spectrum from Matt Pocock's skills to pstack (D45).
AUTHORITY = [
    ("0", "Writes code in your session", "Every decision and every merge", "Your own review"),
    ("1", "Opens PRs, runs a fresh verifier", "Approves plans, merges every PR", "Hooks, CI, protected main"),
    ("2", "A Chief dispatches parallel builders", "Approves plans, merges every PR", "Ticket checks: scope, tests, evidence"),
    ("3", "Merges tickets into the milestone branch", "Signs off each milestone, approves each cut",
     "Verdict on the head from another session, milestone branch as blast radius"),
    ("4", "Also cuts the next milestone inside its branch", "Signs off each milestone, owns the roadmap",
     "Interrogation of high-risk PRs, a swarm and log audit per milestone, evals"),
]


# The threat model (D59): what every level takes for granted, and what that means for picking one.
ASSUMES = [
    "## What the levels assume",
    "",
    "pitaya assumes **cooperating agents**: agents that try to do the work as asked, and sometimes get it wrong. "
    "It defends against three things, in this order: its own rules contradicting each other or claiming to prove "
    "what they don't; honest mistakes, such as loosening a test to get green, editing CI, verifying one's own work "
    "or dropping changes in a merge; and text from outside (issues, PR comments, upstream code) steering an agent. "
    "It does not defend against an agent that sets out to get round it: one that forges a verdict, rewrites the "
    "workflow that judges it, sidesteps a hook or commits under another email. "
    "[Access](concepts/access.md#what-pitaya-assumes) lists where that line runs.",
    "",
    "What follows from it:",
    "",
    "- **Level 3 means agents you trust.** Every agent role uses one machine account, so the verdict that lets "
    "agents merge guards against mistakes, not forgery: it stops a stale or missing verification and a session "
    "passing its own work, not a session that lies about who it is.",
    "- **Don't run Levels 3 and 4 with agents, models or code you don't trust.** Below Level 3 a person reads and "
    "merges every PR, which is the defence those levels lack.",
    "- **Hooks prevent accidents.** They are not a security boundary: a script, another tool or a differently "
    "spelled command gets past them. The rulesets are the boundary.",
    "- **The tripwire is an `undisclosed` row** in a verdict's Attention section: a change or pivot the PR should "
    "have declared and didn't. When one appears, the Owner reviews it and decides whether the assumption still "
    "holds, or whether to add the stricter defences (a separate verifier account, checks that run from the base "
    "branch only, signed commits).",
    "",
]


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
        "level where it joins the recommended workflow. There is no custom mix: pick the level whose authority "
        "you want to give agents.",
        "",
        "## The spectrum",
        "",
        "Each level up gives agents more authority and adds the safeguards that authority needs. Level 0 is closest "
        "to Matt Pocock's skills, where a person decides and merges everything; Level 4 is closest to pstack, where "
        "agents run on their own. Pick a lower level for a project you want to keep close control of.",
        "",
        "| Level | Agent authority | What the Owner does | What keeps it safe |",
        "| --- | --- | --- | --- |",
    ] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in AUTHORITY] + [""] + ASSUMES
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
