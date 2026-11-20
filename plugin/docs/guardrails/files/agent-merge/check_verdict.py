#!/usr/bin/env python3
# pitaya template 0.1.3 · docs/guardrails/files/agent-merge/check_verdict.py
"""Guardrail "agent-merge": a PASS verdict exists for the pull request's current head commit.

Usage (in CI)::

    gh api "repos/$REPO/issues/$PR/comments" --paginate > comments.json
    gh api "repos/$REPO/pulls/$PR/reviews" --paginate > reviews.json
    python3 check_verdict.py --comments comments.json --reviews reviews.json \
        --head <head sha> --verifiers <logins> --branch <head branch>

A verdict comes from an allowed verifier account, for the current head commit:

- a comment that starts with "## Verification: PASS" or "## Verification: FAIL"
  and names a "Head commit:" (the `/verify` template). With one machine account
  the verifier posts as that account, and GitHub doesn't let an author approve
  its own pull request, so this is the usual form. Edited comments don't count.
- a pull request review from a verifier account on that commit: "Approve" is
  PASS, "Request changes" is FAIL. Dismissed reviews don't count.

Any new push voids earlier verdicts. A FAIL on this head is final until the
next push. Plan PRs (`plan/<slug>`) and milestone PRs (`milestone/<id>`) never
pass on a verdict: the Owner merges those.

When to remove: when agents no longer merge on their own, and a person reads
every verdict before merging.

Exit 0 when this head has a PASS and no FAIL from a verifier, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RESULT_RE = re.compile(r"^##\s*Verification:\s*(PASS|FAIL)\b", re.M)
HEAD_RE = re.compile(r"Head commit:\s*`?([0-9a-f]{7,40})", re.I)


def fail(message: str, fix: str) -> int:
    print(f"FAIL agent-merge: {message}")
    print(f"To fix: {fix}")
    return 1


def load(path: Path | None) -> list[dict]:
    return json.loads(path.read_text()) if path and path.exists() else []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check for a PASS verdict on the current head.")
    parser.add_argument("--comments", type=Path, help="JSON from the issue comments API")
    parser.add_argument("--reviews", type=Path, help="JSON from the pull request reviews API")
    parser.add_argument("--head", required=True, help="the pull request's head commit")
    parser.add_argument("--verifiers", required=True, help="logins allowed to give verdicts, comma separated")
    parser.add_argument("--branch", default="", help="the pull request's head branch")
    args = parser.parse_args(argv)

    verifiers = {v.strip().lower() for v in args.verifiers.split(",") if v.strip()}
    if not verifiers:
        return fail("no verifier accounts were given.",
                    "set the repository variable VERIFIER_ACCOUNTS, or MACHINE_ACCOUNT, to the login "
                    "the verifier posts as.")
    if args.branch.startswith(("plan/", "milestone/")):
        return fail("this is a plan or milestone PR; it needs the Owner's review, not a verdict.",
                    "ask the Owner to review and merge it.")

    head = args.head.lower()
    results = []
    for c in load(args.comments):
        login = ((c.get("user") or {}).get("login") or "").lower()
        body = c.get("body") or ""
        result, named = RESULT_RE.search(body), HEAD_RE.search(body)
        edited = c.get("updated_at") and c.get("updated_at") != c.get("created_at")
        if login in verifiers and result and named and not edited and head.startswith(named.group(1).lower()):
            results.append(result.group(1))
    for r in load(args.reviews):
        login = ((r.get("user") or {}).get("login") or "").lower()
        if login in verifiers and (r.get("commit_id") or "").lower() == head:
            results.append({"APPROVED": "PASS", "CHANGES_REQUESTED": "FAIL"}.get(r.get("state"), ""))

    if "FAIL" in results:
        return fail(f"a verifier reported FAIL on head {args.head[:7]}.",
                    "fix what the verdict reports and push; the new head needs a new /verify.")
    if "PASS" not in results:
        return fail(f"no PASS verdict for head {args.head[:7]}.",
                    "run /verify on the current head (a new push voids earlier verdicts) and fix what it reports.")
    print(f"PASS agent-merge: a verifier passed head {args.head[:7]}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
