#!/usr/bin/env python3
# pitaya template 0.1.5 · docs/guardrails/files/append-only/check_append_only.py
"""Guardrail "append-only": listed files only gain lines in a PR.

Usage (from the repository root, in CI)::

    python3 check_append_only.py --base <base sha> --head <head sha> --files "CHANGELOG.md,docs/decisions.md" [--ticket ticket.md]

Files come from --files and, optionally, the ticket's "## Append-only files"
section. A changed or removed line, a line inserted between old ones, or deleting
the file, fails: new lines go after the last existing one. Creating the
file is fine.

When to remove: when the files are generated (for example a changelog built
from fragments), so nobody edits them by hand.

Exit 0 when the files only gained lines, 1 otherwise. Standard library and git only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


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


def show(rev: str, path: str) -> str | None:
    out = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def broken_lines(base: str, head: str, path: str) -> list[str]:
    """Lines that break append-only: old lines changed or removed, or new lines placed before the end."""
    merge_base = subprocess.run(["git", "merge-base", base, head], capture_output=True,
                                text=True, check=True).stdout.strip()
    old, new = show(merge_base, path), show(head, path)
    if old is None:
        return []  # a new file: everything in it is an addition
    if new is None:
        return ["(the file was deleted)"]
    old_lines, new_lines = old.splitlines(), new.splitlines()
    if new_lines[:len(old_lines)] == old_lines:
        return []
    # Report the first place they part ways, and what the PR has there.
    for i, line in enumerate(old_lines):
        if i >= len(new_lines) or new_lines[i] != line:
            shown = new_lines[i] if i < len(new_lines) else "(missing)"
            return [f"line {i + 1}: was {line!r}, now {shown!r}"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that append-only files only gained lines.")
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--files", default="", help="append-only files, comma separated")
    parser.add_argument("--ticket", type=Path, help="ticket with an optional \"## Append-only files\" section")
    args = parser.parse_args(argv)

    files = [f.strip() for f in args.files.split(",") if f.strip()]
    if args.ticket:
        files += ticket_section(args.ticket.read_text(), "Append-only files") or []
    problems = {}
    for path in dict.fromkeys(files):
        lines = broken_lines(args.base, args.head, path)
        if lines:
            problems[path] = lines
    if problems:
        print("FAIL append-only: these files changed before their last original line:")
        for path, lines in problems.items():
            print(f"  {path}:")
            for line in lines[:10]:
                print(f"    - {line}")
        print("To fix: restore the original lines and add your change as new lines at the end, "
              "for example a new entry that supersedes the old one.")
        return 1
    print("PASS append-only: the listed files only gained lines.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
