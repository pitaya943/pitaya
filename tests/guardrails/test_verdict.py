"""Recipe "agent-merge": a PASS verdict for the PR's current head, from an allowed verifier (D42, D44).

With one machine account (D44) the verifier posts as that account, so the verdict
is a comment (an author can't approve its own PR). A review from a verifier
account counts too. An edited PASS doesn't count, any FAIL on the head is final (edited or not),
and plan PRs never pass on a verdict.
"""

import json

from helpers import run_check

HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
OLD = "ffffffffffffffffffffffffffffffffffffffff"


def comment(result, sha=HEAD, login="example-bot", short=False, edited=False, session="verifier-session-1",
            before=""):
    shown = sha[:7] if short else sha
    created = "2026-11-20T10:00:00Z"
    line = f"- Session: {session}\n" if session else ""
    return {"user": {"login": login}, "created_at": created,
            "updated_at": "2026-11-20T11:00:00Z" if edited else created,
            "body": f"{before}## Verification: {result}\n\n- Model: m\n{line}- Round: 1\n- Head commit: {shown}\n"}


def handoff(session="builder-session-1", login="example-bot"):
    """The builder's hand-off comment: it names the session that built the work."""
    return {"user": {"login": login}, "created_at": "2026-11-20T09:00:00Z", "updated_at": "2026-11-20T09:00:00Z",
            "body": f"Hand-off for T-1.\n\n- Head commit: {HEAD}\n- Builder session: {session}\n- Model: m\n"}


def review(state, sha=HEAD, login="example-verifier"):
    return {"user": {"login": login}, "state": state, "commit_id": sha, "body": ""}


def check(tmp_path, comments=(), reviews=(), verifiers="example-bot", head=HEAD, branch="ticket/T-1-x", *extra):
    c, r = tmp_path / "comments.json", tmp_path / "reviews.json"
    c.write_text(json.dumps(list(comments)))
    r.write_text(json.dumps(list(reviews)))
    return run_check("agent-merge", "check_verdict.py", "--comments", str(c), "--reviews", str(r),
                     "--head", head, "--verifiers", verifiers, "--branch", branch, *extra)


def test_pass_comment_for_this_head_passes(tmp_path):
    proc = check(tmp_path, [comment("PASS")])
    assert proc.returncode == 0, proc.stdout


def test_a_short_sha_does_not_match(tmp_path):
    """F31: a 7-character prefix isn't a commit; the verdict names the full head."""
    proc = check(tmp_path, [comment("PASS", short=True)])
    assert proc.returncode == 1 and "40" in proc.stdout


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


def check_git(tmp_path, repo, comments, head, branch="ticket/T-1-a", base="milestone/M1", default="main", *extra):
    c = tmp_path / "comments.json"
    c.write_text(json.dumps(list(comments)))
    return run_check("agent-merge", "check_verdict.py", "--comments", str(c), "--head", head,
                     "--verifiers", "example-bot", "--branch", branch,
                     "--git-dir", str(repo.path), "--base", base, "--default", default, *extra)


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



# --- each half of the history proof on its own (noted by the verdicts on the 0.1.5 PR) ---

def test_a_squashed_update_has_the_right_tree_but_is_not_a_merge(tmp_path, branches):
    """One parent, and exactly the tree a true merge would give: only the history proof can refuse it."""
    repo, passed, _ = branches
    repo.git("reset", "-q", "--hard", passed)
    repo.git("merge", "-q", "--squash", "milestone/M1")
    head = repo.commit("the milestone, squashed in")
    merged = repo.git("merge-tree", "--write-tree", "milestone/M1", passed).splitlines()[0]
    assert repo.git("rev-parse", "HEAD^{tree}") == merged  # the tree proof alone would pass it
    assert check_git(tmp_path, repo, [comment("PASS", sha=passed)], head).returncode == 1


# --- F31: a verdict is a comment that starts with the heading and names the full head --------

