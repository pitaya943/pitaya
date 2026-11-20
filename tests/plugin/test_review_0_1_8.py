"""The fourth batch of fixes from the review of 0.1.4 (D62's Q9, D68): skill logic and autopilot.

F15: a verifier never pushes to the branch it judges. F16: one definition of a fix round, and red-CI
retries are counted. F17: autopilot's run, claims and de-duplication are read from GitHub, with an
expiry. F19: how a coordinator starts another user-invoked skill. F25: `/setup` commits on a branch.
F30: the branch grant in `AGENTS.md` is used before anyone is asked, and an unattended session
raises an issue instead of waiting.

These are contradictions between skills and docs, so the tests keep every page to one story.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
PAGES = sorted(p for p in PLUGIN.rglob("*.md") if p.name != "CHANGELOG.md")

EVIDENCE_BRANCH = "`evidence/<PR>-<short sha>`"


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


def section(text: str, heading: str) -> str:
    """The body under a Markdown heading, up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    match = re.search(rf"^{re.escape(heading)}[ \t]*\n(.*?)(?=^#{{1,{level}}} |\Z)", text, re.M | re.S)
    assert match, f"no section {heading!r}"
    return match.group(1)


def row(text: str, first_cell: str) -> str:
    """The table row whose first cell starts with `first_cell`."""
    for line in text.splitlines():
        if line.startswith(f"| {first_cell}"):
            return line
    raise AssertionError(f"no row {first_cell!r}")


def line_with(text: str, needle: str) -> str:
    for line in text.splitlines():
        if needle in line:
            return line
    raise AssertionError(f"no line with {needle!r}")


# --- F15: a verifier never pushes to the branch it judges --------------------------------------

def test_the_verifier_is_not_told_it_may_push_screenshots_to_the_pr():
    """0.1.7 let the verifier push `docs/evidence/<ticket>/verify/` to the PR's branch. The push moved
    the head, and a verdict counts for one head, so the PASS was void the moment it was posted."""
    dispatch = section(read("skills/verify/SKILL.md"), "## 2. Dispatch a fresh verifier")
    assert "not push anything except" not in dispatch
    told = line_with(dispatch, "not modify product code or tests")
    assert "push nothing to the PR's branch" in told
    assert EVIDENCE_BRANCH in told


def test_the_verifier_skill_says_why_and_where_its_screenshots_go():
    text = read("skills/verify/SKILL.md")
    line = line_with(text, EVIDENCE_BRANCH)
    assert "docs/evidence/<ticket>/verify/" in line
    assert re.search(r"moves? the head", text), "the reason: a push to the PR moves the head the verdict names"
    assert "no pull request" in text, "an evidence branch is never merged"


def test_the_checklist_sends_real_app_evidence_to_the_evidence_branch():
    item = line_with(read("skills/verify/checklist.md"), "**Real app.**")
    assert EVIDENCE_BRANCH in item and "never the PR's branch" in item


def test_the_access_matrix_keeps_the_verifier_off_the_pr_branch():
    cells = row(read("docs/concepts/access.md"), "`docs/evidence/`").split("|")
    verifier = cells[5]
    assert "`evidence/" in verifier and "never" in verifier, verifier


def test_the_evidence_branch_is_a_documented_and_granted_branch():
    assert row(read("docs/concepts/layout.md"), "`evidence/<PR>-<short sha>`")
    branches = section(read("templates/AGENTS.md"), "## Branches")
    assert "`evidence/<PR>-<short sha>`" in branches
    cloud = section(read("README.md"), "## Cloud sessions")
    assert "`evidence/<PR>-<short sha>`" in cloud


def test_states_says_a_verdict_cannot_void_itself():
    verdict = section(read("docs/concepts/states.md"), "## PR verdict")
    assert "never pushes to the pull request's branch" in verdict


