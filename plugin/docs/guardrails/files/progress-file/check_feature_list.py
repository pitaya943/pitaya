#!/usr/bin/env python3
# pitaya template 0.1.3 · docs/guardrails/files/progress-file/check_feature_list.py
"""Guardrail "progress-file": in the feature list, agents may only change "passes".

Usage (in CI)::

    git show origin/main:docs/progress/features.json > base.json
    python3 check_feature_list.py --base base.json --head docs/progress/features.json

The feature list holds the work's requirements, each with an id, a
description, steps to check it and a "passes" flag. During long autonomous
work, the quiet failure is the scope shrinking: a requirement deleted or
reworded until what was built satisfies it. So on a PR, every feature on the
base must still exist with the same description and steps; only "passes" may
change. New features come from the Owner, not from agents.

When to remove: when the work isn't long-running any more, or when models
reliably keep requirements intact on their own across long sessions.

Exit 0 when only "passes" changed, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text())
    return {f["id"]: f for f in data["features"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that a PR only changes the 'passes' flags.")
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--head", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        base, head = load(args.base), load(args.head)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL progress-file: can't read the feature list: {exc}")
        print('To fix: keep the file valid JSON shaped {"features": [{"id", "description", "steps", "passes"}]}.')
        return 1
    problems = []
    for fid, feature in base.items():
        now = head.get(fid)
        if now is None:
            problems.append(f"{fid}: removed")
            continue
        for key in sorted(set(feature) | set(now)):
            if key != "passes" and feature.get(key) != now.get(key):
                problems.append(f"{fid}: {key} changed")
    problems += [f"{fid}: added" for fid in head if fid not in base]
    if problems:
        print("FAIL progress-file: the feature list changed beyond \"passes\":")
        for line in problems:
            print(f"  {line}")
        print("To fix: restore the features as they were and change only \"passes\". If a requirement "
              "really is wrong or missing, ask the Owner to change the list in their own pull request.")
        return 1
    done = sum(1 for f in head.values() if f.get("passes"))
    print(f"PASS progress-file: only \"passes\" changed ({done}/{len(head)} features pass).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
