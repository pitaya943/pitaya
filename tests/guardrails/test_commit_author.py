"""Recipe "commit-author": every commit in a PR is authored by the machine account (by GitHub login)."""

import json

from helpers import run_check


def commits(tmp_path, *authors):
    """authors: GitHub logins, or None for a commit GitHub couldn't link to an account."""
    data = [{"sha": f"{i:040x}", "author": None if a is None else {"login": a},
             "commit": {"author": {"name": "someone", "email": "x@example.com"}, "message": f"c{i}"}}
            for i, a in enumerate(authors, start=1)]
    path = tmp_path / "commits.json"
    path.write_text(json.dumps(data))
    return str(path)


def check(tmp_path, *authors, extra=()):
    return run_check("commit-author", "check_commit_author.py", "--expected", "example-bot",
                     "--commits", commits(tmp_path, *authors), *extra)


def test_all_commits_by_the_machine_account_pass(tmp_path):
    proc = check(tmp_path, "example-bot", "example-bot")
    assert proc.returncode == 0, proc.stdout


def test_another_author_fails(tmp_path):
    proc = check(tmp_path, "example-bot", "example-owner")
    assert proc.returncode == 1 and "example-owner" in proc.stdout and "To fix:" in proc.stdout


def test_unlinked_author_fails(tmp_path):
    proc = check(tmp_path, None)
    assert proc.returncode == 1 and "isn't linked" in proc.stdout


def test_also_allowed_logins_pass(tmp_path):
    # e.g. the Owner's "Update branch" merge commit made on github.com
    proc = check(tmp_path, "example-bot", "example-owner", extra=("--also-allow", "example-owner"))
    assert proc.returncode == 0, proc.stdout


def test_login_comparison_ignores_case(tmp_path):
    assert check(tmp_path, "Example-Bot").returncode == 0


def test_empty_expected_login_fails(tmp_path):
    proc = run_check("commit-author", "check_commit_author.py", "--expected", "",
                     "--commits", commits(tmp_path, "example-bot"))
    assert proc.returncode == 1 and "To fix:" in proc.stdout
