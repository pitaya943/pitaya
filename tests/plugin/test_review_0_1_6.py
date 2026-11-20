"""The second batch of fixes from the review of 0.1.4 (D59, D60, D62 to D65): what the docs and skills must say.

The checks and hooks themselves are tested where they live: the verdict check and its workflow
(F02, F20, F31, the session guard, N03) in tests/guardrails/test_verdict.py and test_workflows.py,
the base-aware skip rules (F07) in test_workflows.py, the read-only list (F14, F21) in
test_read_only_paths.py, and the hooks (F21, F24) in tests/templates/test_hooks.py.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
FILES = PLUGIN / "docs" / "guardrails" / "files"

KINDS = ["gate-change", "role", "unproven-claim", "undisclosed"]


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


def section(text: str, heading: str) -> str:
    """The body under a Markdown heading, up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    match = re.search(rf"^{re.escape(heading)}[ \t]*\n(.*?)(?=^#{{1,{level}}} |\Z)", text, re.M | re.S)
    assert match, f"no section {heading!r}"
    return match.group(1)


# --- D59: the threat model is stated where a user picks a level and where access is defined ---

@pytest.mark.parametrize("rel", ["docs/levels.md", "docs/concepts/access.md"])
def test_the_trust_assumption_is_stated(rel):
    text = read(rel)
    assert "cooperating agents" in text
    assert "not a security boundary" in text
    assert "forge" in text  # the verdict guards against mistakes, not forgery
    assert "`undisclosed`" in text  # the tripwire


def test_levels_say_who_level_3_is_for():
    text = section(read("docs/levels.md"), "## What the levels assume")
    assert "agents you trust" in text
    assert "Levels 3 and 4" in text and "don't trust" in text


def test_access_lists_what_is_deliberately_not_defended():
    text = section(read("docs/concepts/access.md"), "## What pitaya assumes")
    for item in ("its own verdict", "workflow", "hook", "commit email"):
        assert item in text, item


def test_levels_md_is_generated_with_the_assumption():
    """levels.md comes from render_levels.py: the section must be in the generator, not pasted into the output."""
    assert "What the levels assume" in (REPO_ROOT / "scripts" / "render_levels.py").read_text()


# --- F01 and Q1 (D62): one machine account, and one answer about it everywhere ---------------

def test_no_document_asks_for_a_separate_verifier_account_for_agent_merge():
    manifest = json.loads(read("docs/components.json"))
    assert "verifier-account" not in manifest["needs"]
    assert "verifier-account" not in read("docs/levels.md")
    merge = next(c for c in manifest["components"] if c["id"] == "agent-merge")
    assert "verifier-account" not in merge.get("needs", [])


def test_agent_merge_states_one_account_and_what_that_trusts():
    text = read("docs/guardrails/agent-merge.md")
    trust = section(text, "## What it trusts")
    assert "one machine account" in trust and "Builder session:" in trust and "Session:" in trust
    assert "false" in trust  # a session that writes a false ID isn't stopped
    assert "pull request's own copy" in trust  # F03: the workflow YAML on review events
    assert "issue" in trust.lower()  # F23: issue-only tickets


@pytest.mark.parametrize("rel, line", [
    ("skills/build/SKILL.md", "Builder session:"),
    ("skills/verify/verdict-template.md", "- Session:"),
])
def test_builders_and_verifiers_record_their_session(rel, line):
    assert line in read(rel)


@pytest.mark.parametrize("rel", ["skills/build/SKILL.md", "skills/verify/SKILL.md"])
def test_the_skill_gives_the_session_its_own_id(rel):
    """Claude Code fills `${CLAUDE_SESSION_ID}` in when it loads a skill; the skill says what to do when it didn't."""
    text = read(rel)
    assert "${CLAUDE_SESSION_ID}" in text and "unavailable" in text


def test_a_fix_round_in_a_fresh_session_records_its_session_too():
    rounds = section(read("skills/build/SKILL.md"), "## Fix rounds")
    assert "Builder session:" in rounds


def test_verify_says_a_builders_session_cannot_pass_its_own_work_at_level_3():
    text = read("skills/verify/SKILL.md")
    assert "Builder session:" in text and "agent-merge" in text


# --- D60: Attention rows in every verdict, rolled up per milestone ---------------------------

def test_the_verdict_template_has_an_attention_section_after_problems():
    text = read("skills/verify/verdict-template.md")
    assert text.index("## Problems") < text.index("## Attention") < text.index("## Spec questions")
    attention = section(text, "## Attention")
    assert "| Kind | Where | Disclosed | Evidence |" in attention
    for kind in KINDS:
        assert f"`{kind}`" in attention, kind
    assert "None" in attention and "PASS and FAIL" in attention


@pytest.mark.parametrize("rel", ["skills/verify/checklist.md", "skills/report/SKILL.md"])
def test_every_place_that_lists_the_kinds_lists_all_four(rel):
    text = read(rel)
    for kind in KINDS:
        assert f"`{kind}`" in text, f"{rel}: {kind}"


