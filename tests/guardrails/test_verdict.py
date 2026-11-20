"""Recipe "agent-merge": a PASS review exists for the PR's current head, from an allowed verifier (D42).

The verdict is a PR review, not a comment: other accounts with write access can
edit or delete comments, but not change another account's review. A review
records the commit it was given on, and it can only be dismissed, not flipped.
"""

import json

from helpers import run_check

HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
OLD = "ffffffffffffffffffffffffffffffffffffffff"


def review(state, sha=HEAD, login="example-verifier", at="2026-11-20T10:00:00Z"):
    return {"user": {"login": login}, "state": state, "commit_id": sha, "submitted_at": at,
            "body": f"## Verification: {'PASS' if state == 'APPROVED' else 'FAIL'}\n"}


def check(tmp_path, reviews, verifiers="example-verifier", head=HEAD, machine="example-bot",
          author="example-bot", branch="ticket/T-1-x"):
    path = tmp_path / "reviews.json"
    path.write_text(json.dumps(reviews))
    return run_check("agent-merge", "check_verdict.py", "--reviews", str(path), "--head", head,
                     "--verifiers", verifiers, "--machine-account", machine,
                     "--author", author, "--branch", branch)


def test_approval_on_this_head_passes(tmp_path):
    proc = check(tmp_path, [review("APPROVED")])
    assert proc.returncode == 0, proc.stdout


def test_no_verdict_fails(tmp_path):
    proc = check(tmp_path, [review("COMMENTED")])
    assert proc.returncode == 1 and "To fix:" in proc.stdout


def test_approval_on_an_older_head_is_stale(tmp_path):
    proc = check(tmp_path, [review("APPROVED", sha=OLD)])
    assert proc.returncode == 1 and "head" in proc.stdout.lower()


def test_any_fail_on_this_head_is_final(tmp_path):
    reviews = [review("CHANGES_REQUESTED", at="2026-11-20T10:00:00Z"),
               review("APPROVED", at="2026-11-20T11:00:00Z")]
    assert check(tmp_path, reviews).returncode == 1


def test_dismissed_reviews_are_ignored(tmp_path):
    assert check(tmp_path, [review("DISMISSED")]).returncode == 1
    assert check(tmp_path, [review("DISMISSED", sha=HEAD), review("APPROVED")]).returncode == 0


def test_verdict_from_someone_else_is_ignored(tmp_path):
    assert check(tmp_path, [review("APPROVED", login="example-bot")]).returncode == 1


def test_the_pr_author_cannot_verify_its_own_pr(tmp_path):
    proc = check(tmp_path, [review("APPROVED")], author="example-verifier")
    assert proc.returncode == 1


def test_verifier_must_not_be_the_machine_account(tmp_path):
    proc = check(tmp_path, [review("APPROVED", login="example-bot")], verifiers="example-bot")
    assert proc.returncode == 1 and "MACHINE_ACCOUNT" in proc.stdout and "To fix:" in proc.stdout


def test_empty_verifier_list_fails(tmp_path):
    proc = check(tmp_path, [review("APPROVED")], verifiers="")
    assert proc.returncode == 1 and "To fix:" in proc.stdout


def test_plan_prs_never_pass_on_a_verdict(tmp_path):
    proc = check(tmp_path, [review("APPROVED")], branch="plan/roadmap")
    assert proc.returncode == 1 and "Owner" in proc.stdout