def test_a_comment_that_quotes_a_verdict_is_not_a_verdict(tmp_path):
    quoted = comment("PASS", before="Hand-off notes. The last verdict said:\n\n")
    assert check(tmp_path, [quoted]).returncode == 1
    block = comment("PASS", before="> ")
    assert check(tmp_path, [block]).returncode == 1


def test_a_quoted_fail_does_not_block_a_real_pass(tmp_path):
    quoted = comment("FAIL", before="Fixed what the last verdict reported:\n\n")
    assert check(tmp_path, [quoted, comment("PASS")]).returncode == 0


def test_blank_lines_before_the_heading_are_fine(tmp_path):
    assert check(tmp_path, [comment("PASS", before="\n\n")]).returncode == 0


def test_a_sha_longer_than_a_commit_does_not_match(tmp_path):
    assert check(tmp_path, [comment("PASS", sha=HEAD + "0")]).returncode == 1


# --- F02: a FAIL is one-way (D63) ----------------------------------------------------

def test_an_edited_fail_still_counts(tmp_path):
    """Editing one character of a FAIL used to erase it; a later PASS then merged the failed head."""
    proc = check(tmp_path, [comment("FAIL", edited=True), comment("PASS")])
    assert proc.returncode == 1 and "FAIL" in proc.stdout


def test_an_edited_pass_still_does_not_count(tmp_path):
    assert check(tmp_path, [comment("PASS", edited=True)]).returncode == 1


def test_a_recorded_fail_counts_after_its_comment_is_deleted(tmp_path):
    """The workflow recorded the FAIL in a status when it saw it; the comment is gone now."""
    proc = check(tmp_path, [comment("PASS")], (), "example-bot", HEAD, "ticket/T-1-x", "--failed", HEAD)
    assert proc.returncode == 1 and "recorded" in proc.stdout and "To fix:" in proc.stdout


def test_a_recorded_fail_on_another_commit_does_not_block_this_head(tmp_path):
    proc = check(tmp_path, [comment("PASS")], (), "example-bot", HEAD, "ticket/T-1-x", "--failed", f"{OLD}, ")
    assert proc.returncode == 0, proc.stdout


def test_a_recorded_fail_on_the_passed_head_stops_the_carry(tmp_path, branches):
    repo, passed, head = branches
    proc = check_git(tmp_path, repo, [comment("PASS", sha=passed)], head, "ticket/T-1-a", "milestone/M1", "main",
                     "--failed", passed)
    assert proc.returncode == 1, proc.stdout


def test_the_check_reports_each_fail_it_saw_for_the_workflow_to_record(tmp_path, branches):
    repo, passed, head = branches
    record = tmp_path / "record.txt"
    verdicts = [comment("FAIL", sha=passed, edited=True), comment("FAIL", sha=OLD), comment("PASS", sha=head)]
    proc = check_git(tmp_path, repo, verdicts, head, "ticket/T-1-a", "milestone/M1", "main", "--record", str(record))
    assert proc.returncode == 0, proc.stdout  # the FAIL was on an earlier head; this head has its own PASS
    assert record.read_text().split() == [passed]  # OLD isn't a commit of this repository, so there's nothing to mark


def test_a_fail_on_the_head_is_reported_for_recording(tmp_path):
    record = tmp_path / "record.txt"
    proc = check(tmp_path, [comment("FAIL")], (), "example-bot", HEAD, "ticket/T-1-x", "--record", str(record))
    assert proc.returncode == 1 and record.read_text().split() == [HEAD]


# --- Q1 (D62): a verdict from the builder's own session isn't a verdict ----------------

def test_a_pass_from_the_builders_session_does_not_count(tmp_path):
    """The honest mistake: the session that built the ticket runs the checklist itself and posts PASS."""
    proc = check(tmp_path, [handoff("s-1"), comment("PASS", session="s-1")])
    assert proc.returncode == 1
    assert "builder" in proc.stdout.lower() and "session" in proc.stdout.lower() and "To fix:" in proc.stdout


def test_a_pass_from_another_session_counts(tmp_path):
    assert check(tmp_path, [handoff("s-1"), comment("PASS", session="s-2")]).returncode == 0


