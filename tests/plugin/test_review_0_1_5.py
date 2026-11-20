"""The first batch of fixes from the review of 0.1.4 (D59 to D61): what the docs and templates must now say.

The checks themselves are tested under tests/guardrails/: the history proof (N01) in
test_verdict.py and test_workflows.py, sync PRs in commit-author and progress-file (N02),
and the unset MACHINE_ACCOUNT (F13).
"""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
FILES = PLUGIN / "docs" / "guardrails" / "files"


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


# --- N04: every branch class the checks recognise is documented and granted ---------

def branch_prefixes() -> set[str]:
    """Branch prefixes the shared "Find the ticket" step treats specially, plus ticket/."""
    text = (FILES / "scope" / "scope.yml").read_text()
    found = set(re.findall(r'\$\{HEAD_REF#([a-z]+)/\}', text))
    assert {"milestone", "plan", "sync"} <= found
    return found | {"ticket"}


@pytest.mark.parametrize("rel", ["templates/AGENTS.md", "docs/concepts/layout.md", "docs/concepts/states.md",
                                 "docs/guardrails/README.md", "skills/help/SKILL.md"])
def test_every_branch_prefix_the_checks_recognise_is_documented(rel):
    text = read(rel)
    missing = sorted(p for p in branch_prefixes() if f"`{p}/" not in text)
    assert not missing, f"{rel} doesn't mention: {missing}"


def test_agents_md_grants_the_sync_branch():
    branches = read("templates/AGENTS.md").split("## Branches", 1)[1].split("\n## ", 1)[0]
    assert "`sync/<slug>`" in branches


# --- F22: one answer on where ticket PRs go and who merges main ---------------------

def test_states_send_ticket_prs_to_the_milestone_branch_at_every_level():
    text = read("docs/concepts/states.md")
    assert "or main below Level 3" not in text
    assert "PR opened into milestone/M<n>" in text


def test_roles_agree_that_only_the_owner_merges_main():
    text = read("docs/concepts/roles.md")
    assert "unless the autonomy setting says otherwise" not in text
    assert "Whatever it says, only the Owner merges `main`" in read("docs/concepts/autonomy.md")


# --- F06: below Level 3 the milestone branch needs the Owner's approval -------------

def test_milestone_ruleset_requires_an_approval_below_level_3():
    text = read("docs/guardrails/protect-main.md").split("### Milestone branches", 1)[1]
    row = next(line for line in text.splitlines() if line.startswith("| Require a pull request before merging"))
    assert "Required approvals: 1" in row and "below Level 3" in row
    assert "Required approvals: 0" in row and "verdict" in row


def test_agent_merge_drops_the_approval_in_the_step_that_requires_the_verdict():
    text = read("docs/guardrails/agent-merge.md")
    step = next(line for line in text.splitlines() if "require the `verdict` status" in line)
    assert "Required approvals" in step and "0" in step and "same" in step


def test_setup_hands_over_the_milestone_approval():
    assert "1 approval below Level 3" in read("skills/setup/SKILL.md")


# --- F05, what was left: creating the milestone branch under its ruleset ------------

def test_protect_main_says_what_creating_a_branch_needs_and_proves_it():
    text = read("docs/guardrails/protect-main.md")
    assert "Do not require status checks on creation" in text
    proof = text.split("## How to prove it works", 1)[1].split("\n## ", 1)[0]
    assert "milestone/" in proof and "create" in proof.lower()


# --- F09: the allow rules can't write files, read denied ones or run commands -------

DANGEROUS = [
    "git diff --output=.claude/hooks/no_push_main.py",
    "git show HEAD --output=AGENTS.md",
    "git log -p --output=x",
    "git diff --no-index /dev/null .env",
    "git fetch --upload-pack=touch x origin",
    "git fetch origin --upload-pack 'sh -c id'",
    "git diff --ext-diff HEAD~1",
]
EVERYDAY = [
    "git status --short", "git diff --stat main...HEAD", "git diff HEAD -- src/app.py", "git log --oneline -20",
    "git show HEAD:docs/tickets/T-001.md", "git fetch origin milestone/M1", "git fetch origin",
]


def bash_rules(settings: dict, kind: str) -> list[str]:
    return [r[5:-1] for r in settings["permissions"][kind] if r.startswith("Bash(") and r.endswith(")")]


def matches(command: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(command, p) for p in patterns)


@pytest.mark.parametrize("path", [PLUGIN / "templates/.claude/settings.json", REPO_ROOT / ".claude/settings.json"],
                         ids=["template", "this repository"])
def test_git_allow_rules_have_deny_rules_for_their_dangerous_options(path):
    settings = json.loads(path.read_text())
    allow, deny = bash_rules(settings, "allow"), bash_rules(settings, "deny")
    for command in DANGEROUS:
        assert matches(command, deny), f"nothing denies: {command}"
    for command in EVERYDAY:
        assert matches(command, allow) and not matches(command, deny), command


def test_suggestion_says_the_allow_rules_are_narrowed():
    assert "--output" in read("docs/suggestion.md")


# --- found by the consistency audit before the PR (decision log) --------------------

def test_every_place_that_names_the_branches_to_allow_names_all_of_them():
    """autopilot asks for them when AGENTS.md has no grant; the README tells cloud users what to allow."""
    ask = next(line for line in read("skills/autopilot/SKILL.md").splitlines() if "ask the user once to allow" in line)
    cloud = read("README.md").split("## Cloud sessions", 1)[1].split("\n## ", 1)[0]
    for name, text in (("autopilot", ask), ("README", cloud)):
        missing = sorted(p for p in branch_prefixes() if f"`{p}/" not in text)
        assert not missing, f"{name} doesn't name: {missing}"


def test_autonomy_says_which_ruleset_drops_its_approval():
    line = next(l for l in read("docs/concepts/autonomy.md").splitlines() if "to 0 only together" in l)
    assert "`milestone/*`" in line


def test_agents_merge_sync_prs_where_they_merge_ticket_prs():
    assert "ticket and sync PRs" in read("docs/concepts/autonomy.md")
    assert "sync PR" in read("docs/concepts/roles.md")


@pytest.mark.parametrize("rel", ["docs/guardrails/commit-author.md", "docs/guardrails/progress-file.md"])
def test_recipes_say_an_unset_machine_account_fails_every_pr(rel):
    assert "fails on every pull request" in read(rel)


def test_every_description_of_the_permissions_mentions_the_git_deny_rules():
    manifest = json.loads(read("docs/components.json"))
    guards = json.dumps(manifest)
    assert "--output" in guards
    assert "--output" in read("docs/levels.md") and "--output" in read("docs/concepts/access.md")
