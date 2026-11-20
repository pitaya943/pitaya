#!/usr/bin/env python3
# pitaya template 0.1.2 · docs/guardrails/files/evidence/check_evidence.py
"""Guardrail "evidence": the PR description shows evidence, and screenshots when the ticket requires them.

Usage (from the repository root, in CI)::

    python3 check_evidence.py --pr-body body.md --ticket ticket.md --base <base sha> --head <head sha>

The PR description needs a "## Evidence" section holding at least one code
block (commands and their output) or link. When the ticket's "## Screenshots"
says "required", the section must also show an image, or the PR must add an
image under docs/evidence/.

It checks that evidence is there, not that it's true: the verifier re-runs it.

When to remove: when the verifier's verdict, which re-runs everything, is
required for every merge and the PR description no longer matters.

Exit 0 when the evidence is there, 1 otherwise. Standard library and git only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


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


def changed_files(base: str, head: str) -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", "--no-renames", f"{base}...{head}"],
                         capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def body_section(text: str, title: str) -> str | None:
    """The raw text under "## <title>" in the PR description, or None."""
    match = re.search(rf"^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return match.group(1) if match else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that a PR description carries evidence.")
    parser.add_argument("--pr-body", required=True, type=Path)
    parser.add_argument("--ticket", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args(argv)

    section = body_section(args.pr_body.read_text(), "Evidence")
    if section is None:
        print("FAIL evidence: the PR description has no \"## Evidence\" section.")
        print("To fix: add a \"## Evidence\" section with the commands you ran and their output in a code block, "
              "or links to CI runs and screenshots.")
        return 1
    has_code = "`" * 3 in section
    has_link = re.search(r"\]\([^)]+\)|https?://", section) is not None
    if not (has_code or has_link):
        print("FAIL evidence: the \"## Evidence\" section has no code block or link, only prose.")
        print("To fix: paste the commands and their real output in a code block, or link the CI run.")
        return 1
    wanted = " ".join(ticket_section(args.ticket.read_text(), "Screenshots") or []).lower()
    if "required" in wanted and "not required" not in wanted:
        image_link = re.search(r"!\[[^\]]*\]\([^)]+\)", section) is not None
        image_file = any(f.startswith("docs/evidence/") and f.lower().endswith(IMAGE_EXTENSIONS)
                         for f in changed_files(args.base, args.head))
        if not (image_link or image_file):
            print("FAIL evidence: the ticket requires screenshots, and the PR shows none.")
            print("To fix: take screenshots of the working feature yourself, add them under "
                  "docs/evidence/<ticket>/ or as images in the \"## Evidence\" section.")
            return 1
    print("PASS evidence: the PR description carries evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
