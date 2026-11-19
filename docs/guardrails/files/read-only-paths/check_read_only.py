#!/usr/bin/env python3
# pitaya template 0.1.0 · docs/guardrails/files/read-only-paths/check_read_only.py
"""Guardrail "read-only-paths": a ticket PR can't change rules, specs or CI.

Usage (from the repository root, in CI)::

    python3 check_read_only.py --base <base sha> --head <head sha> --ticket ticket.md [--also "docs/spec/**,..."]

Read-only by default: every AGENTS.md and CLAUDE.md, docs/agents/**, .claude/**,
.github/** and docs/decisions.md. Add the project's specs with --also (comma
separated globs) or the READ_ONLY_PATHS constant below.

The one exception: a path the ticket's "## Scope" section lists **exactly**,
with no wildcard, because the Owner approved changing that file. A glob in the
scope never unlocks a read-only path.

When to remove: when rule and spec files sit behind a CODEOWNERS review the
agents can't satisfy, which enforces the same thing at merge time.

Exit 0 when no read-only path changed, 1 otherwise. Standard library and git only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

READ_ONLY_PATHS = [
    "AGENTS.md", "**/AGENTS.md", "CLAUDE.md", "**/CLAUDE.md",
    "docs/agents/**", ".claude/**", ".github/**", "docs/decisions.md",
]


def ticket_section(text: str, title: str) -> list[str] | None:
    """Bullet items under "## <title>", backticks stripped; None if the section is missing."""
    items, inside = None, False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip().lower().replace("-", " ") == title.lower().replace("-", " ")
            if inside:
                items = []
            continue
        match = re.match(r"\s*(?:[-*]|\d+\.)\s+(.*)", line) if inside else None
        if match:
            items.append(match.group(1).strip().strip("`").strip())
    return items


def glob_to_regex(pattern: str) -> re.Pattern:
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def changed_files(base: str, head: str) -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", "--no-renames", f"{base}...{head}"],
                         capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that a ticket PR leaves read-only paths alone.")
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--ticket", required=True, type=Path)
    parser.add_argument("--also", default="", help="extra read-only globs, comma separated")
    args = parser.parse_args(argv)

    globs = READ_ONLY_PATHS + [g.strip() for g in args.also.split(",") if g.strip()]
    patterns = [glob_to_regex(g) for g in globs]
    # Only an exact string match unlocks a path; a glob never equals a real path.
    exact = set(ticket_section(args.ticket.read_text(), "Scope") or [])
    touched = [f for f in changed_files(args.base, args.head)
               if any(p.match(f) for p in patterns) and f not in exact]
    if touched:
        print("FAIL read-only-paths: this PR changes read-only files:")
        for path in touched:
            print(f"  {path}")
        print("To fix: revert these changes. If the ticket really needs one of them, ask the Owner to "
              "list that exact file (no wildcard) in the ticket's \"## Scope\" section.")
        return 1
    print("PASS read-only-paths: no read-only file changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
