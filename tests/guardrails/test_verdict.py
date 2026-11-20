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


# --- plan PRs into a milestone branch: the Level 4 cut (F04) and the report PR (F18); D67 ---

LEVEL_3 = "Agents merge ticket PRs into milestone branches; only the Owner merges main"
LEVEL_4 = "Agents merge ticket and plan PRs into milestone branches; only the Owner merges main"
MILESTONE = "# M{n}: a milestone\n\nStatus: {status}\n\n## Goal\n\nSomething works.\n\n## Exit criteria\n\n1. It runs.\n\n## Tickets\n\n{tickets}\n"
TICKET = "# {id}\n\nStatus: {status}\nMilestone: {milestone}\nRisk: low\n\n## Done when\n\n1. It works.\n"


def harness(autonomy):
    return f"# Harness\n\n## People and accounts\n\n- Owner: example-owner.\n- Autonomy: {autonomy}.\n  The alternatives: at Level 4, \"{LEVEL_4}\".\n"


@pytest.fixture
def planned(tmp_path):
    """main with M1 active (T-1 done on its branch) and M2 planned; milestone/M1 and milestone/M2 exist."""
    (tmp_path / "repo").mkdir()
    repo = Repo(tmp_path / "repo")
    repo.write("app.py", "x = 1\n")
    repo.write("docs/agents/harness.md", harness(LEVEL_3))
    repo.write("docs/milestones/M1.md", MILESTONE.format(n=1, status="active", tickets="T-1: first"))
    repo.write("docs/milestones/M2.md", MILESTONE.format(n=2, status="planned", tickets=""))
    repo.write("docs/tickets/T-1.md", TICKET.format(id="T-1", status="open", milestone="M1"))
    repo.commit("the roadmap and M1's cut")
    repo.git("checkout", "-q", "-b", "milestone/M1")
    repo.write("docs/tickets/T-1.md", TICKET.format(id="T-1", status="done", milestone="M1"))
    repo.commit("T-1 merged")
    repo.git("branch", "milestone/M2", "main")
    return repo


def level_4(repo):
    """The Owner sets the Level 4 autonomy on main; milestone/M2 is cut from it afterwards."""
    repo.git("checkout", "-q", "main")
    repo.write("docs/agents/harness.md", harness(LEVEL_4))
    repo.commit("the Owner moves to Level 4")
    repo.git("branch", "-f", "milestone/M2", "main")


def cut(repo, base="milestone/M2", branch="plan/M2"):
    """A plan PR that cuts M2 inside its branch: the design, two tickets, Status: active."""
    repo.git("checkout", "-q", "-b", branch, base)
    repo.write("docs/milestones/M2.md", MILESTONE.format(n=2, status="active", tickets="T-2: second\nT-3: third"))
    repo.write("docs/milestones/M2-design.md", "# M2 design\n\n## Scenarios\n\nS-1: it works.\n")
    repo.write("docs/tickets/T-2.md", TICKET.format(id="T-2", status="open", milestone="M2"))
    repo.write("docs/tickets/T-3.md", TICKET.format(id="T-3", status="open", milestone="M2"))
    return repo.commit("cut M2")


def report_pr(repo, status="done", report=True, milestone="M1", base="milestone/M1"):
    """The report PR: Status: done and docs/reports/M1.md, into the milestone's own branch."""
    repo.git("checkout", "-q", "-b", "plan/M1-report", base)
    if status:
        path = f"docs/milestones/{milestone}.md"
        text = (repo.path / path).read_text()
        repo.write(path, re.sub(r"^Status: \w+$", f"Status: {status}", text, flags=re.M))
    if report:
        repo.write("docs/reports/M1.md", "# Report: M1\n\n## Conclusion\n\nReady.\n")
    return repo.commit("the report for M1")


import re  # noqa: E402


def test_a_level_4_cut_into_its_milestone_branch_needs_no_verdict(tmp_path, planned):
    """F04: the `verdict` status is required on milestone/*, and no verifier judges a plan PR."""
    level_4(planned)
    head = cut(planned)
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 0, proc.stdout
    assert "cut" in proc.stdout


def test_a_cut_needs_the_level_4_autonomy_setting(tmp_path, planned):
    """At Level 3 the Owner approves each cut, on main: a plan PR into a milestone branch waits for the Owner."""
    head = cut(planned)
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1 and "Owner" in proc.stdout, proc.stdout


