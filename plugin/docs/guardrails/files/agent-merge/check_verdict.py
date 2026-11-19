#!/usr/bin/env python3
# pitaya template 0.1.0 · docs/guardrails/files/agent-merge/check_verdict.py
"""Guardrail "agent-merge": a PASS verdict exists for the pull request's current head commit.

Usage (in CI)::

    gh api "repos/$REPO/issues/$PR/comments" --paginate > comments.json
    python3 check_verdict.py --comments comments.json --head <head sha> --verifiers <logins>

A verdict is a comment from an allowed verifier account that starts with
"## Verification: PASS" or "## Verification: FAIL" and names a "Head commit:"
(the `/verify` template). Only verdicts for the current head count, so any new
push voids an earlier PASS; the latest of those wins. Comments from anyone
else, including the account that built the work, are ignored.

When to remove: when agents no longer merge on their own, and a person reads
every verdict before merging.

Exit 0 when the latest verdict for this head is PASS, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RESULT_RE = re.compile(r"^##\s*Verification:\s*(PASS|FAIL)\b", re.M)
HEAD_RE = re.compile(r"Head commit:\s*`?([0-9a-f]{7,40})", re.I)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check for a PASS verdict on the current head.")
    parser.add_argument("--comments", required=True, type=Path, help="JSON from the issue comments API")
    parser.add_argument("--head", required=True, help="the pull request's head commit")
    parser.add_argument("--verifiers", required=True, help="logins allowed to post verdicts, comma separated")
    args = parser.parse_args(argv)

    verifiers = {v.strip().lower() for v in args.verifiers.split(",") if v.strip()}
    if not verifiers:
        print("FAIL agent-merge: no verifier accounts were given.")
        print("To fix: set the repository variable VERIFIER_ACCOUNTS to the verifier's GitHub login, "
              "an account the builder can't post as.")
        return 1
    latest = None
    for comment in json.loads(args.comments.read_text()):
        login = ((comment.get("user") or {}).get("login") or "").lower()
        body = comment.get("body") or ""
        result, head = RESULT_RE.search(body), HEAD_RE.search(body)
        if login in verifiers and result and head and args.head.lower().startswith(head.group(1).lower()):
            latest = result.group(1)
    if latest != "PASS":
        state = "FAIL" if latest == "FAIL" else "no verdict"
        print(f"FAIL agent-merge: the latest verdict for head {args.head[:7]} is {state}.")
        print("To fix: run /verify on the current head (a new push voids earlier verdicts) and fix "
              "what it reports; only a PASS for this exact commit lets the pull request merge.")
        return 1
    print(f"PASS agent-merge: the latest verdict for head {args.head[:7]} is PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