def test_no_page_lets_a_verifier_push_to_the_pull_request():
    for page in PAGES:
        for line in page.read_text().splitlines():
            if "verify/" in line and "push" in line.lower() and "docs/evidence" in line:
                assert "evidence/<PR>" in line, f"{page.relative_to(PLUGIN)}: {line[:120]}"


# --- F16: one definition of a fix round, and red-CI retries are counted ------------------------

ROUND_PAGES = ["skills/build/SKILL.md", "skills/verify/SKILL.md", "skills/autopilot/SKILL.md",
               "skills/autopilot/tick.md", "docs/concepts/escalation.md", "skills/ask-owner/SKILL.md"]


def fix_rounds() -> str:
    return section(read("docs/concepts/states.md"), "## Fix rounds")


def test_states_defines_a_fix_round_once_as_a_table():
    text = fix_rounds()
    assert "number of FAIL verdicts" in text
    assert row(text, "FAIL number 1"), "what the first FAIL starts"
    assert row(text, "FAIL number `Fix rounds` + 1"), "the FAIL that escalates"
    assert "`verdict-fail`" in text, "a deleted FAIL still counts"


@pytest.mark.parametrize("rel", ROUND_PAGES)
def test_every_page_that_talks_about_fix_rounds_points_to_the_one_definition(rel):
    assert "states.md" in read(rel) and re.search(r"states\.md[^\n]*[Ff]ix rounds|[Ff]ix rounds[^\n]*states\.md", read(rel)), rel


def test_verify_escalates_on_the_fail_after_the_last_fix_round_not_on_the_last_round():
    """0.1.7: "FAIL in the last round the harness file's 'Fix rounds' allows (default 2): recommend
    escalating". Read as verify round 2, that allowed one fix where `Fix rounds: 2` promises two."""
    after = section(read("skills/verify/SKILL.md"), "## After the verdict")
    assert "FAIL in the last round" not in after
    assert "`Fix rounds` + 1" in after and "the third" in after


def test_under_autopilot_every_fix_round_is_a_fresh_session_and_the_verdict_says_so():
    """Q9. Autopilot is stateless and can't reach the builder's session, so a verdict that said
    "fix round 1 in the builder's session" named a step nobody could take."""
    where = row(fix_rounds(), "Where a fix round runs")
    assert "`/autopilot`" in where and "every" in where and "fresh session" in where
    assert "builder's session" in where, "interactively, round 1 may stay there"
    next_step = line_with(read("skills/verify/verdict-template.md"), "- Next step:")
    assert "under `/autopilot`" in next_step
    rounds = section(read("skills/build/SKILL.md"), "## Fix rounds")
    assert "`/autopilot`" in rounds and "fresh session" in rounds
    template = line_with(read("skills/setup/harness-template.md"), "- Fix rounds:")
    assert "`/autopilot`" in template


def test_no_page_says_round_one_is_always_the_builders_session():
    for rel in ("docs/concepts/escalation.md", "skills/build/SKILL.md", "skills/setup/harness-template.md"):
        text = read(rel)
        assert "the same Builder session fixes" not in text, rel
        assert "Round 1 in the builder's session, the rest in fresh sessions" not in text, rel


def test_red_ci_retries_are_counted_and_capped():
    """A red CI started a new build session each tick, and only FAIL verdicts were counted, so a
    persistently red CI restarted builders without limit."""
    retries = row(fix_rounds(), "Red CI")
    assert "same" in retries and "round" in retries, "a retry belongs to the round in progress"
    assert "CI retry" in retries and "2" in retries and "escalate" in retries
    tick = row(read("skills/autopilot/tick.md"), "CI retries used")
    assert "`Autopilot: CI retry" in tick
    skill = section(read("skills/autopilot/SKILL.md"), "## Each tick")
    red = line_with(skill, "CI red")
    assert "CI retry" in red and "ask-owner" in red
    assert "FAIL verdict" not in red, "a red CI and a FAIL are two cases with two counters"
    assert "CI retries" in line_with(read("skills/setup/harness-template.md"), "- Autopilot:")