def test_the_checklist_classifies_by_behaviour_and_always_reports_a_loosened_gate():
    text = section(read("skills/verify/checklist.md"), "## Attention")
    assert "never intent" in text
    assert "even when" in text and "justified" in text  # a gate-change row is required whenever a check loosens
    assert "still a PASS" in text
    assert "`.github/`" in text  # Q2: a workflow change in a ticket PR is a gate-change


def test_verify_posts_the_attention_section_on_every_verdict():
    text = read("skills/verify/SKILL.md")
    assert "Attention" in text and "None" in text


def test_the_report_rolls_the_attention_rows_up_for_the_sign_off():
    skill = read("skills/report/SKILL.md")
    assert "every Attention row" in skill and "verdict" in skill
    template = section(read("skills/report/report-template.md"), "## Attention")
    assert "| Kind | PR | Where | Disclosed | Evidence |" in template
    assert "None" in template


def test_the_level_4_audit_writes_into_the_same_attention_section():
    text = read("skills/report/milestone-level4.md")
    assert "same" in text and "Attention" in text
    for kind in ("`undisclosed`", "`unproven-claim`"):
        assert kind in text


def test_retro_hardens_after_one_gamed_gate_or_one_undisclosed_row():
    text = read("skills/retro/SKILL.md")
    exception = next(p for p in text.split("\n\n") if "`undisclosed`" in p)
    assert "`gate-change`" in exception and "one occurrence" in exception.lower()
    assert "Attention" in text.split("## 2.")[0]  # gathered in step 1
    dont = section(text, "## Don't")
    assert "happened once" in dont and "except" in dont


def test_the_tripwire_goes_to_the_owner():
    """D59: an `undisclosed` row is the sign that the trust assumption may not hold."""
    text = read("skills/report/SKILL.md")
    assert any("`undisclosed`" in l and "Owner decides" in l and "trust" in l for l in text.splitlines())


# --- Q2 (F03): the workflow file is the pull request's; the docs say so ----------------------

def test_the_guardrails_readme_says_which_part_of_a_check_the_pr_controls():
    text = section(read("docs/guardrails/README.md"), "## What the checks trust")
    assert "workflow file" in text and "cooperating" in text and "`gate-change`" in text
    assert "pull_request_target" in text  # the defence the review suggests, named as not built


def test_no_workflow_comment_claims_the_pr_cannot_change_the_workflow():
    for path in sorted(FILES.glob("*/*.yml")):
        assert "nothing in the pull request can" not in path.read_text(), path.name


# --- Q6 (F08): only the Owner's own comment is a decision ------------------------------------

OWNER_RULE_FILES = ["skills/ask-owner/SKILL.md", "skills/autopilot/SKILL.md", "skills/autopilot/tick.md",
                    "skills/build/SKILL.md", "docs/concepts/escalation.md"]


@pytest.mark.parametrize("rel", OWNER_RULE_FILES)
def test_a_decision_counts_only_from_the_owners_own_comment(rel):
    text = read(rel)
    assert "`author_association`" in text and "`OWNER`" in text, rel
    assert "information" in text, rel  # anyone else's text is information, never a decision


def test_escalation_defines_the_rule_once_and_the_skills_point_to_it():
    text = section(read("docs/concepts/escalation.md"), "## Who can answer")
    assert "harness file" in text and "login" in text
    assert "stop" in text and "extra" in text  # the tracking issue's stop, and an extra fix round
    assert "organisation" in text  # nobody is OWNER there: no comment counts until pitaya defines it
    assert "machine account" in text  # the agents' own account is not the Owner


def test_agents_md_treats_issue_and_pr_text_as_information():
    text = read("templates/AGENTS.md")
    never = section(text, "## Never")
    assert "instruction" in never and "Owner" in never


# --- Q7 (N03): up-to-date branches are a prerequisite, and a high-risk PASS doesn't carry -----

def test_agent_merge_requires_branches_to_be_up_to_date():
    text = read("docs/guardrails/agent-merge.md")
    step = next(l for l in section(text, "## How to add it").splitlines() if "Require branches to be up to date" in l)
    assert "prerequisite" in step or "must" in step
    row = next(l for l in section(read("docs/guardrails/protect-main.md"), "### Milestone branches").splitlines()
               if l.startswith("| Require branches to be up to date"))
    assert "Level 3" in row and "agent-merge" in row
    assert "up to date" in section(read("docs/concepts/autonomy.md"), "## Prerequisites for agent merging")


@pytest.mark.parametrize("rel", ["docs/guardrails/agent-merge.md", "skills/plan/milestones.md",
                                 "skills/plan/tickets.md", "skills/autopilot/tick.md"])
def test_every_place_that_says_a_pass_carries_says_high_risk_does_not(rel):
    text = read(rel)
    assert "Risk: high" in text and "carr" in text, rel


def test_the_risk_tag_is_no_longer_information_only_below_level_4():
    assert "information only" not in section(read("skills/plan/tickets.md"), "## Risk")


