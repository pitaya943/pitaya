#!/usr/bin/env python3
# pitaya template 0.1.0 · docs/guardrails/files/serial-resources/check_serial.py
"""Guardrail "serial-resources": only one open ticket at a time changes a shared resource.

Usage (in CI)::

    python3 check_serial.py --ticket ticket.md --others other-tickets/ --known "migrations,lockfile"

The ticket's "## Serial resources" lists resources such as database
migrations or a lockfile, where two PRs that are each fine can conflict once
both merge. Each must be one of --known. `other-tickets/` holds the tickets of
the other open PRs, one file each; a resource claimed by any of them fails.

When to remove: when the resource can't conflict any more, for example
migrations are generated with timestamps and merged in order by a merge queue.

Exit 0 when nothing is claimed twice, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import re
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that no other open ticket claims the same serial resource.")
    parser.add_argument("--ticket", required=True, type=Path)
    parser.add_argument("--others", required=True, type=Path, help="directory with the other open PRs' tickets")
    parser.add_argument("--known", required=True, help="the project's serial resources, comma separated")
    args = parser.parse_args(argv)

    mine = ticket_section(args.ticket.read_text(), "Serial resources") or []
    known = {k.strip() for k in args.known.split(",") if k.strip()}
    unknown = [r for r in mine if r not in known]
    if unknown:
        print(f"FAIL serial-resources: unknown resources: {', '.join(unknown)} (known: {', '.join(sorted(known))}).")
        print("To fix: use one of the known names in the ticket, or ask the Owner to add the resource "
              "to the workflow's SERIAL_RESOURCES.")
        return 1
    clashes = []
    if args.others.is_dir():
        for other in sorted(args.others.glob("*.md")):
            theirs = set(ticket_section(other.read_text(), "Serial resources") or [])
            clashes += [f"{r}: also claimed by {other.stem}" for r in mine if r in theirs]
    if clashes:
        print("FAIL serial-resources: another open pull request is changing the same resource:")
        for line in clashes:
            print(f"  {line}")
        print("To fix: wait until that pull request merges or closes, then update this branch and re-run.")
        return 1
    print("PASS serial-resources: no other open ticket claims the same resource.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
