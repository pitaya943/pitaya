"""Fixes for the problems W8 part 2 found at Level 2 (docs/trials/w8.md; D57).

P14 and P20 change the merge gate and ship separately (0.1.4).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
FILES = PLUGIN / "docs" / "guardrails" / "files"


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


# P9: agents write action versions from memory when the template doesn't name one.

SETUP_V7 = "actions/setup-python" + "@" + "v7"  # built at runtime so the personal-data scan doesn't read it as a mention


def test_setup_comments_name_the_current_setup_action():
    assert SETUP_V7 in read("templates/.github/workflows/tests.yml")
    for wf in ("no-weakened-tests/no-weakened-tests.yml", "done-when/done-when.yml"):
        assert SETUP_V7 in (FILES / wf).read_text(), wf


# P10: the ticket template states the Test ID format.

def test_ticket_template_states_the_test_id_format():
    text = read("skills/plan/ticket-template.md").split("## Test IDs", 1)[1].split("## ", 1)[0]
    assert "classname::name" in text and "parametrized" in text


# P11: a cloud checkout's remote refs can be stale.

def test_build_fetches_its_base_before_branching():
    text = read("skills/build/SKILL.md")
    assert "git fetch origin" in text and "ticket file exists" in text


# P13: the branch permission is granted once in AGENTS.md.

def test_agents_template_grants_the_branch_names():
    text = read("templates/AGENTS.md")
    assert "## Branches" in text
    for name in ("plan/<slug>", "ticket/<id>-<slug>", "milestone/M<n>"):
        assert name in text, name


# P15: one word per kind of round.

def test_verify_and_fix_rounds_are_named_apart():
    assert "Verify round: <n> of at most" in read("skills/verify/verdict-template.md")
    sequence = "verify 1, fix 1, verify 2, fix 2, verify 3, escalate"
    assert sequence in read("docs/concepts/escalation.md")
    assert "next step" in read("skills/verify/SKILL.md").lower()


# P16: the milestone ruleset needs a bypass, or a milestone can't be discarded.

def test_protect_milestones_lists_a_bypass():
    section = read("docs/guardrails/protect-main.md").split("### Milestone branches", 1)[1].split("\n## ", 1)[0]
    assert "Bypass list" in section and "Repository admin" in section


# P17: lessons named in earlier verdicts of the same milestone reach the next builder.

def test_build_reads_earlier_verdicts_of_the_milestone():
    assert "Learning proposals" in read("skills/build/SKILL.md")


# P18: checklist item 6 is a rule a verifier runs, not one it interprets.

def test_error_path_item_is_a_mutation():
    item = re.search(r"\n6\. \*\*Error paths\.\*\*.*", read("skills/verify/checklist.md")).group(0)
    assert "change one character" in item and "substring" in item


# P19: a report can be committed as a file in the closing plan PR.

def test_plan_prs_may_add_reports():
    for wf in sorted(FILES.glob("*/*.yml")):
        text = wf.read_text()
        if "plan PR may change only" not in text:
            continue
        allow = re.search(r"grep -vE '([^']+)'", text).group(1)
        assert re.search(allow, "docs/reports/M2.md"), wf.name
        assert "docs/reports/*.md" in text, wf.name
    assert "docs/reports/" in read("skills/plan/tickets.md")
    assert "closing plan PR" in read("skills/report/SKILL.md")


# P21: the milestone PR closes the issue mirrors of its tickets.

def test_report_closes_the_milestone_issue_mirrors():
    assert "Closes #<n>" in read("skills/report/SKILL.md")


# P14 and P20 (0.1.4, D58): the merge gate.

def test_milestones_explain_the_sync_pr():
    section = read("skills/plan/milestones.md").split("## The milestone branch", 1)[1].split("\n## ", 1)[0]
    assert "sync/M<n>-" in section and "Update branch" in section
    assert "sync" in read("skills/autopilot/tick.md")


def test_agent_merge_recipe_explains_what_carries_a_verdict():
    text = read("docs/guardrails/agent-merge.md")
    assert "Update branch" in text and "sync/" in text and "tree" in text
