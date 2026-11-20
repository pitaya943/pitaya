"""Recipe "agent-merge": a PASS verdict for the PR's current head, from an allowed verifier (D42, D44).

With one machine account (D44) the verifier posts as that account, so the verdict
is a comment (an author can't approve its own PR). A review from a verifier
account counts too. Edited comments don't count, any FAIL on the head is final,
and plan PRs never pass on a verdict.
"""

import json

from helpers import run_check

HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
OLD = "ffffffffffffffffffffffffffffffffffffffff"


def comment(result, sha=HEAD, login="example-bot", short=False, edited=False):
    shown = sha[:7] if short else sha
    created = "2026-11-20T10:00:00Z"
    return {"user": {"login": login}, "created_at": created,
            "updated_at": "2026-11-20T11:00:00Z" if edited else created,
            "body": f"## Verification: {result}\n\n- Model: m\n- Round: 1\n- Head commit: {shown}\n"}


def review(state, sha=HEAD, login="example-verifier"):
    return {"user": {"login": login}, "state": state, "commit_id": sha, "body": ""}


def check(tmp_path, comments=(), reviews=(), verifiers="example-bot", head=HEAD, branch="ticket/T-1-x"):
    c, r = tmp_path / "comments.json", tmp_path / "reviews.json"
    c.write_text(json.dumps(list(comments)))
    r.write_text(json.dumps(list(reviews)))
    return run_check("agent-merge", "check_verdict.py", "--comments", str(c), "--reviews", str(r),
                     "--head", head, "--verifiers", verifiers, "--branch", branch)


def test_pass_comment_for_this_head_passes(tmp_path):
    proc = check(tmp_path, [comment("PASS")])
    assert proc.returncode == 0, proc.stdout


def test_short_sha_matches(tmp_path):
    assert check(tmp_path, [comment("PASS", short=True)]).returncode == 0


def test_no_verdict_fails(tmp_path):
    proc = check(tmp_path, [{"user": {"login": "example-owner"}, "body": "looks good"}])
    assert proc.returncode == 1 and "To fix:" in proc.stdout


def test_pass_for_an_older_head_is_stale(tmp_path):
    proc = check(tmp_path, [comment("PASS", sha=OLD)])
    assert proc.returncode == 1 and "head" in proc.stdout.lower()


def test_any_fail_on_this_head_is_final(tmp_path):
    assert check(tmp_path, [comment("FAIL"), comment("PASS")]).returncode == 1
    assert check(tmp_path, [comment("PASS"), comment("FAIL")]).returncode == 1


def test_edited_comments_do_not_count(tmp_path):
    assert check(tmp_path, [comment("PASS", edited=True)]).returncode == 1


def test_verdict_from_someone_else_is_ignored(tmp_path):
    assert check(tmp_path, [comment("PASS", login="someone-else")]).returncode == 1


def test_an_approving_review_from_a_verifier_counts(tmp_path):
    assert check(tmp_path, reviews=[review("APPROVED")], verifiers="example-verifier").returncode == 0
    assert check(tmp_path, reviews=[review("APPROVED", sha=OLD)], verifiers="example-verifier").returncode == 1
    assert check(tmp_path, reviews=[review("CHANGES_REQUESTED"), review("APPROVED")],
                 verifiers="example-verifier").returncode == 1


def test_empty_verifier_list_fails(tmp_path):
    proc = check(tmp_path, [comment("PASS")], verifiers="")
    assert proc.returncode == 1 and "To fix:" in proc.stdout


def test_plan_and_milestone_prs_never_pass_on_a_verdict(tmp_path):
    for branch in ("plan/roadmap", "milestone/M2"):
        proc = check(tmp_path, [comment("PASS")], branch=branch)
        assert proc.returncode == 1 and "Owner" in proc.stdout, branch