def test_the_states_table_row_points_at_the_definition():
    assert "[Fix rounds](#fix-rounds)" in row(read("docs/concepts/states.md"), "Fix rounds used")


# --- F17: autopilot's run, claims and de-duplication are read from GitHub ----------------------

def tick() -> str:
    return read("skills/autopilot/tick.md")


def autopilot() -> str:
    return read("skills/autopilot/SKILL.md")


def at_work() -> str:
    return section(tick(), "## Sessions at work")


def test_the_ten_minute_rule_that_read_comments_autopilot_never_posted_is_gone():
    """wake.md skipped "a PR whose latest comment from autopilot is less than ten minutes old", but
    autopilot posted on the tracking issue, never on PRs: the rule matched nothing."""
    for page in PAGES:
        assert "ten minutes" not in page.read_text(), page.relative_to(PLUGIN)


def test_a_tick_posts_a_start_comment_on_the_pr_before_it_starts_a_session():
    text = at_work()
    for kind in ("verifier", "fix round <n>", "CI retry <k>"):
        assert kind in line_with(text, "`Autopilot: "), kind
    assert "full head" in text, "the comment names the head, so a new head needs a new session"
    assert "before" in line_with(text, "`Autopilot: ").lower()


def test_a_second_tick_does_not_start_the_same_session_again():
    text = at_work()
    assert re.search(r"same (action|kind)[^.]*same head", text), "what makes two starts duplicates"
    assert "read the comments again" in text and "earliest" in text, "two ticks at once: post, re-read, the earliest wins"


def test_start_comments_count_only_from_the_machine_account_and_by_githubs_clock():
    text = at_work()
    assert "machine account" in text, "anyone can comment; a stranger's line must not stall a PR"
    assert "`created_at`" in text, "the time GitHub recorded, not a time written in the text"


def test_a_claim_expires_and_is_taken_over_without_deleting_a_branch():
    """A claim was a remote branch with no expiry; a dead builder left its ticket claimed for good,
    and agents may not delete remote branches."""
    text = at_work()
    assert "claim expiry" in text and "2 hours" in text
    assert "take over" in text or "takes over" in text
    assert re.search(r"same branch", text) and "never delete" in text.lower()
    assert "`Started:`" in text, "a claim's time is the tracking-issue line that names it"
    assert "no start line" in text, "a branch a tick pushed and then died before recording"


def test_the_report_and_cut_claims_expire_too():
    """Batch 3 left this: a report or planning session that died stalled its step until someone
    deleted the branch."""
    closing = section(tick(), "## Closing the milestone")
    cut = section(tick(), "## The next cut")
    for name, text, branch in (("closing", closing, "`plan/M<n>-report`"), ("cut", cut, "`plan/M<n+1>-cut`")):
        waiting = next(l for l in text.splitlines() if re.match(r"\d\. The branch " + re.escape(branch), l))
        assert "at work" in waiting and "#sessions-at-work" in waiting, name
        assert "expired" in waiting and "same branch" in waiting, name


def test_a_builder_continues_a_branch_that_already_exists():
    step = line_with(read("skills/build/SKILL.md"), "Branch `ticket/<id>-<short-slug>`")
    assert "already exists" in step and "continue" in step
    assert "Push after each commit" in read("skills/build/SKILL.md"), "pushes are how a tick sees a builder is alive"


def test_a_run_has_a_start_line_and_the_budget_is_measured_from_it():
    """The budget was "5 tickets or 8 hours per run", but a scheduled wake-up is a fresh session,
    so each one was a new run and nothing stored the start."""
    first = section(autopilot(), "## Before the first tick")
    assert "`Run started" in first and "`wake`" in first
    stop = section(autopilot(), "## Stop")
    budget = line_with(stop, "budget")
    assert "`Run started" in budget and "`created_at`" in budget
    assert "merged into `milestone/M<n>` since" in budget, "the count is read from GitHub, not kept"
    assert "wake" in read("skills/autopilot/SKILL.md").split("argument-hint:", 1)[1].splitlines()[0]


