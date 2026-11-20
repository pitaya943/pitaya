"""The third batch of fixes from the review of 0.1.4 (D62's Q4 and Q8, D67): the branch and merge model.

F04: Level 4's cut can merge (the verdict check passes it without a verifier), and a milestone's
state is read from its own branch. F18: one definition of a done milestone: the report PR sets
`Status: done` inside the milestone PR, and the Owner's merge of that PR brings it to `main`.

The check itself is tested in tests/guardrails/test_verdict.py and test_workflows.py. These tests
keep the skills and docs to one story, so the contradiction the review found can't come back.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
FILES = PLUGIN / "docs" / "guardrails" / "files"
PAGES = sorted(p for p in PLUGIN.rglob("*") if p.suffix in {".md", ".yml", ".py", ".json"} and p.name != "CHANGELOG.md")

LEVEL_3 = "Agents merge ticket PRs into milestone branches; only the Owner merges main"
LEVEL_4 = "Agents merge ticket and plan PRs into milestone branches; only the Owner merges main"
REPORT_BRANCH = "plan/M<n>-report"


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


# --- F18: one definition of a done milestone ---------------------------------------------------

# Each of these said, somewhere in 0.1.6, that a plan PR into main marks a milestone done after its sign-off.
OLD_DEFINITIONS = [
    r"closing plan PR",
    r"sets M<n> done",
    r"sets M<n> to `Status: done`",
    r"sets the previous milestone to `Status: done`",
    r"plan PR that closes",
    r"plan PR that sets `?Status",
    r"only the Owner's merge of a plan PR changes it",
]


@pytest.mark.parametrize("pattern", OLD_DEFINITIONS)
def test_no_page_has_a_plan_pr_mark_a_milestone_done_after_its_sign_off(pattern):
    hits = [str(p.relative_to(PLUGIN)) for p in PAGES if re.search(pattern, p.read_text())]
    assert not hits, hits


@pytest.mark.parametrize("rel", ["skills/report/SKILL.md", "skills/plan/milestones.md", "skills/autopilot/tick.md",
                                 "docs/concepts/states.md", "docs/guardrails/agent-merge.md"])
def test_the_report_pr_is_named_the_same_everywhere(rel):
    """`/report` writes it, `/autopilot` merges it and the verdict check passes it: one name, one branch."""
    text = read(rel)
    assert "report PR" in text, rel
    assert REPORT_BRANCH in text, rel


def test_report_sets_done_inside_the_milestone_pr():
    text = read("skills/report/SKILL.md")
    assert "Status: done" in text and "docs/reports/M<n>.md" in text
    assert "`milestone/M<n>`" in text
    # The report PR merges first, so the milestone PR never reaches main without the status.
    assert re.search(r"report PR[^.]*merged[^.]*open the milestone PR|open the milestone PR[^.]*(once|after)[^.]*report PR[^.]*merged",
                     text), "the order of the two PRs isn't stated"


def test_plan_no_longer_touches_the_previous_milestone():
    text = section(read("skills/plan/milestones.md"), "## `/plan M<n>`")
    assert "Status: active" in text
    assert not re.search(r"previous milestone to", text)
    closing = section(read("skills/plan/milestones.md"), "## Closing a milestone")
    assert "report PR" in closing and "sign-off" in closing
    assert "/plan M<n+1>" in closing and "Status: done" in closing


def test_the_milestone_diagram_has_done_arrive_with_the_owners_merge():
    text = section(read("docs/concepts/states.md"), "## Milestone")
    done = [line for line in text.splitlines() if "--> done" in line]
    assert len(done) == 1 and "milestone PR" in done[0] and "main" in done[0], done
    closing = [line for line in text.splitlines() if "--> closing" in line]
    assert len(closing) == 1 and "report PR" in closing[0], closing


def test_the_milestone_template_says_who_changes_its_status():
    comment = read("skills/plan/milestone-template.md").splitlines()[0]
    assert "report PR" in comment and "milestone PR" in comment


def test_autopilot_looks_before_it_closes_a_milestone():
    """F18: a stateless tick that finds every ticket done must not write the report and open the PR twice."""
    summary = section(read("skills/autopilot/SKILL.md"), "## Closing")
    assert "every ticket" in summary and "tick.md#closing-the-milestone" in summary
    closing = section(read("skills/autopilot/tick.md"), "## Closing the milestone")
    merged, report = closing.find("merged"), closing.find("/pitaya:report")
    assert 0 <= merged < report, "the check for a merged milestone PR must come before starting the report"
    for state in ("Status: done", "milestone PR", "report PR", "open"):
        assert state in closing, state


def test_between_milestones_has_one_plan_pr_job():
    text = section(read("skills/autopilot/SKILL.md"), "## Between milestones")
    assert "cuts the next milestone" in text
    assert "done" in text.split("start a fresh session")[0], "the trigger is M<n> done on main"
    assert "sets M<n>" not in text


# --- F04: a milestone's state is read from its own branch ---------------------------------------

READING_RULE = re.compile(r"on `milestone/M<n>`[^.|]*(when|if|while)[^.|]*exists[^.|]*`main`", re.S)


@pytest.mark.parametrize("rel,where", [
    ("docs/concepts/states.md", "Milestone phase"),
    ("skills/autopilot/tick.md", "The active milestone and its tickets"),
])
def test_the_state_tables_read_a_milestone_from_its_branch(rel, where):
    line = row(read(rel), where)
    assert READING_RULE.search(line), line


def test_autopilot_finds_the_active_milestone_on_its_branch():
    first = section(read("skills/autopilot/SKILL.md"), "## Before the first tick")
    step = next(line for line in first.splitlines() if line.startswith("2."))
    assert "under `docs/milestones/` on `main`" not in step
    assert "`milestone/M<n>`" in step and "tick.md" in step
    assert "Level 4" in step, "with no active milestone, Level 4 cuts the next one instead of stopping"


@pytest.mark.parametrize("rel", ["skills/help/SKILL.md", "skills/report/SKILL.md"])
def test_the_other_readers_use_the_same_rule(rel):
    """`/help` reports the state and `/report` reads the ticket list: both would miss a Level 4 cut on main."""
    text = read(rel)
    assert "docs/concepts/states.md" in text or "concepts/states.md" in text, rel
    assert "milestone/M<n>" in text, rel


def test_states_define_each_phase_by_where_status_is_read():
    text = section(read("docs/concepts/states.md"), "## Milestone")
    for phase in ("planned", "active", "closing", "done"):
        assert re.search(rf"\*\*{phase}\*\*", text), phase
    assert "Level 4" in text


# --- F04: the cut merges without a verdict, and every page says who merges a plan PR the same way ---

def test_autonomy_lists_the_level_4_setting():
    text = read("docs/concepts/autonomy.md")
    assert f"**{LEVEL_3}**" in text and f"**{LEVEL_4}**" in text
    template = read("skills/setup/harness-template.md")
    assert LEVEL_3 in template and LEVEL_4 in template
    assert LEVEL_4 in read("docs/guardrails/deep-verification.md")


def test_the_recipe_says_which_plan_prs_pass_without_a_verdict():
    text = read("docs/guardrails/agent-merge.md")
    assert "Plan and milestone PRs never pass" not in text
    para = re.search(r"^\*\*Plan PRs\.\*\*.*?(?=^\*\*|^## )", text, re.M | re.S).group(0)
    for word in ("report PR", "cut", "Autonomy", "default branch", "Owner"):
        assert word in para, word
    assert "never get a passing verdict" not in read("docs/concepts/states.md")


def test_autopilot_never_merges_other_plan_prs():
    never = section(read("skills/autopilot/SKILL.md"), "## Never")
    assert "never merge a plan PR anywhere" not in never
    assert "report PR" in never and "Level 4" in never
    cut = section(read("skills/autopilot/SKILL.md"), "## Between milestones")
    assert "verdict" in cut and "Autonomy" in cut


@pytest.mark.parametrize("rel", ["skills/plan/tickets.md", "docs/guardrails/README.md", "docs/concepts/layout.md",
                                 "docs/concepts/access.md", "docs/concepts/autonomy.md"])
def test_every_page_on_who_merges_a_plan_pr_knows_both_exceptions(rel):
    """Into main, only the Owner. Into a milestone branch: the report PR, and at Level 4 the cut."""
    text = read(rel)
    lines = [line for line in text.splitlines() if "plan PR" in line or "`plan/<slug>`" in line]
    joined = "\n".join(lines)
    assert "report PR" in joined, rel
    assert "Level 4" in joined, rel


def test_the_shared_step_and_the_check_allow_the_same_plan_files():
    """Two copies of one list: the ticket checks' shared step and the verdict check's own."""
    import importlib.util
    import sys
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("check_verdict", FILES / "agent-merge" / "check_verdict.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    shared = {re.search(r"grep -vE '([^']+)'", wf.read_text()).group(1)
              for wf in FILES.glob("*/*.yml") if "plan PR may change only" in wf.read_text()}
    assert len(shared) == 1, shared
    assert module.PLAN_FILES_RE.pattern == shared.pop()


def test_the_workflows_message_names_what_a_plan_pr_into_a_milestone_is_for():
    for wf in FILES.glob("*/*.yml"):
        text = wf.read_text()
        if "a plan PR targets" in text:
            line = next(line for line in text.splitlines() if "a plan PR targets" in line)
            assert "report" in line and "cut" in line, wf.name


# --- flows traced after the first draft: a stateless tick during "closing", and a milestone sent back ---

def test_a_tick_that_wakes_while_the_milestone_is_closing_finishes_closing_it():
    """A fresh session finds `Status: done` on the branch: that isn't "no active milestone", and at
    Level 4 it must not cut the next milestone before the sign-off."""
    first = section(read("skills/autopilot/SKILL.md"), "## Before the first tick")
    step = next(line for line in first.splitlines() if line.startswith("2."))
    closing, cut = step.find("closing"), step.find("next cut")
    assert 0 <= closing < cut, "the closing milestone must be handled before the next cut is considered"
    assert "tick.md#closing-the-milestone" in step
    between = section(read("skills/autopilot/SKILL.md"), "## Between milestones")
    assert "on `main`" in between.split("start a fresh session")[0]


def test_a_milestone_sent_back_gets_a_new_report():
    """With the milestone PR still open, "PR open: stop" alone would leave the first report standing."""
    closing = section(read("skills/autopilot/tick.md"), "## Closing the milestone")
    assert "sends" in closing and "since the report" in closing
    wait = next(line for line in closing.splitlines() if "milestone PR" in line and "isn't open" in line)
    assert "current" in wait and "sync PRs" in wait, wait
    report = read("skills/report/SKILL.md")
    assert "already open" in report, "a second report replaces the open milestone PR's description"


def test_plan_can_repair_a_milestone_signed_off_without_its_status():
    """Upgrading from 0.1.6, or a skipped report PR: the milestone PR is merged and main still says active."""
    text = section(read("skills/plan/milestones.md"), "## `/plan M<n>`")
    assert "milestone PR is merged" in text and "0.1.7" not in text
    tick = section(read("skills/autopilot/tick.md"), "## Closing the milestone")
    assert "skipped" in tick


def test_design_and_plan_say_who_approves_at_level_4():
    """F04: under a Level 4 autopilot nobody is there to approve the design or the cut before it merges."""
    for rel in ("skills/design/SKILL.md", "skills/plan/milestones.md"):
        text = read(rel)
        assert re.search(r"Level 4[^.]*sign-off", text), rel


def test_an_unmet_milestone_does_not_start_a_report_on_every_tick():
    """Every ticket done but an exit criterion unmet: `/report` opens no report PR, so the tick needs
    another sign that a report was already written, or it starts one each time it wakes."""
    report = section(read("skills/report/SKILL.md"), "## Deliver")
    assert "needs-owner" in report or "ask-owner" in report
    closing = section(read("skills/autopilot/tick.md"), "## Closing the milestone")
    unmet = closing.find("needs-owner")
    assert 0 <= unmet < closing.find("/pitaya:report"), "look for the escalation before starting another report"


# --- found by the consistency audit before the 0.1.7 PR ------------------------------------------

def test_the_never_list_does_not_forbid_the_merges_the_skill_asks_for():
    """A1: a sync PR, a report PR and a cut never have a PASS; "never merge without a PASS" forbade them."""
    never = section(read("skills/autopilot/SKILL.md"), "## Never")
    line = next(l for l in never.splitlines() if "no PASS" in l)
    assert "ticket PR" in line and "green `verdict`" in line, line
    point = next(l for l in read("docs/concepts/autonomy.md").splitlines() if l.startswith("7."))
    assert "ticket PR" in point and "green `verdict`" in point, point


def test_one_place_says_what_happens_with_no_milestone_to_run():
    """A2, B4: step 2 said "stop" below Level 4 while "Between milestones" said to start the design."""
    first = section(read("skills/autopilot/SKILL.md"), "## Before the first tick")
    step = next(l for l in first.splitlines() if l.startswith("2."))
    assert "below Level 4 stop" not in step
    cut = section(read("skills/autopilot/tick.md"), "## The next cut")
    assert cut.find("open") < cut.find("/pitaya:design"), "look for an open plan PR before starting another"
    assert "Level 4" in cut and "claim" in cut.lower()


def test_a_sent_back_milestone_is_built_not_closed():
    """B1: the branch still says done; with a ticket open the tick must build, not sit in "closing"."""
    first = section(read("skills/autopilot/SKILL.md"), "## Before the first tick")
    step = next(l for l in first.splitlines() if l.startswith("2."))
    assert re.search(r"closing[^.]*every ticket[^.]*done", step), step
    closing = section(read("skills/autopilot/tick.md"), "## Closing the milestone")
    assert re.search(r"only (when|while) every ticket", closing.split("1.")[0])
    assert "sent back" in read("skills/help/SKILL.md")


def test_autopilot_keeps_a_wake_up_while_it_waits_for_the_owner():
    """B2: cancelling the wake-up when every ticket is done left closing, and the next cut, to nobody."""
    stop = section(read("skills/autopilot/SKILL.md"), "## Stop")
    assert "every ticket of the milestone is done" not in stop
    assert re.search(r"keep[^.]*wake", stop), "the waits on the Owner's merge keep a wake-up"
    wake = read("skills/autopilot/wake.md")
    assert "report PR" in wake and "milestone PR" in wake


def test_one_session_opens_the_milestone_pr():
    """B3, B5: under autopilot the tick opens it; alone, `/report` does, and looks before it acts."""
    deliver = section(read("skills/report/SKILL.md"), "## Deliver")
    assert "/autopilot" in deliver and "look" in deliver.lower()
    closing = section(read("skills/autopilot/tick.md"), "## Closing the milestone")
    assert "description" in closing
    assert "/report M<n>" in read("skills/help/SKILL.md")


def test_new_work_for_a_level_4_milestone_goes_into_its_branch():
    """B6: at Level 4 main holds the roadmap's copy of the milestone file, so a plan PR on main conflicts in the sync."""
    for rel in ("skills/plan/milestones.md", "skills/autopilot/tick.md"):
        text = read(rel)
        assert re.search(r"At Level 4[^.]*plan PR into `milestone/M<n>`", text), rel


