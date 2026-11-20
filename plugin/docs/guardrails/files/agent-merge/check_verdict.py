#!/usr/bin/env python3
# pitaya template 0.1.0 · docs/guardrails/files/agent-merge/check_verdict.py
"""Guardrail "agent-merge": a PASS review exists for the pull request's current head commit.

Usage (in CI)::

    gh api "repos/$REPO/pulls/$PR/reviews" --paginate > reviews.json
    python3 check_verdict.py --reviews reviews.json --head <head sha> --verifiers <logins> \
        --machine-account <login> --author <PR author> --branch <head branch>

The verdict is a pull request review from an allowed verifier account, given on
the current head commit: "Approve" is PASS, "Request changes" is FAIL. Reviews,
unlike comments, can't be edited into a different result by another account,
and each records the commit it was given on, so any new push voids an earlier
PASS. A FAIL on this head is final until a new push. Dismissed reviews, reviews
from anyone else, and reviews by the PR's own author don't count.

It also refuses:
- a verifier list that includes the machine account, because then the builder
  could verify its own work;
- plan PRs (`plan/<slug>`), which only the Owner merges.

When to remove: when agents no longer merge on their own, and a person reads
every verdict before merging.

Exit 0 when this head has a PASS and no FAIL from a verifier, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def logins(text: str) -> set[str]:
    return {v.strip().lower() for v in text.split(",") if v.strip()}


def fail(message: str, fix: str) -> int:
    print(f"FAIL agent-merge: {message}")
    print(f"To fix: {fix}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check for a PASS review on the current head.")
    parser.add_argument("--reviews", required=True, type=Path, help="JSON from the pull request reviews API")
    parser.add_argument("--head", required=True, help="the pull request's head commit")
    parser.add_argument("--verifiers", required=True, help="logins allowed to give verdicts, comma separated")
    parser.add_argument("--machine-account", default="", help="the builders' login (MACHINE_ACCOUNT)")
    parser.add_argument("--author", default="", help="the pull request's author")
    parser.add_argument("--branch", default="", help="the pull request's head branch")
    args = parser.parse_args(argv)

    verifiers = logins(args.verifiers)
    if not verifiers:
        return fail("no verifier accounts were given.",
                    "set the repository variable VERIFIER_ACCOUNTS to the verifier's GitHub login, "
                    "an account the builder can't act as.")
    if verifiers & logins(args.machine_account):
        return fail("VERIFIER_ACCOUNTS includes the MACHINE_ACCOUNT, so the builder could verify its own work.",
                    "give the verifier its own account and list only that one in VERIFIER_ACCOUNTS.")
    if args.branch.startswith("plan/"):
        return fail("this is a plan PR; plans need the Owner's approval, not a verdict.",
                    "ask the Owner to review and merge it.")

    author = args.author.strip().lower()
    on_head = [
        r for r in json.loads(args.reviews.read_text())
        if ((r.get("user") or {}).get("login") or "").lower() in verifiers - {author}
        and (r.get("commit_id") or "").lower() == args.head.lower()
        and r.get("state") in ("APPROVED", "CHANGES_REQUESTED")
    ]
    if any(r["state"] == "CHANGES_REQUESTED" for r in on_head):
        return fail(f"a verifier requested changes on head {args.head[:7]}.",
                    "fix what the verdict reports and push; the new head needs a new /verify.")
    if not on_head:
        return fail(f"no PASS verdict for head {args.head[:7]}.",
                    "run /verify on the current head (a new push voids earlier verdicts); the verifier "
                    "posts its verdict as an approving review from its own account.")
    print(f"PASS agent-merge: a verifier approved head {args.head[:7]}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