def test_a_wake_up_never_starts_a_new_run():
    wake = read("skills/autopilot/wake.md")
    for mechanism in ("**Schedule**", "**GitHub Action**"):
        assert "`/pitaya:autopilot M<n> wake`" in row(wake, mechanism), mechanism
    assert "never starts a new run" in wake
    assert "`concurrency`" in row(wake, "**GitHub Action**"), "one tick at a time where the tool offers a lock"


def test_states_says_where_the_run_and_the_claims_live():
    states = read("docs/concepts/states.md")
    assert "`Run started" in row(states, "Autopilot progress")
    claimed = row(states, "Ticket claimed")
    assert "`Started:`" in claimed and "expir" in claimed
    assert row(states, "Session at work")


def test_the_tick_comment_examples_show_the_new_lines():
    comments = section(tick(), "## Comments to post")
    assert "> Run started" in comments and "> Autopilot: verifier started for" in comments


# --- F19: how a coordinator starts another user-invoked skill ----------------------------------

def test_the_skill_rule_matches_what_autopilot_does():
    """skills/README.md: "A user-invoked skill may call model-invoked ones, but never another
    user-invoked skill", while autopilot's whole job is to start build, verify, plan and report."""
    readme = read("skills/README.md")
    rule = line_with(readme, "never another user-invoked skill")
    assert "in its own session" in rule
    assert "coordinator" in readme and "new session" in readme and "slash command" in readme
    assert "`SKILL.md`" in readme, "the subagent path: the model can't invoke it, so it reads the file"


def test_autopilot_starts_a_skill_by_slash_command_or_by_file_path():
    starting = section(tick(), "## Starting sessions")
    assert "slash command" in starting and "prompt" in starting
    fallback = line_with(starting, "`SKILL.md`")
    assert "can't invoke" in fallback and "path" in fallback and "read" in fallback
    assert "from memory" in fallback


def test_one_session_is_never_given_two_slash_commands():
    """A session's prompt is one slash command; "`/pitaya:design M<n+1>` and then `/pitaya:plan
    M<n+1>`" asked the model to invoke the second, which `disable-model-invocation` forbids."""
    for rel in ("skills/autopilot/SKILL.md", "skills/autopilot/tick.md"):
        assert not re.search(r"`/pitaya:design M<n\+1>`,? and then `/pitaya:plan", read(rel)), rel
    cut = section(tick(), "## The next cut")
    assert "`/pitaya:design M<n+1>`" in cut and "plan/SKILL.md" in cut
    hand_over = section(read("skills/design/SKILL.md"), "## Hand over")
    assert "plan/SKILL.md" in hand_over and "read" in hand_over


# --- F30: the branch grant is used before anyone is asked --------------------------------------

GRANT = 'the "Branches" section of `AGENTS.md`'
ASKERS = {
    "skills/build/SKILL.md": "Branch `ticket/<id>-<short-slug>`",
    "skills/plan/tickets.md": "on a branch named `plan/<short-slug>`",
    "skills/plan/milestones.md": "Commit on a `plan/<slug>` branch",
    "skills/autopilot/SKILL.md": "assigned branch",
}


@pytest.mark.parametrize("rel", sorted(ASKERS))
def test_a_skill_uses_the_grant_before_it_asks(rel):
    """`/setup` installs the Owner's standing grant in AGENTS.md, and the skills still stopped to
    ask the user, who isn't there in a session autopilot started."""
    line = line_with(read(rel), ASKERS[rel])
    assert GRANT in line, rel
    assert line.index(GRANT) < line.lower().index("ask the user"), "the grant comes first, asking second"


@pytest.mark.parametrize("rel", sorted(ASKERS))
def test_an_unattended_session_raises_an_issue_instead_of_waiting(rel):
    line = line_with(read(rel), ASKERS[rel])
    assert "`needs-owner`" in line and "nobody" in line, rel