def test_the_autonomy_setting_is_read_from_the_default_branch(tmp_path, planned):
    """The milestone branch is where agents merge; only the Owner's main says what they may merge."""
    planned.git("checkout", "-q", "milestone/M2")
    planned.write("docs/agents/harness.md", harness(LEVEL_4))
    planned.commit("Level 4, but only on the milestone branch")
    head = cut(planned)
    assert check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2").returncode == 1


def test_the_alternatives_note_under_the_autonomy_line_does_not_count(tmp_path, planned):
    """The template's note quotes the Level 4 value under a Level 3 setting; only the field's own value counts."""
    assert LEVEL_4 in (planned.path / "docs/agents/harness.md").read_text()
    head = cut(planned)
    assert check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2").returncode == 1


def test_a_cut_that_changes_code_waits_for_the_owner(tmp_path, planned):
    level_4(planned)
    cut(planned)
    planned.write("app.py", "x = 2\n")
    head = planned.commit("code riding on the cut")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1 and "app.py" in proc.stdout, proc.stdout


def test_a_cut_may_not_change_a_ticket_that_exists(tmp_path, planned):
    """A cut adds tickets. Re-planning one that exists, such as loosening its conditions, is the Owner's."""
    level_4(planned)
    planned.git("checkout", "-q", "-b", "plan/replan", "milestone/M1")
    planned.git("merge", "-q", "--no-edit", "main")
    planned.git("branch", "-f", "milestone/M1", "HEAD")
    planned.write("docs/tickets/T-1.md", TICKET.format(id="T-1", status="open", milestone="M1").replace("It works", "It compiles"))
    head = planned.commit("loosen T-1")
    proc = check_git(tmp_path, planned, [], head, branch="plan/replan", base="milestone/M1")
    assert proc.returncode == 1 and "T-1" in proc.stdout, proc.stdout


def test_a_cut_may_not_delete_a_ticket(tmp_path, planned):
    level_4(planned)
    planned.git("checkout", "-q", "-b", "plan/drop", "milestone/M2")
    planned.remove("docs/tickets/T-1.md")
    head = planned.commit("drop T-1")
    assert check_git(tmp_path, planned, [], head, branch="plan/drop", base="milestone/M2").returncode == 1


def test_a_plan_pr_into_the_default_branch_never_passes(tmp_path, planned):
    """Whatever the level, only the Owner merges main: a cut aimed there gets no status."""
    level_4(planned)
    head = cut(planned, base="main")
    proc = check_git(tmp_path, planned, [comment("PASS", sha=head)], head, branch="plan/M2", base="main")
    assert proc.returncode == 1 and "Owner" in proc.stdout, proc.stdout


