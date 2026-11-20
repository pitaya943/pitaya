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


# --- a PASS survives only a merge of the base (P20), and sync PRs (P14); D58 ---------

import pytest  # noqa: E402

from helpers import Repo  # noqa: E402


@pytest.fixture
def branches(tmp_path):
    """A ticket branch with a PASS head, then its milestone moves on and the base is merged in."""
    (tmp_path / "repo").mkdir()
    repo = Repo(tmp_path / "repo")
    repo.write("app.py", "x = 1\n")
    repo.commit("start")
    repo.git("checkout", "-q", "-b", "milestone/M1")
    repo.git("checkout", "-q", "-b", "ticket/T-1-a")
    repo.write("a.py", "a = 1\n")
    passed = repo.commit("ticket T-1")
    repo.git("checkout", "-q", "milestone/M1")
    repo.write("b.py", "b = 1\n")
    repo.commit("ticket T-2 merged into the milestone")
    repo.git("checkout", "-q", "ticket/T-1-a")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")  # "Update branch"
    head = repo.git("rev-parse", "HEAD")
    return repo, passed, head


def check_git(tmp_path, repo, comments, head, branch="ticket/T-1-a", base="milestone/M1", default="main"):
    c = tmp_path / "comments.json"
    c.write_text(json.dumps(list(comments)))
    return run_check("agent-merge", "check_verdict.py", "--comments", str(c), "--head", head,
                     "--verifiers", "example-bot", "--branch", branch,
                     "--git-dir", str(repo.path), "--base", base, "--default", default)


def test_a_pass_carries_over_a_merge_of_the_base(tmp_path, branches):
    repo, passed, head = branches
    proc = check_git(tmp_path, repo, [comment("PASS", sha=passed)], head)
    assert proc.returncode == 0, proc.stdout
    assert passed[:7] in proc.stdout and "base" in proc.stdout


def test_a_pass_does_not_carry_over_any_other_change(tmp_path, branches):
    repo, passed, _ = branches
    repo.write("a.py", "a = 2  # not what was verified\n")
    head = repo.commit("an unverified change after the merge")
    assert check_git(tmp_path, repo, [comment("PASS", sha=passed)], head).returncode == 1


def test_a_change_hidden_in_the_update_merge_does_not_carry(tmp_path, branches):
    repo, passed, _ = branches
    repo.write("a.py", "a = 'amended into the merge'\n")
    repo.git("add", "-A")
    repo.git("commit", "-q", "--amend", "--no-edit")
    head = repo.git("rev-parse", "HEAD")
    assert check_git(tmp_path, repo, [comment("PASS", sha=passed)], head).returncode == 1


def test_a_fail_on_the_passed_head_stops_the_carry(tmp_path, branches):
    repo, passed, head = branches
    verdicts = [comment("PASS", sha=passed), comment("FAIL", sha=passed)]
    assert check_git(tmp_path, repo, verdicts, head).returncode == 1


def test_a_fail_on_the_current_head_is_still_final(tmp_path, branches):
    repo, passed, head = branches
    verdicts = [comment("PASS", sha=passed), comment("FAIL", sha=head)]
    assert check_git(tmp_path, repo, verdicts, head).returncode == 1


def test_a_pass_on_a_commit_outside_the_branch_does_not_carry(tmp_path, branches):
    repo, _, head = branches
    repo.git("checkout", "-q", "-b", "elsewhere", "main")
    repo.write("a.py", "a = 1\n")
    other = repo.commit("same file, another branch")
    assert check_git(tmp_path, repo, [comment("PASS", sha=other)], head).returncode == 1


def test_an_edited_or_foreign_pass_does_not_carry(tmp_path, branches):
    repo, passed, head = branches
    assert check_git(tmp_path, repo, [comment("PASS", sha=passed, edited=True)], head).returncode == 1
    assert check_git(tmp_path, repo, [comment("PASS", sha=passed, login="someone-else")], head).returncode == 1