def test_any_builder_session_on_the_pr_is_a_builder(tmp_path):
    """A fix round in a fresh session is a second builder; neither may pass the work."""
    comments = [handoff("s-1"), handoff("s-3"), comment("PASS", session="s-3")]
    assert check(tmp_path, comments).returncode == 1


def test_a_pass_must_name_its_session(tmp_path):
    for session in ("", "unavailable:", "<id>", "${CLAUDE_SESSION_ID}"):
        proc = check(tmp_path, [handoff("s-1"), comment("PASS", session=session)])
        assert proc.returncode == 1 and "Session" in proc.stdout, session


def test_a_fail_from_the_builders_session_still_counts(tmp_path):
    comments = [handoff("s-1"), comment("FAIL", session="s-1"), comment("PASS", session="s-2")]
    assert check(tmp_path, comments).returncode == 1


def test_a_builder_session_named_by_someone_else_is_ignored(tmp_path):
    """Comment text from outside the agents' account can't void a verdict."""
    comments = [handoff("s-2", login="someone-else"), comment("PASS", session="s-2")]
    assert check(tmp_path, comments).returncode == 0


def test_a_review_from_a_separate_verifier_account_needs_no_session(tmp_path):
    proc = check(tmp_path, [handoff("s-1")], [review("APPROVED")], "example-verifier")
    assert proc.returncode == 0, proc.stdout


# --- N03 (D62, Q7): a high-risk ticket's PASS doesn't carry ---------------------------

def with_ticket(repo, risk):
    """Put the ticket file on the milestone branch, as a plan PR would, and update the ticket branch again."""
    repo.git("checkout", "-q", "milestone/M1")
    repo.write("docs/tickets/T-1.md", f"# T-1: a\n\nStatus: open\nMilestone: M1\nRisk: {risk}\n\n## Scope\n\n- `a.py`\n")
    repo.commit("the ticket file")
    repo.git("checkout", "-q", "ticket/T-1-a")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")
    return repo.git("rev-parse", "HEAD")


def test_a_low_risk_tickets_pass_carries(tmp_path, branches):
    repo, passed, _ = branches
    head = with_ticket(repo, "low")
    proc = check_git(tmp_path, repo, [comment("PASS", sha=passed)], head)
    assert proc.returncode == 0, proc.stdout


def test_a_high_risk_tickets_pass_does_not_carry(tmp_path, branches):
    repo, passed, _ = branches
    head = with_ticket(repo, "high")
    proc = check_git(tmp_path, repo, [comment("PASS", sha=passed)], head)
    assert proc.returncode == 1
    assert "Risk: high" in proc.stdout and "To fix:" in proc.stdout


def test_a_high_risk_ticket_still_passes_on_a_verdict_for_its_head(tmp_path, branches):
    repo, _, _ = branches
    head = with_ticket(repo, "high")
    assert check_git(tmp_path, repo, [comment("PASS", sha=head)], head).returncode == 0


def test_an_issue_tickets_risk_comes_from_its_body(tmp_path, branches):
    repo, passed, head = branches
    body = tmp_path / "issue.md"
    body.write_text("Risk: high\n\n## Goal\n\nx\n")
    proc = check_git(tmp_path, repo, [comment("PASS", sha=passed)], head, "ticket/12-a", "milestone/M1", "main",
                     "--ticket", str(body))
    assert proc.returncode == 1 and "Risk: high" in proc.stdout


def test_another_tickets_risk_does_not_matter(tmp_path, branches):
    repo, passed, _ = branches
    repo.git("checkout", "-q", "milestone/M1")
    repo.write("docs/tickets/T-10.md", "# T-10\n\nStatus: open\nRisk: high\n")
    repo.commit("another ticket, high risk")
    repo.git("checkout", "-q", "ticket/T-1-a")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")
    head = repo.git("rev-parse", "HEAD")
    assert check_git(tmp_path, repo, [comment("PASS", sha=passed)], head).returncode == 0
