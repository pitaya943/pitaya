"""Recipe "agent-merge": a PASS verdict exists for the PR's current head, from an allowed verifier."""

import json

from helpers import run_check

HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
OLD = "ffffffffffffffffffffffffffffffffffffffff"


def verdict(result, sha, login="example-verifier", short=False):
    shown = sha[:7] if short else sha
    body = f"## Verification: {result}\n\n- Model: m\n- Round: 1\n- Head commit: {shown}\n"
    return {"user": {"login": login}, "body": body}


def check(tmp_path, comments, verifiers="example-verifier", head=HEAD):
    path = tmp_path / "comments.json"
    path.write_text(json.dumps(comments))
    return run_check("agent-merge", "check_verdict.py", "--comments", str(path), "--head", head,
                     "--verifiers", verifiers)


def test_pass_for_this_head_passes(tmp_path):
    proc = check(tmp_path, [verdict("PASS", HEAD)])
    assert proc.returncode == 0, proc.stdout


def test_short_sha_matches(tmp_path):
    assert check(tmp_path, [verdict("PASS", HEAD, short=True)]).returncode == 0


def test_no_verdict_fails(tmp_path):
    proc = check(tmp_path, [{"user": {"login": "example-owner"}, "body": "looks good"}])
    assert proc.returncode == 1 and "To fix:" in proc.stdout


def test_pass_for_an_older_head_is_stale(tmp_path):
    proc = check(tmp_path, [verdict("PASS", OLD)])
    assert proc.returncode == 1 and "head" in proc.stdout.lower()


def test_latest_verdict_for_this_head_wins(tmp_path):
    assert check(tmp_path, [verdict("PASS", HEAD), verdict("FAIL", HEAD)]).returncode == 1
    assert check(tmp_path, [verdict("FAIL", HEAD), verdict("PASS", HEAD)]).returncode == 0


def test_verdict_from_someone_else_is_ignored(tmp_path):
    # e.g. the builder's account posting a PASS for its own work
    proc = check(tmp_path, [verdict("PASS", HEAD, login="example-bot")])
    assert proc.returncode == 1


def test_empty_verifier_list_fails(tmp_path):
    proc = check(tmp_path, [verdict("PASS", HEAD)], verifiers="")
    assert proc.returncode == 1 and "To fix:" in proc.stdout