@pytest.fixture
def sync_branch(tmp_path):
    """sync/M1-main: milestone/M1 with main merged in."""
    (tmp_path / "repo").mkdir()
    repo = Repo(tmp_path / "repo")
    repo.write("app.py", "x = 1\n")
    repo.commit("start")
    repo.git("checkout", "-q", "-b", "milestone/M1")
    repo.write("a.py", "a = 1\n")
    repo.commit("a ticket")
    repo.git("checkout", "-q", "main")
    repo.write("docs.md", "plan\n")
    repo.commit("a plan PR")
    repo.git("checkout", "-q", "-b", "sync/M1-main", "milestone/M1")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "main")
    return repo


def test_a_sync_pr_needs_no_verdict(tmp_path, sync_branch):
    head = sync_branch.git("rev-parse", "HEAD")
    proc = check_git(tmp_path, sync_branch, [], head, branch="sync/M1-main")
    assert proc.returncode == 0, proc.stdout
    assert "sync" in proc.stdout


def test_a_sync_pr_with_its_own_change_needs_a_verdict(tmp_path, sync_branch):
    sync_branch.write("a.py", "a = 'smuggled'\n")
    head = sync_branch.commit("a change riding on the sync")
    assert check_git(tmp_path, sync_branch, [], head, branch="sync/M1-main").returncode == 1


def test_a_sync_branch_into_main_is_not_a_sync_pr(tmp_path, sync_branch):
    head = sync_branch.git("rev-parse", "HEAD")
    assert check_git(tmp_path, sync_branch, [], head, branch="sync/M1-main", base="main").returncode == 1


# --- the proof covers history, not only the tree (review finding N01, D61) ----------

def test_a_pass_carries_over_update_branch_pressed_twice(tmp_path, branches):
    repo, passed, _ = branches
    repo.git("checkout", "-q", "milestone/M1")
    repo.write("c.py", "c = 1\n")
    repo.commit("ticket T-3 merged into the milestone")
    repo.git("checkout", "-q", "ticket/T-1-a")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")  # "Update branch" again
    head = repo.git("rev-parse", "HEAD")
    proc = check_git(tmp_path, repo, [comment("PASS", sha=passed)], head)
    assert proc.returncode == 0, proc.stdout


def test_a_pass_does_not_carry_over_an_ours_merge_of_another_branch(tmp_path, branches):
    """`git merge -s ours` keeps the tree and records the other branch as merged."""
    repo, passed, _ = branches
    repo.git("checkout", "-q", "-b", "ticket/T-9-unverified", "milestone/M1")
    repo.write("z.py", "z = 'nobody verified this'\n")
    repo.commit("unverified work")
    repo.git("checkout", "-q", "ticket/T-1-a")
    repo.git("merge", "-q", "-s", "ours", "--no-edit", "ticket/T-9-unverified")
    head = repo.git("rev-parse", "HEAD")
    proc = check_git(tmp_path, repo, [comment("PASS", sha=passed)], head)
    assert proc.returncode == 1, proc.stdout


def test_a_sync_pr_with_an_ours_merge_needs_a_verdict(tmp_path, sync_branch):
    """The ours-merge marks an unmerged commit as merged, so main's later copy of it would be dropped."""
    repo = sync_branch
    repo.git("checkout", "-q", "-b", "owner/correction", "main")
    repo.write("docs.md", "plan, corrected\n")
    repo.commit("a correction the Owner hasn't merged yet")
    repo.git("checkout", "-q", "sync/M1-main")
    repo.git("merge", "-q", "-s", "ours", "--no-edit", "owner/correction")
    head = repo.git("rev-parse", "HEAD")
    proc = check_git(tmp_path, repo, [], head, branch="sync/M1-main")
    assert proc.returncode == 1, proc.stdout
    assert "To fix:" in proc.stdout


def test_a_sync_pr_updated_with_its_milestone_still_needs_no_verdict(tmp_path, sync_branch):
    repo = sync_branch
    repo.git("checkout", "-q", "milestone/M1")
    repo.write("b.py", "b = 1\n")
    repo.commit("another ticket merged into the milestone")
    repo.git("checkout", "-q", "sync/M1-main")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")  # "Update branch"
    head = repo.git("rev-parse", "HEAD")
    proc = check_git(tmp_path, repo, [], head, branch="sync/M1-main")
    assert proc.returncode == 0, proc.stdout

