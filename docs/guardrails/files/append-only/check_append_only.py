#!/usr/bin/env python3
# pitaya template 0.1.0 · docs/guardrails/files/append-only/check_append_only.py
"""Guardrail "append-only": listed files only gain lines in a PR.

Usage (from the repository root, in CI)::

    python3 check_append_only.py --base <base sha> --head <head sha> --files "CHANGELOG.md,docs/decisions.md" [--ticket ticket.md]

Files come from --files and, optionally, the ticket's "## Append-only files"
section. A changed or removed line, or deleting the file, fails. Creating the
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


def removed_lines(base: str, head: str, path: str) -> list[str]:
    diff = subprocess.run(["git", "diff", "--unified=0", "--no-renames", f"{base}...{head}", "--", path],
                          capture_output=True, text=True, check=True).stdout
    return [line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]


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
        lines = removed_lines(args.base, args.head, path)
        if lines:
            problems[path] = lines
    if problems:
        print("FAIL append-only: these files lost or changed lines:")
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
