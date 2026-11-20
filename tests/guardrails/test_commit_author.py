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


# --- commits the default branch already holds aren't the PR's (review finding N02, D61) ---

import pytest  # noqa: E402

from helpers import Repo  # noqa: E402


@pytest.fixture
def sync_commits(tmp_path):
    """A sync PR's commits: one the Owner merged into main, and the machine account's merge of main."""
    (tmp_path / "repo").mkdir()
    repo = Repo(tmp_path / "repo")
    repo.write("a.txt", "a\n")
    repo.commit("start")
    repo.git("checkout", "-q", "-b", "milestone/M1")
    repo.git("checkout", "-q", "main")
    repo.write("plan.md", "plan\n")
    on_main = repo.commit("the Owner merged a plan PR")
    repo.git("checkout", "-q", "-b", "sync/M1-main", "milestone/M1")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "main")
    return repo, on_main, repo.git("rev-parse", "HEAD")


def check_shas(tmp_path, repo, authors: dict[str, str], *extra: str):
    data = [{"sha": sha, "author": {"login": login}, "commit": {"author": {"name": login}}}
            for sha, login in authors.items()]
    path = tmp_path / "commits.json"
    path.write_text(json.dumps(data))
    return run_check("commit-author", "check_commit_author.py", "--expected", "example-bot",
                     "--commits", str(path), *extra)


def test_a_commit_already_on_the_default_branch_is_not_checked(tmp_path, sync_commits):
    repo, on_main, merge = sync_commits
    authors = {on_main: "example-owner", merge: "example-bot"}
    assert check_shas(tmp_path, repo, authors).returncode == 1  # without the repository: as before
    proc = check_shas(tmp_path, repo, authors, "--git-dir", str(repo.path), "--default", "main")
    assert proc.returncode == 0, proc.stdout


def test_another_authors_commit_off_the_default_branch_still_fails(tmp_path, sync_commits):
    repo, on_main, merge = sync_commits
    repo.write("b.txt", "b\n")
    other = repo.commit("not on main")
    authors = {on_main: "example-owner", merge: "example-bot", other: "example-owner"}
    proc = check_shas(tmp_path, repo, authors, "--git-dir", str(repo.path), "--default", "main")
    assert proc.returncode == 1 and other[:7] in proc.stdout
