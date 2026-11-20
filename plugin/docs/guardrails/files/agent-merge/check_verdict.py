#!/usr/bin/env python3
# pitaya template 0.1.5 · docs/guardrails/files/agent-merge/check_verdict.py
"""Guardrail "agent-merge": a PASS verdict exists for the pull request's current head commit.

Usage (in CI)::

    gh api "repos/$REPO/issues/$PR/comments" --paginate > comments.json
    gh api "repos/$REPO/pulls/$PR/reviews" --paginate > reviews.json
    python3 check_verdict.py --comments comments.json --reviews reviews.json \
        --head <head sha> --verifiers <logins> --branch <head branch> \
        [--git-dir . --base origin/<base branch> --default origin/<default branch>]

A verdict comes from an allowed verifier account, for the current head commit:

- a comment that starts with "## Verification: PASS" or "## Verification: FAIL"
  and names a "Head commit:" (the `/verify` template). With one machine account
  the verifier posts as that account, and GitHub doesn't let an author approve
  its own pull request, so this is the usual form. Edited comments don't count.
- a pull request review from a verifier account on that commit: "Approve" is
  PASS, "Request changes" is FAIL. Dismissed reviews don't count.

Any new push voids earlier verdicts, with one exception that needs `--git-dir`:
a PASS carries over to a head that adds only a merge of the base branch (GitHub's
"Update branch"). The check proves it twice. The head's tree must equal the tree
git gets by merging the current base into the PASS head, and every commit added
since must be a true merge: two parents, and the tree git gets by merging them.
Anything else on top needs a new verdict: a change folded into the merge commit
gives another tree, and `git merge -s ours` keeps the tree but records a commit as
merged whose changes never arrived, so a later merge of that commit is dropped. A FAIL on this head, or on the PASS head being carried, is final.

A sync PR (`sync/<slug>` into `milestone/<id>`, with `--git-dir`) needs no
verdict when its tree equals the base merged with the newest default-branch
commit it contains, and every commit it adds is a true merge: everything in it
was already merged into the default branch.

A FAIL on this head is final until the
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
import subprocess
import sys
from pathlib import Path

RESULT_RE = re.compile(r"^##\s*Verification:\s*(PASS|FAIL)\b", re.M)
HEAD_RE = re.compile(r"Head commit:\s*`?([0-9a-f]{7,40})", re.I)
MILESTONE_RE = re.compile(r"(^|/)milestone/[^/]+$")


def fail(message: str, fix: str) -> int:
    print(f"FAIL agent-merge: {message}")
    print(f"To fix: {fix}")
    return 1


def load(path: Path | None) -> list[dict]:
    return json.loads(path.read_text()) if path and path.exists() else []


def git(repo: Path, *args: str) -> str | None:
    """Run git in `repo`; None when it fails (an unknown commit, a conflict)."""
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def merged_tree(repo: Path, base: str, other: str) -> str | None:
    """The tree git gets by merging `other` into `base`; None on a conflict."""
    out = git(repo, "merge-tree", "--write-tree", base, other)
    return out.splitlines()[0] if out else None


def true_merges(repo: Path, head: str, *known: str) -> bool:
    """True when every commit `head` adds to the `known` commits is a true merge.

    A true merge has two parents and the tree git gets by merging them. A commit with one
    parent is a change; `git merge -s ours` and a merge with an edit folded in have a tree
    that isn't the merge of their parents. Either would put history on the branch that the
    tree comparison can't see: a commit recorded as merged whose changes never arrived.
    """
    listed = git(repo, "rev-list", "--parents", head, *(f"^{k}" for k in known))
    if listed is None:
        return False
    for line in listed.splitlines():
        commit, *parents = line.split()
        if len(parents) != 2:
            return False
        if merged_tree(repo, *parents) != git(repo, "rev-parse", f"{commit}^{{tree}}"):
            return False
    return True


def only_merges(repo: Path, head: str, base: str, other: str) -> bool:
    """True when `head` holds exactly `other` merged with the base, and nothing else.

    Two proofs, both needed: the head's tree is the base merged with `other`, and every
    commit the head adds to them is a true merge (see `true_merges`).
    """
    want = merged_tree(repo, base, other)
    return (want is not None and want == git(repo, "rev-parse", f"{head}^{{tree}}")
            and true_merges(repo, head, base, other))


def verdicts(comments: list[dict], reviews: list[dict], verifiers: set[str]) -> list[tuple[str, str]]:
    """(named commit, PASS or FAIL) for each verdict that counts: an allowed author, not edited."""
    out = []
    for c in comments:
        login = ((c.get("user") or {}).get("login") or "").lower()
        body = c.get("body") or ""
        result, named = RESULT_RE.search(body), HEAD_RE.search(body)
        edited = c.get("updated_at") and c.get("updated_at") != c.get("created_at")
        if login in verifiers and result and named and not edited:
            out.append((named.group(1).lower(), result.group(1)))
    for r in reviews:
        login = ((r.get("user") or {}).get("login") or "").lower()
        result = {"APPROVED": "PASS", "CHANGES_REQUESTED": "FAIL"}.get(r.get("state"), "")
        if login in verifiers and result:
            out.append(((r.get("commit_id") or "").lower(), result))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check for a PASS verdict on the current head.")
    parser.add_argument("--comments", type=Path, help="JSON from the issue comments API")
    parser.add_argument("--reviews", type=Path, help="JSON from the pull request reviews API")
    parser.add_argument("--head", required=True, help="the pull request's head commit")
    parser.add_argument("--verifiers", required=True, help="logins allowed to give verdicts, comma separated")
    parser.add_argument("--branch", default="", help="the pull request's head branch")
    parser.add_argument("--git-dir", type=Path, help="a clone with the head, base and default commits")
    parser.add_argument("--base", default="", help="the base branch as a commit or ref, with --git-dir")
    parser.add_argument("--default", default="", help="the default branch as a commit or ref, with --git-dir")
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
    repo = args.git_dir
    found = verdicts(load(args.comments), load(args.reviews), verifiers)

    def matches(named: str, commit: str) -> bool:
        return bool(named) and commit.startswith(named)

    on_head = [result for named, result in found if matches(named, head)]
    if "FAIL" in on_head:
        return fail(f"a verifier reported FAIL on head {args.head[:7]}.",
                    "fix what the verdict reports and push; the new head needs a new /verify.")
    if "PASS" in on_head:
        print(f"PASS agent-merge: a verifier passed head {args.head[:7]}.")
        return 0

    if repo and args.base:
        # A sync PR brings commits already merged into the default branch; it needs no verdict.
        if args.branch.startswith("sync/") and MILESTONE_RE.search(args.base) and args.default:
            newest = git(repo, "merge-base", head, args.default)
            if newest and only_merges(repo, head, args.base, newest):
                print(f"PASS agent-merge: sync PR; head {args.head[:7]} only merges {args.default} "
                      f"({newest[:7]}) into {args.base}.")
                return 0
            return fail(f"sync PR head {args.head[:7]} has changes or commits besides merging {args.default}.",
                        "recreate the sync branch from the milestone branch and merge only the default "
                        "branch into it, with a plain `git merge` (no strategy option, no edits); "
                        "move other changes to a ticket.")
        # A PASS carries over a merge of the base ("Update branch"), and nothing else.
        for named, result in found:
            if result != "PASS":
                continue
            passed = git(repo, "rev-parse", "--verify", "--quiet", f"{named}^{{commit}}")
            if not passed or passed == head:
                continue
            if any(r == "FAIL" and matches(n, passed) for n, r in found):
                continue
            ancestor = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", passed, head])
            if ancestor.returncode == 0 and only_merges(repo, head, args.base, passed):
                print(f"PASS agent-merge: head {args.head[:7]} is the PASS head {passed[:7]} with only the "
                      f"base merged in since.")
                return 0

    return fail(f"no PASS verdict for head {args.head[:7]}.",
                "run /verify on the current head (a new push voids earlier verdicts, except a merge of "
                "the base alone) and fix what it reports.")


if __name__ == "__main__":
    sys.exit(main())