def test_a_fail_on_a_cuts_head_still_blocks_it(tmp_path, planned):
    level_4(planned)
    head = cut(planned)
    proc = check_git(tmp_path, planned, [comment("FAIL", sha=head)], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1, proc.stdout


def test_a_cut_updated_with_its_base_still_needs_no_verdict(tmp_path, planned):
    """"Require branches to be up to date": a sync merged meanwhile, and the cut pressed "Update branch"."""
    level_4(planned)
    cut(planned)
    planned.git("checkout", "-q", "milestone/M2")
    planned.write("other.md", "merged meanwhile\n")
    planned.commit("something else merged into the milestone")
    planned.git("checkout", "-q", "plan/M2")
    planned.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M2")
    head = planned.git("rev-parse", "HEAD")
    assert check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2").returncode == 0


def test_a_milestone_pr_never_passes_even_at_level_4(tmp_path, planned):
    level_4(planned)
    head = planned.git("rev-parse", "milestone/M1")
    proc = check_git(tmp_path, planned, [comment("PASS", sha=head)], head, branch="milestone/M1", base="main")
    assert proc.returncode == 1 and "Owner" in proc.stdout


def test_a_report_pr_needs_no_verdict(tmp_path, planned):
    """F18: the milestone PR itself carries Status: done, so some PR into the milestone branch must set it."""
    head = report_pr(planned)
    proc = check_git(tmp_path, planned, [], head, branch="plan/M1-report")
    assert proc.returncode == 0, proc.stdout
    assert "report" in proc.stdout


def test_a_report_pr_may_update_the_report_alone(tmp_path, planned):
    """After the Owner sends a milestone back, Status is done already; the new report is the only change."""
    planned.git("checkout", "-q", "milestone/M1")
    planned.write("docs/milestones/M1.md", MILESTONE.format(n=1, status="done", tickets="T-1: first"))
    planned.commit("the first report PR merged")
    head = report_pr(planned, status="")
    assert check_git(tmp_path, planned, [], head, branch="plan/M1-report").returncode == 0


def test_a_report_pr_may_not_change_anything_else_in_the_milestone_file(tmp_path, planned):
    """The honest mistake: making the exit criteria fit what was built, in the PR nobody verifies."""
    report_pr(planned)
    text = (planned.path / "docs/milestones/M1.md").read_text()
    planned.write("docs/milestones/M1.md", text.replace("1. It runs.", "1. It compiles."))
    head = planned.commit("and an easier exit criterion")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M1-report")
    assert proc.returncode == 1 and "Status" in proc.stdout, proc.stdout


def test_a_report_pr_sets_only_done(tmp_path, planned):
    head = report_pr(planned, status="planned")
    assert check_git(tmp_path, planned, [], head, branch="plan/M1-report").returncode == 1


def test_a_report_pr_closes_only_its_own_milestone(tmp_path, planned):
    head = report_pr(planned, milestone="M2")
    assert check_git(tmp_path, planned, [], head, branch="plan/M1-report").returncode == 1


def test_a_report_pr_with_any_other_file_waits_for_the_owner(tmp_path, planned):
    report_pr(planned)
    planned.write("docs/decisions.md", "| D1 | a decision |\n")
    head = planned.commit("and a decision")
    assert check_git(tmp_path, planned, [], head, branch="plan/M1-report").returncode == 1


def test_a_milestone_with_an_open_ticket_is_not_done(tmp_path, planned):
    """Status: done claims every ticket is done; the check reads the tickets instead of believing it."""
    planned.git("checkout", "-q", "milestone/M1")
    planned.write("docs/tickets/T-9.md", TICKET.format(id="T-9", status="open", milestone="M1"))
    planned.commit("a ticket still open")
    head = report_pr(planned)
    proc = check_git(tmp_path, planned, [], head, branch="plan/M1-report")
    assert proc.returncode == 1 and "T-9" in proc.stdout, proc.stdout


def test_another_milestones_open_ticket_does_not_block_the_report(tmp_path, planned):
    planned.git("checkout", "-q", "milestone/M1")
    planned.write("docs/tickets/T-9.md", TICKET.format(id="T-9", status="open", milestone="M2"))
    planned.commit("a ticket of the next milestone")
    head = report_pr(planned)
    assert check_git(tmp_path, planned, [], head, branch="plan/M1-report").returncode == 0


def test_a_fail_on_a_report_prs_head_still_blocks_it(tmp_path, planned):
    head = report_pr(planned)
    assert check_git(tmp_path, planned, [comment("FAIL", sha=head)], head, branch="plan/M1-report").returncode == 1


def test_the_check_reads_the_autonomy_values_the_harness_template_offers():
    """One source: the values `/setup` writes are the values the check understands."""
    import importlib.util
    import sys as _sys
    from helpers import FILES, PLUGIN_ROOT
    _sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("check_verdict", FILES / "agent-merge" / "check_verdict.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    template = (PLUGIN_ROOT / "skills" / "setup" / "harness-template.md").read_text()
    assert LEVEL_3 in template and LEVEL_4 in template
    assert module.agents_merge_plans(f"- Autonomy: {LEVEL_4}.\n")
    assert not module.agents_merge_plans(f"- Autonomy: {LEVEL_3}.\n")
    assert not module.agents_merge_plans("- Autonomy: Only the Owner merges `main`.\n")
    default = re.search(r"^- Autonomy: .*(?:\n  .*)*", template, re.M).group(0)
    assert not module.agents_merge_plans(default)


def test_a_cut_may_not_change_another_milestones_file(tmp_path, planned):
    """The roadmap changes only through the Owner: a cut fills in its own milestone, not its neighbours."""
    level_4(planned)
    cut(planned)
    planned.write("docs/milestones/M1.md", MILESTONE.format(n=1, status="done", tickets="T-1: first"))
    head = planned.commit("and M1 marked done from M2's cut")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1 and "docs/milestones/M1.md" in proc.stdout, proc.stdout


def test_a_cut_deletes_nothing(tmp_path, planned):
    level_4(planned)
    cut(planned)
    planned.remove("docs/milestones/M1.md")
    head = planned.commit("and a milestone dropped from the roadmap")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1 and "delete" in proc.stdout, proc.stdout


def test_a_report_pr_may_not_delete_the_report(tmp_path, planned):
    planned.git("checkout", "-q", "milestone/M1")
    planned.write("docs/reports/M1.md", "# Report: M1\n")
    planned.commit("an earlier report")
    planned.git("checkout", "-q", "-b", "plan/M1-report")
    planned.remove("docs/reports/M1.md")
    head = planned.commit("the report removed")
    assert check_git(tmp_path, planned, [], head, branch="plan/M1-report").returncode == 1


def test_a_plan_pr_that_changes_nothing_does_not_pass(tmp_path, planned):
    planned.git("checkout", "-q", "-b", "plan/empty", "milestone/M1")
    head = planned.commit("nothing")
    assert check_git(tmp_path, planned, [], head, branch="plan/empty").returncode == 1


# --- 0.1.9: the gaps the verdict on 0.1.7 found in the two proofs above (D69) ---

def test_a_cut_may_not_set_its_milestone_to_done(tmp_path, planned):
    """A cut fills its milestone in; closing it is the report PR's, which checks that no ticket is open."""
    level_4(planned)
    cut(planned)
    text = (planned.path / "docs/milestones/M2.md").read_text()
    planned.write("docs/milestones/M2.md", text.replace("Status: active", "Status: done"))
    head = planned.commit("and M2 closed in the cut that opens its tickets")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1 and "done" in proc.stdout, proc.stdout


def test_a_report_mixed_with_a_new_ticket_is_not_a_cut(tmp_path, planned):
    """The mix of two allowed shapes: Status: done and the report, plus a ticket that is still open."""
    level_4(planned)
    planned.git("checkout", "-q", "milestone/M1")
    planned.git("merge", "-q", "--no-edit", "main")
    report_pr(planned)
    planned.write("docs/tickets/T-9.md", TICKET.format(id="T-9", status="open", milestone="M1"))
    head = planned.commit("and one more ticket for M1")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M1-report")
    assert proc.returncode == 1, proc.stdout


@pytest.mark.parametrize("path", ["docs/reports/M1.md", "docs/adr/0001-storage.md", "docs/milestones/M1-design.md"])
def test_a_cut_may_not_change_a_plan_record_that_exists(tmp_path, planned, path):
    """A report, an ADR or an earlier design is a record the Owner read; a cut only adds."""
    level_4(planned)
    planned.git("checkout", "-q", "milestone/M2")
    planned.write(path, "# A record\n\nWhat the Owner read.\n")
    planned.commit("a record that exists")
    cut(planned)
    planned.write(path, "# A record\n\nSomething else.\n")
    head = planned.commit("and a record rewritten")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1 and path in proc.stdout, proc.stdout


@pytest.mark.parametrize("path", ["docs/agents/glossary.md", "docs/agents/architecture.md", "docs/decisions.md"])
def test_a_cut_may_still_update_the_living_plan_files(tmp_path, planned, path):
    """`/plan` keeps the glossary, the architecture map and the decision log current in the same change."""
    level_4(planned)
    planned.git("checkout", "-q", "milestone/M2")
    planned.write(path, "# Living\n\nfirst\n")
    planned.commit("a living file")
    cut(planned)
    planned.write(path, "# Living\n\nfirst\nsecond\n")
    head = planned.commit("and a new term")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 0, proc.stdout


def test_a_cut_may_add_a_report_or_an_adr(tmp_path, planned):
    level_4(planned)
    cut(planned)
    planned.write("docs/adr/0002-queue.md", "# ADR 2\n")
    head = planned.commit("and a new ADR")
    assert check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2").returncode == 0


def test_a_stale_report_branch_is_judged_on_what_merging_it_gives(tmp_path, planned):
    """A ticket opened on the milestone branch after the report branch was made is still open after the merge."""
    head = report_pr(planned)
    planned.git("checkout", "-q", "milestone/M1")
    planned.write("docs/tickets/T-9.md", TICKET.format(id="T-9", status="open", milestone="M1"))
    planned.commit("a ticket added after the report branch was made")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M1-report")
    assert proc.returncode == 1 and "T-9" in proc.stdout, proc.stdout


def test_a_report_branch_that_conflicts_with_its_base_does_not_pass(tmp_path, planned):
    head = report_pr(planned)
    planned.git("checkout", "-q", "milestone/M1")
    planned.write("docs/reports/M1.md", "# Another report\n")
    planned.commit("another report landed first")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M1-report")
    assert proc.returncode == 1, proc.stdout


@pytest.mark.parametrize("status", ["done, criteria waived", "done (two tickets dropped)", "done-ish"])
def test_a_report_pr_sets_exactly_done(tmp_path, planned, status):
    """`Status: done` with a rider is a different claim; the Owner reads it."""
    planned.git("checkout", "-q", "-b", "plan/M1-report", "milestone/M1")
    text = (planned.path / "docs/milestones/M1.md").read_text()
    planned.write("docs/milestones/M1.md", text.replace("Status: active", f"Status: {status}"))
    planned.write("docs/reports/M1.md", "# Report: M1\n")
    head = planned.commit("the report for M1")
    assert check_git(tmp_path, planned, [], head, branch="plan/M1-report").returncode == 1


def test_a_ticket_done_with_a_rider_is_not_done(tmp_path, planned):
    planned.git("checkout", "-q", "milestone/M1")
    planned.write("docs/tickets/T-1.md", TICKET.format(id="T-1", status="done, criteria waived", milestone="M1"))
    planned.commit("T-1 half done")
    head = report_pr(planned)
    proc = check_git(tmp_path, planned, [], head, branch="plan/M1-report")
    assert proc.returncode == 1 and "T-1" in proc.stdout, proc.stdout


@pytest.mark.parametrize("autonomy", [
    "Agents merge ticket PRs, never plan PRs, into milestone branches; only the Owner merges main",
    "Agents merge ticket PRs into milestone branches (plan PRs wait for the Owner); only the Owner merges main",
    "Agents merge ticket and plan PRs into main",
])
def test_a_hand_written_autonomy_value_is_not_level_4(tmp_path, planned, autonomy):
    """Only the value `/setup` offers for Level 4 lets a cut merge; a sentence that mentions plan PRs doesn't."""
    planned.git("checkout", "-q", "main")
    planned.write("docs/agents/harness.md", harness(autonomy))
    planned.commit("a hand-written Autonomy value")
    planned.git("branch", "-f", "milestone/M2", "main")
    head = cut(planned)
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1 and "Autonomy" in proc.stdout, proc.stdout


@pytest.mark.parametrize("autonomy", [LEVEL_4, f"`{LEVEL_4}`", LEVEL_4.upper(), LEVEL_4.replace("; only", ";  Only"),
                                      LEVEL_4.split(";")[0], f'"{LEVEL_4.split(";")[0]}".'])
def test_the_level_4_value_is_read_whatever_its_case_or_quoting(tmp_path, planned, autonomy):
    planned.git("checkout", "-q", "main")
    planned.write("docs/agents/harness.md", harness(autonomy))
    planned.commit("Level 4")
    planned.git("branch", "-f", "milestone/M2", "main")
    head = cut(planned)
    assert check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2").returncode == 0


@pytest.mark.parametrize("status", ["done, criteria waived", "Done.", "done (all tickets)", "DONE"])
def test_a_cut_may_not_close_its_milestone_with_a_rider_either(tmp_path, planned, status):
    """Found by the audit before the 0.1.9 PR: the cut's guard asked for exactly `done`, so a rider slipped by."""
    level_4(planned)
    cut(planned)
    text = (planned.path / "docs/milestones/M2.md").read_text()
    planned.write("docs/milestones/M2.md", text.replace("Status: active", f"Status: {status}"))
    head = planned.commit("and M2 closed, with a rider")
    proc = check_git(tmp_path, planned, [], head, branch="plan/M2", base="milestone/M2")
    assert proc.returncode == 1 and "done" in proc.stdout, proc.stdout


def test_a_cut_into_a_milestone_already_marked_done_may_add_tickets(tmp_path, planned):
    """A milestone the Owner sent back: its branch says done, and the new tickets arrive like a cut."""
    level_4(planned)
    planned.git("checkout", "-q", "milestone/M2")
    planned.write("docs/milestones/M2.md", MILESTONE.format(n=2, status="done", tickets="T-2: second"))
    planned.commit("M2 was closed, then sent back")
    planned.git("checkout", "-q", "-b", "plan/M2-more")
    planned.write("docs/milestones/M2.md", MILESTONE.format(n=2, status="done", tickets="T-2: second\nT-5: fifth"))
    planned.write("docs/tickets/T-5.md", TICKET.format(id="T-5", status="open", milestone="M2"))
    head = planned.commit("one more ticket")
    assert check_git(tmp_path, planned, [], head, branch="plan/M2-more", base="milestone/M2").returncode == 0
