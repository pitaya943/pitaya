#!/usr/bin/env python3
# pitaya template 0.1.8 · docs/guardrails/files/commit-author/check_commit_author.py
"""Guardrail "commit-author": every commit in a PR is authored by the machine account.

Usage (in CI)::

    gh api "repos/$REPO/pulls/$PR/commits" --paginate > commits.json
    python3 check_commit_author.py --expected <machine account login> --commits commits.json \
        [--git-dir . --default origin/<default branch>]

It compares GitHub's own `author.login` for each commit, not the email in the
commit, so a commit made under the wrong identity can't pass by copying an
address. A commit whose email GitHub can't link to any account fails too.
`--also-allow` adds logins that may appear, such as the Owner's account for
"Update branch" merge commits made on github.com.

With `--git-dir` and `--default`, a commit the default branch already contains
isn't checked: it was merged there under that branch's own rules, and a sync PR
(`sync/<slug>` into `milestone/<id>`) brings such commits in, whoever wrote them.

When to remove: when only one agent works in the repository, or when signed
commits from the machine account are enforced by the ruleset instead.

Exit 0 when every commit is by an allowed login, 1 otherwise. Standard library and git only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def on_default(repo: Path, sha: str, default: str) -> bool:
    """True when the default branch already contains this commit."""
    if not sha:
        return False
    proc = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, default], capture_output=True)
    return proc.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that every PR commit is by the machine account.")
    parser.add_argument("--expected", required=True, help="the machine account's GitHub login")
    parser.add_argument("--commits", required=True, type=Path, help="JSON from the pull request commits API")
    parser.add_argument("--also-allow", default="", help="other allowed logins, comma separated")
    parser.add_argument("--git-dir", type=Path, help="a clone holding the PR's commits and the default branch")
    parser.add_argument("--default", default="", help="the default branch as a commit or ref, with --git-dir")
    args = parser.parse_args(argv)

    if not args.expected.strip():
        print("FAIL commit-author: no machine account login was given.")
        print("To fix: set the repository variable MACHINE_ACCOUNT to the machine account's GitHub login.")
        return 1
    allowed = {args.expected.strip().lower()} | {a.strip().lower() for a in args.also_allow.split(",") if a.strip()}
    problems = []
    for commit in json.loads(args.commits.read_text()):
        if args.git_dir and args.default and on_default(args.git_dir, commit.get("sha", ""), args.default):
            continue  # already merged into the default branch: not this PR's work
        sha = commit.get("sha", "")[:7]
        author = commit.get("author") or {}
        login = author.get("login")
        if not login:
            name = (commit.get("commit") or {}).get("author", {}).get("name", "?")
            problems.append(f"{sha}: the author ({name}) isn't linked to a GitHub account")
        elif login.lower() not in allowed:
            problems.append(f"{sha}: authored by {login}")
    if problems:
        print(f"FAIL commit-author: commits not authored by {args.expected}:")
        for line in problems:
            print(f"  {line}")
        print(f"To fix: set the commit author to {args.expected} with its GitHub noreply email, "
              "then recreate these commits on a new branch (don't rewrite a shared branch) and open a new PR.")
        return 1
    print(f"PASS commit-author: every commit is by an allowed account.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