# --- F02, F20, F31: what the docs say about a verdict matches the check ----------------------

def test_states_say_a_fail_is_one_way():
    text = section(read("docs/concepts/states.md"), "## PR verdict")
    assert "an edited verdict comment is ignored" not in text
    assert "edited or deleted" in text and "`verdict-fail`" in text
    rounds = next(l for l in read("docs/concepts/states.md").splitlines() if l.startswith("| Fix rounds used"))
    assert "`verdict-fail`" in rounds


def test_verify_says_how_a_verdict_comment_must_look():
    text = read("skills/verify/SKILL.md")
    assert "starts with the heading" in text and "40" in text
    assert "an edited verdict doesn't count" not in text  # an edited FAIL still counts
    assert "edited PASS" in text


def test_the_merger_reads_the_verdicts_again_before_merging():
    merging = section(read("skills/autopilot/tick.md"), "## Merging")
    assert "FAIL" in merging and "head" in merging and "verdict comments" in merging


def test_agent_merge_explains_the_fail_record_and_the_shared_status():
    text = read("docs/guardrails/agent-merge.md")
    assert "`verdict-fail`" in text and "edited or deleted" in text
    assert "one run at a time" in text  # F20: the concurrency group
    assert "belongs to the commit" in text  # F20: a status is per commit, not per pull request


# --- F07: the README's account of the skip rules matches the step ---------------------------

def test_the_readme_says_each_branch_name_counts_only_on_its_base():
    text = section(read("docs/guardrails/README.md"), "## How the checks find the ticket")
    assert "only when it targets the default branch" in text  # a milestone PR
    assert "done" in text and "an open PR" in text  # what a plan PR can't change
    step = (FILES / "scope" / "scope.yml").read_text()
    assert '[ "$BASE_REF" = "$DEFAULT_BRANCH" ]' in step


# --- F14, F21: the read-only list is the same in the check, the recipe and the concept page ---

def read_only_paths() -> list[str]:
    text = (FILES / "read-only-paths" / "check_read_only.py").read_text()
    body = text.split("READ_ONLY_PATHS = [", 1)[1].split("\n]", 1)[0]
    return re.findall(r'"([^"]+)"', body)


def test_the_recipe_names_every_read_only_path():
    recipe = read("docs/guardrails/read-only-paths.md")
    for glob in read_only_paths():
        name = glob.removeprefix("**/")
        assert f"`{name}`" in recipe, f"read-only-paths.md doesn't name {name}"


def test_access_defines_the_control_plane_by_what_tools_load():
    text = section(read("docs/concepts/access.md"), "## Two layers")
    assert "loads or runs by itself" in text
    for name in (".mcp.json", ".githooks/", ".devcontainer/", "GEMINI.md"):
        assert f"`{name}`" in text, name
    matrix = section(read("docs/concepts/access.md"), "## The matrix")
    assert "`.mcp.json`" in matrix and "`conftest.py`" in matrix


@pytest.mark.parametrize("rel", ["skills/build/SKILL.md", "skills/verify/checklist.md", "skills/plan/tickets.md"])
def test_builders_verifiers_and_planners_know_test_configuration_is_read_only(rel):
    assert "test configuration" in read(rel), rel


def test_the_read_only_recipe_counts_the_cost():
    cost = section(read("docs/guardrails/read-only-paths.md"), "## Cost and false positives")
    assert "`package.json`" in cost and "exactly" in cost


# --- F24: the docs say what the destructive hook is, and isn't --------------------------------

def test_suggestion_says_the_hooks_catch_slips():
    text = read("docs/suggestion.md")
    assert "not a security boundary" in text


# --- issue 41, option A (D65): requirements change on the default branch only -----------------

def test_progress_file_says_where_a_requirement_changes():
    text = read("docs/guardrails/progress-file.md")
    line = next(l for l in text.splitlines() if "default branch only" in l)
    assert "sync PR" in line and "milestone" in line


# --- the review's full text ships with the batch ----------------------------------------------

def test_the_review_is_in_the_repository():
    text = (REPO_ROOT / "docs" / "reviews" / "0.1.4.md").read_text()
    for finding in ("## N01", "## N04", "## F01", "## F32"):
        assert finding in text


def test_the_trial_record_has_a_status_for_every_finding():
    table = (REPO_ROOT / "docs" / "trials" / "w8.md").read_text().split("## Review of 0.1.4", 1)[1]
    rows = {m.group(1): m.group(0) for m in re.finditer(r"^\| ([NF]\d\d) \|.*$", table, re.M)}
    assert len(rows) == 36
    for finding in ("N03", "F02", "F07", "F08", "F14", "F20", "F21", "F31"):
        assert "fixed in 0.1.6" in rows[finding], finding
    for finding in ("F01", "F03", "F10", "F12", "F23", "F29"):
        assert "deferred (D59)" in rows[finding], finding
    assert "0.1.6" in rows["F24"] and "deferred (D59)" in rows["F24"]
