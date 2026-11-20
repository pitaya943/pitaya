#!/usr/bin/env python3
# pitaya template 0.1.7 · docs/guardrails/files/agent-merge/check_verdict.py
"""Guardrail "agent-merge": a PASS verdict exists for the pull request's current head commit.

Usage (in CI)::

    gh api "repos/$REPO/issues/$PR/comments" --paginate > comments.json
    gh api "repos/$REPO/pulls/$PR/reviews" --paginate > reviews.json
    python3 check_verdict.py --comments comments.json --reviews reviews.json \
        --head <head sha> --verifiers <logins> --branch <head branch> \
        [--git-dir . --base origin/<base branch> --default origin/<default branch>] \
        [--failed <sha,sha>] [--record <file>] [--ticket <issue body file>]

A verdict comes from an allowed verifier account, for the current head commit:

- a comment that **starts** with "## Verification: PASS" or "## Verification: FAIL"
  and has a "Head commit:" line with the full 40-character commit (the `/verify`
  template). A comment that quotes a verdict further down isn't one, and neither
  is a 7-character prefix. With one machine account the verifier posts as that
  account, and GitHub doesn't let an author approve its own pull request, so this
  is the usual form.
- a pull request review from a verifier account on that commit: "Approve" is
  PASS, "Request changes" is FAIL. Dismissed reviews don't count.

A PASS comment also needs a "Session:" line with a real ID ("unavailable" or an
unfilled placeholder doesn't count), and that session must not be one a
"Builder session:" line on the pull request names (the builder's hand-off and
fix-round comments carry it): the session that built the work, or a subagent of
it, can't pass it. This catches an honest mistake. It doesn't stop a session
that writes a false ID: pitaya trusts cooperating agents (see the recipe).

A FAIL is one-way. An edited PASS doesn't count, but an edited FAIL still does,
and `--failed` lists the commits whose FAIL the workflow recorded in a
`verdict-fail` commit status when it first saw it, so a FAIL whose comment was
edited or deleted afterwards still counts. `--record` writes the commits this run
saw a FAIL for, for the workflow to record. A FAIL on a commit is final for that
commit: fix, push, and get a PASS on the new head.

Any new push voids earlier verdicts, with one exception that needs `--git-dir`:
a PASS carries over to a head that adds only a merge of the base branch (GitHub's
"Update branch"). The check proves it twice. The head's tree must equal the tree
git gets by merging the current base into the PASS head, and every commit added
since must be a true merge: two parents, and the tree git gets by merging them.
Anything else on top needs a new verdict: a change folded into the merge commit
gives another tree, and `git merge -s ours` keeps the tree but records a commit as
merged whose changes never arrived, so a later merge of that commit is dropped. A
FAIL on the PASS head being carried stops the carry. So does `Risk: high` in the
ticket (its file on the base branch, or `--ticket` for an issue's body): nobody
verified the combined result, and a high-risk ticket is where that matters.

A sync PR (`sync/<slug>` into `milestone/<id>`, with `--git-dir`) needs no
verdict when its tree equals the base merged with the newest default-branch
commit it contains, and every commit it adds is a true merge: everything in it
was already merged into the default branch.

Milestone PRs (`milestone/<id>`) never pass, and neither does a plan PR
(`plan/<slug>`) into the default branch: the Owner merges those, and no verdict
changes that. A plan PR into a milestone branch has no verifier to wait for, so
it passes without a verdict in two cases, and only with `--git-dir`:

- the report PR, which closes `milestone/<id>` from inside, from any `plan/` branch:
  it changes nothing but `docs/reports/<id>.md` and the `Status:` line of
  `docs/milestones/<id>.md`, which may only become `done`, and no ticket file
  of that milestone is still open. The report alone is enough (a new report
  after the Owner sent the milestone back). The Owner reads both in the
  milestone PR, whose merge is the sign-off.
- a cut, where the Owner lets agents merge it: the "Autonomy" line of
  `docs/agents/harness.md` on the default branch starts with "Agents merge"
  and names plan PRs (Level 4). It changes only plan files and deletes nothing,
  it adds tickets without changing one that exists, and it changes no milestone
  file but its own.

Anything else in such a PR waits for the Owner. A FAIL on its head blocks it like
any other.

When to remove: when agents no longer merge on their own, and a person reads
every verdict before merging.

Exit 0 when this head has no FAIL and either a PASS from a verifier or one of the
proofs above (a carried PASS, a sync PR, a report PR, a cut); 1 otherwise.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# A verdict comment starts with the heading (blank lines before it are fine) and names the full commit.
RESULT_RE = re.compile(r"\A\s*##[ \t]*Verification:[ \t]*(PASS|FAIL)\b")
HEAD_RE = re.compile(r"^[ \t]*[-*]?[ \t]*Head commit:[ \t]*`?([0-9a-f]{40})\b", re.I | re.M)
SESSION_RE = re.compile(r"^[ \t]*[-*]?[ \t]*Session:[ \t]*`?([^\s`]*)", re.I | re.M)
BUILDER_RE = re.compile(r"^[ \t]*[-*]?[ \t]*Builder session:[ \t]*`?([^\s`]+)", re.I | re.M)
RISK_HIGH_RE = re.compile(r"^Risk:[ \t]*high\b", re.I | re.M)
MILESTONE_RE = re.compile(r"(^|/)milestone/([^/]+)$")
STATUS_RE = re.compile(r"^Status:[ \t]*(\S+)[ \t]*$", re.I)
DONE_RE = re.compile(r"^Status:[ \t]*done\b", re.I | re.M)
AUTONOMY_RE = re.compile(r"^[ \t]*-[ \t]*Autonomy:[ \t]*(.*)$", re.M)
# The files a plan PR may change: the same list as the ticket checks' shared step.
PLAN_FILES_RE = re.compile(r"^(docs/(tickets|milestones|adr|reports)/[^/]+\.md|docs/agents/(glossary|architecture)\.md"
                           r"|docs/decisions\.md)$")
HARNESS = "docs/agents/harness.md"


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


def real_session(value: str) -> bool:
    """False for an empty value, "unavailable" or a placeholder nobody filled in."""
    return bool(value) and not value.lower().startswith("unavailable") and not set(value) & set("<>${}")


def builder_sessions(comments: list[dict], agents: set[str]) -> set[str]:
    """Session IDs the builders recorded on the pull request ("Builder session: <id>").

    Only comments from the verifier accounts count. With one machine account that is the
    builders' account too; with a separate verifier account the guard isn't needed, because
    a builder can't post as the verifier. Text from anyone else is information, so an
    outsider can't void a verdict by naming the verifier's session as a builder's.
    """
    out = set()
    for c in comments:
        if ((c.get("user") or {}).get("login") or "").lower() in agents:
            out.update(BUILDER_RE.findall(c.get("body") or ""))
    return out


def verdicts(comments: list[dict], reviews: list[dict], verifiers: set[str]) -> tuple[list[tuple[str, str]], list[str]]:
    """((named commit, PASS or FAIL) for each verdict that counts, why each other PASS didn't).

    A PASS counts when it comes from an allowed author, wasn't edited, and names a session that
    isn't a builder's. A FAIL counts from an allowed author whatever else is true of it.
    """
    out, notes = [], []
    builders = builder_sessions(comments, verifiers)
    for c in comments:
        login = ((c.get("user") or {}).get("login") or "").lower()
        body = c.get("body") or ""
        result = RESULT_RE.search(body)
        if login not in verifiers or not result:
            continue
        named = HEAD_RE.search(body)
        if not named:
            notes.append(f"a {result.group(1)} verdict has no \"Head commit:\" line with the full 40-character commit.")
            continue
        commit = named.group(1).lower()
        if result.group(1) == "FAIL":
            out.append((commit, "FAIL"))
            continue
        session = SESSION_RE.search(body)
        session = session.group(1) if session else ""
        if c.get("updated_at") and c.get("updated_at") != c.get("created_at"):
            notes.append(f"the PASS for {commit[:7]} was edited after it was posted; an edited PASS doesn't count.")
        elif not real_session(session):
            notes.append(f"the PASS for {commit[:7]} has no \"Session:\" line naming the verifier's session.")
        elif session in builders:
            notes.append(f"the PASS for {commit[:7]} comes from session {session}, which a \"Builder session:\" "
                         "line on this pull request names: a builder can't verify its own work.")
        else:
            out.append((commit, "PASS"))
    for r in reviews:
        login = ((r.get("user") or {}).get("login") or "").lower()
        result = {"APPROVED": "PASS", "CHANGES_REQUESTED": "FAIL"}.get(r.get("state"), "")
        if login in verifiers and result:
            out.append(((r.get("commit_id") or "").lower(), result))
    return out, notes


def high_risk(repo: Path | None, base: str, branch: str, ticket: Path | None) -> bool:
    """True when the branch's ticket says "Risk: high": `ticket` if given, else its file on the base branch."""
    if ticket and ticket.exists():
        return bool(RISK_HIGH_RE.search(ticket.read_text()))
    if not (repo and base and branch.startswith("ticket/")):
        return False
    for path in (git(repo, "ls-tree", "--name-only", base, "docs/tickets/") or "").splitlines():
        name = Path(path).stem
        if path.endswith(".md") and (branch == f"ticket/{name}" or branch.startswith(f"ticket/{name}-")):
            return bool(RISK_HIGH_RE.search(git(repo, "show", f"{base}:{path}") or ""))
    return False


def agents_merge_plans(harness: str) -> bool:
    """True when the harness file's Autonomy value lets agents merge plan PRs (Level 4).

    Only the field's own value counts, up to its first semicolon: the note under it quotes
    the alternatives, and the part after the semicolon says who merges the default branch.
    """
    match = AUTONOMY_RE.search(harness)
    value = match.group(1).split(";")[0].strip().lower() if match else ""
    return value.startswith("agents merge") and bool(re.search(r"\bplan\b", value))


def changed(repo: Path, base: str, head: str) -> list[tuple[str, str]] | None:
    """(status letter, path) for each file the pull request changes, as GitHub shows it; None when git fails."""
    out = git(repo, "diff", "--name-status", "--no-renames", f"{base}...{head}")
    return None if out is None else [tuple(line.split("\t", 1)) for line in out.splitlines()]


def plan_into_milestone(repo: Path, head: str, base: str, default: str) -> tuple[str, str]:
    """(why a plan PR into a milestone branch needs no verdict, why it does); one of them is empty."""
    milestone = MILESTONE_RE.search(base).group(2)
    files = changed(repo, base, head)
    start = git(repo, "merge-base", base, head)
    if files is None or not start:
        return "", "the check couldn't read what it changes"
    if not files:
        return "", "it changes nothing"
    deleted = [path for status, path in files if status == "D"]
    if deleted:
        return "", "it deletes " + ", ".join(deleted) + ": plan files are records, and removing one is the Owner's"
    paths = [path for _, path in files]
    milestone_file, report = f"docs/milestones/{milestone}.md", f"docs/reports/{milestone}.md"

    if set(paths) <= {milestone_file, report}:
        # The report PR: Status: done and the report, for this branch's own milestone.
        if milestone_file in paths:
            before = (git(repo, "show", f"{start}:{milestone_file}") or "").splitlines()
            after = (git(repo, "show", f"{head}:{milestone_file}") or "").splitlines()
            differing = [(a, b) for a, b in zip(before, after) if a != b]
            if len(before) != len(after) or not before or not all(
                    STATUS_RE.match(a) and DONE_RE.match(b) for a, b in differing):
                return "", (f"it changes more of {milestone_file} than its Status line to \"Status: done\": the goal, "
                            "the exit criteria and the ticket list are the Owner's")
        for path in (git(repo, "ls-tree", "--name-only", head, "docs/tickets/") or "").splitlines():
            text = git(repo, "show", f"{head}:{path}") or ""
            if path.endswith(".md") and re.search(rf"^Milestone:[ \t]*{re.escape(milestone)}[ \t]*$", text, re.I | re.M) \
                    and not DONE_RE.search(text):
                return "", f"ticket {Path(path).stem} of {milestone} isn't done, so the milestone isn't either"
        return f"report PR; it only sets {milestone} to done and writes its report", ""

    other = [path for path in paths if not PLAN_FILES_RE.match(path)]
    if other:
        return "", "it changes files that aren't plan files: " + ", ".join(other)
    harness = (git(repo, "show", f"{default}:{HARNESS}") or "") if default else ""
    if not agents_merge_plans(harness):
        return "", (f"the Autonomy line in {HARNESS} on the default branch doesn't let agents merge plan PRs, "
                    "and it isn't a report PR (only the milestone's Status line and its report)")
    # A cut fills in its own milestone and adds tickets. A ticket that exists, and every other
    # milestone's file, stay as the Owner approved them.
    kept = [path for status, path in files if status != "A" and path != milestone_file
            and path.startswith(("docs/tickets/", "docs/milestones/"))]
    if kept:
        return "", ("a cut adds tickets and fills in its own milestone; this changes tickets or milestones "
                    "that exist: " + ", ".join(kept))
    return "cut; it only adds plan files, and the Owner's Autonomy setting lets agents merge it", ""


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
    parser.add_argument("--failed", default="", help="commits with a recorded FAIL (the verdict-fail status), "
                                                     "comma separated full SHAs")
    parser.add_argument("--record", type=Path, help="write the commits this run saw a FAIL verdict for, one per line")
    parser.add_argument("--ticket", type=Path, help="the ticket's text when it is an issue, for its Risk line")
    args = parser.parse_args(argv)

    verifiers = {v.strip().lower() for v in args.verifiers.split(",") if v.strip()}
    if not verifiers:
        return fail("no verifier accounts were given.",
                    "set the repository variable VERIFIER_ACCOUNTS, or MACHINE_ACCOUNT, to the login "
                    "the verifier posts as.")

    head = args.head.lower()
    repo = args.git_dir
    found, notes = verdicts(load(args.comments), load(args.reviews), verifiers)
    recorded = {s.strip().lower() for s in args.failed.split(",") if s.strip()}
    failed = recorded | {named for named, result in found if result == "FAIL"}
    if args.record:
        # Only commits this repository has can carry a status: the head, and with a clone anything it resolves.
        seen = sorted(c for c in failed - recorded
                      if c == head or (repo and git(repo, "rev-parse", "--verify", "--quiet", f"{c}^{{commit}}")))
        args.record.write_text("".join(f"{c}\n" for c in seen))

    if args.branch.startswith("milestone/"):
        return fail("this is a milestone PR; it needs the Owner's review, not a verdict.",
                    "ask the Owner to review and merge it.")

    if head in failed:
        how = "a verifier reported FAIL" if any(n == head and r == "FAIL" for n, r in found) \
            else "a FAIL was recorded (its comment was edited or deleted since)"
        return fail(f"{how} on head {args.head[:7]}.",
                    "fix what the verdict reports and push; the new head needs a new /verify.")

    if args.branch.startswith("plan/"):
        # No verifier judges a plan PR. Into a milestone branch it passes when it is the report PR
        # or a cut the Owner lets agents merge; everything else, and every plan PR into the default
        # branch, is the Owner's to merge.
        why = "it targets a branch only the Owner merges"
        if repo and MILESTONE_RE.search(args.base):
            reason, why = plan_into_milestone(repo, head, args.base, args.default)
            if reason:
                print(f"PASS agent-merge: {reason} (head {args.head[:7]}).")
                return 0
        return fail(f"this plan PR needs the Owner's review, not a verdict: {why}.",
                    "ask the Owner to review and merge it. A report PR changes only the milestone's Status line "
                    "and docs/reports/<milestone>.md; a cut changes only plan files and adds tickets.")
    if any(named == head and result == "PASS" for named, result in found):
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
            if not passed or passed == head or passed in failed:
                continue
            ancestor = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", passed, head])
            if ancestor.returncode == 0 and only_merges(repo, head, args.base, passed):
                if high_risk(repo, args.base, args.branch, args.ticket):
                    return fail(f"head {args.head[:7]} is the PASS head {passed[:7]} with only the base merged in, "
                                "but the ticket is Risk: high, and a high-risk ticket's PASS doesn't carry.",
                                "run /verify on the current head: nobody has checked this ticket against the "
                                "new base.")
                print(f"PASS agent-merge: head {args.head[:7]} is the PASS head {passed[:7]} with only the "
                      f"base merged in since.")
                return 0

    for note in notes:
        print(f"Note: {note}")
    return fail(f"no PASS verdict for head {args.head[:7]}.",
                "run /verify on the current head, in a session that didn't build it (a new push voids earlier "
                "verdicts, except a merge of the base alone). The verdict comment starts with the heading, and "
                "names the full 40-character head commit and the verifier's session.")


if __name__ == "__main__":
    sys.exit(main())