def test_a_milestone_that_falls_short_has_a_way_out():
    """B8: the Owner's answer on the issue is one of three things, and `/report` follows it."""
    deliver = section(read("skills/report/SKILL.md"), "## Deliver")
    for way in ("new tickets", "exit criteria", "as it is"):
        assert way in deliver, way


def test_unattended_design_and_plan_sessions_do_not_wait_for_the_owner():
    """A3, B7: autopilot starts them with nobody in the conversation, at Level 3 too."""
    for rel in ("skills/design/SKILL.md", "skills/plan/SKILL.md"):
        text = read(rel)
        assert "unattended" in text, rel
        assert "/autopilot" in text, rel


def test_the_repair_names_a_pr_that_can_carry_it():
    """A4: at Level 4 the cut goes into a milestone branch, where it may not touch another milestone's file."""
    text = section(read("skills/plan/milestones.md"), "## `/plan M<n>`")
    assert re.search(r"plan PR into `main`", text) and "Level 4" in text


def test_roles_and_the_recipes_agree_on_who_approves_a_cut():
    owner = row(read("docs/concepts/roles.md"), "**Owner**")
    assert "below Level 4" in owner
    assert "report PR" in read("docs/guardrails/protect-main.md")
    assert "like a sync PR" in row(read("docs/concepts/layout.md"), "`plan/<slug>`")


def test_recipes_that_state_their_version_state_the_current_one():
    import json
    version = json.loads(read(".claude-plugin/plugin.json"))["version"]
    stated = re.findall(r"this recipe is version (\d+\.\d+\.\d+)", read("docs/guardrails/progress-file.md"))
    assert stated == [version]


def test_the_checks_own_notes_list_every_rule_for_a_cut():
    text = " ".join((FILES / "agent-merge" / "check_verdict.py").read_text().split('"""')[1].split())
    for rule in ("deletes nothing", "no milestone file but its own", "any `plan/` branch"):
        assert rule in text, rule
    assert "Exit 0 when this head has a PASS and no FAIL" not in text
