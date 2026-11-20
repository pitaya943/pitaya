#!/usr/bin/env python3
# pitaya template 0.1.6 · docs/guardrails/files/done-when/check_done_when.py
"""Guardrail "done-when": every test the ticket names exists in the PR's results and passes.

Usage (in CI, after running the test command on the PR head)::

    python3 check_done_when.py --junit head-junit.xml --ticket ticket.md

The ticket's "## Test IDs" section lists one test ID per done-when condition,
as JUnit reports it ("classname::name", for pytest "tests.test_cli::test_x") or
as a pytest path ("tests/test_cli.py::test_x", "tests/test_x.py::TestC::test_y"),
which is converted to the JUnit form. An ID without parameters also stands for
every parametrized case of that test ("test_x[1]", "test_x[2]"): all of them
must pass. A listed test that's missing, failing or skipped means a condition
claimed done isn't shown to be done.

When to remove: when the verifier's checklist reliably catches untested
conditions and the extra ticket field costs more than it saves.

Exit 0 when every listed test passes, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
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


def load_results(path: Path) -> dict[str, str]:
    """Map "classname::name" to "passed", "failed" or "skipped". Raises ValueError if unreadable."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"can't read {path}: {exc}") from exc
    results = {}
    for case in root.iter("testcase"):
        test_id = f"{case.get('classname', '')}::{case.get('name', '')}"
        if case.find("failure") is not None or case.find("error") is not None:
            results[test_id] = "failed"
        elif case.find("skipped") is not None:
            results[test_id] = "skipped"
        else:
            results[test_id] = "passed"
    return results


def junit_id(test_id: str) -> str:
    """"tests/test_x.py::TestC::test_y" -> "tests.test_x.TestC::test_y"; JUnit-form IDs are unchanged."""
    parts = test_id.split("::")
    if len(parts) >= 2 and parts[0].endswith(".py"):
        module = parts[0][:-3].replace("/", ".")
        return ".".join([module, *parts[1:-1]]) + "::" + parts[-1]
    return test_id


def outcome(test_id: str, results: dict[str, str]) -> list[str]:
    """Problems for one listed ID: [] when it passes. An ID without "[" covers its parametrized cases."""
    wanted = junit_id(test_id)
    if wanted in results:
        return [] if results[wanted] == "passed" else [f"{test_id}: {results[wanted]}"]
    if "[" not in wanted:
        cases = {k: v for k, v in results.items() if k.startswith(wanted + "[") and k.endswith("]")}
        if cases:
            return [f"{k}: {v}" for k, v in sorted(cases.items()) if v != "passed"]
    return [f"{test_id}: missing"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that every done-when test passes.")
    parser.add_argument("--junit", required=True, type=Path)
    parser.add_argument("--ticket", required=True, type=Path)
    args = parser.parse_args(argv)

    wanted = ticket_section(args.ticket.read_text(), "Test IDs")
    if not wanted:
        print("FAIL done-when: the ticket has no \"## Test IDs\" section, or it's empty.")
        print("To fix: add a \"## Test IDs\" section to the ticket with one test ID (classname::name) "
              "per done-when condition, in order.")
        return 1
    try:
        results = load_results(args.junit)
    except ValueError as exc:
        print(f"FAIL done-when: {exc}")
        print("To fix: make the test command write JUnit XML to the path the workflow expects.")
        return 1
    problems = [line for t in wanted for line in outcome(t, results)]
    if problems:
        print("FAIL done-when: these done-when tests don't pass:")
        for line in problems:
            print(f"  {line}")
        print("To fix: write or fix the test for each condition so it runs and passes under exactly "
              "this ID, or ask the Owner to correct the ID in the ticket.")
        return 1
    print(f"PASS done-when: all {len(wanted)} done-when tests pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