def test_autopilot_does_not_hand_out_permission_it_was_never_given():
    """"Pass that permission to every session you start" is another agent's word, not the Owner's."""
    text = autopilot()
    assert "pass that permission" not in text
    line = line_with(text, "assigned branch")
    assert "your word" in line and "every session you start" in line


def test_every_skill_that_makes_a_branch_is_covered_by_the_grant():
    branches = section(read("templates/AGENTS.md"), "## Branches")
    for prefix in ("plan/", "ticket/", "milestone/", "sync/", "setup/", "evidence/"):
        assert f"`{prefix}" in branches, prefix
    assert "without asking" in branches


def test_the_readme_says_what_an_unattended_cloud_session_does_without_the_grant():
    cloud = section(read("README.md"), "## Cloud sessions")
    assert "`needs-owner`" in cloud and "unattended" in cloud


# --- F25: /setup commits on a branch -----------------------------------------------------------

def test_setup_commits_on_a_setup_branch_and_opens_a_pr():
    """"Commit ... Open a PR only if the user asks", run on `main`, left a commit there that the
    just-installed rules and the `no_push_main` hook forbid pushing."""
    install = section(read("skills/setup/SKILL.md"), "## 3. Install and write")
    last = [l for l in install.splitlines() if re.match(r"\d+\. ", l)][-1]
    assert "`setup/pitaya`" in last
    assert last.index("`setup/pitaya`") < last.index("commit"), "branch first, then commit"
    assert "Open a PR only if the user asks" not in install
    assert "open a PR" in last and "the Owner merges" in last
    assert "never on `main`" in last


def test_setup_says_what_to_do_without_a_remote_and_on_a_re_run():
    last = line_with(read("skills/setup/SKILL.md"), "`setup/pitaya`")
    assert "no remote" in last, "nothing to open a PR on"
    assert "`setup/update-<version>`" in last, "a re-run after the first PR merged needs a new name"


# --- found by tracing every flow the new rules sit in (decision log) ---------------------------

def work_row(first_cell: str) -> list[str]:
    return [c.strip() for c in row(at_work(), first_cell).split("|")[1:-1]]


def test_a_first_build_is_at_work_until_its_hand_off_not_until_its_pr():
    """A builder opens its PR, then waits for CI and fixes a red one before it hands off. Had the PR
    been its result, the first red CI would have started a CI retry beside the live builder."""
    result = work_row("A builder")[1]
    assert "`Builder session:`" in result
    assert "the PR, for a first build" not in result


def test_an_expired_session_is_handled_by_the_prs_state_not_always_taken_over():
    """A fix session that pushed a green head and died before its comment needs a verifier, not a
    second builder."""
    expired = work_row("A builder")[3]
    assert "by its state" in expired
    assert "no PR" in expired and "same branch" in expired, "only a branch with no PR is simply taken over"


def test_a_builder_that_escalated_is_not_started_again_every_expiry():
    result = work_row("A builder")[1]
    assert "`needs-owner`" in result
    assert "blocked" in row(at_work(), "A builder")


def test_a_wake_with_no_open_run_says_so_once():
    """After an upgrade the tracking issue has no `Run started` line; ending silently would look
    like autopilot running while nothing moved."""
    run = line_with(autopilot(), "**The run.**")
    assert "say so" in run and "unless" in run


def test_each_tick_checks_the_run_is_still_open():
    read_step = line_with(section(autopilot(), "## Each tick"), "**Read:**")
    assert "`Run started`" in read_step


def test_setup_asks_before_using_its_branch_in_a_session_with_an_assigned_branch():
    """The grant `/setup` installs is in the very commit it is about to push: it isn't the Owner's
    until that PR merges, so it can't authorise its own branch."""
    last = line_with(read("skills/setup/SKILL.md"), "`setup/pitaya`")
    assert "assigned branch" in last and "ask the user" in last
