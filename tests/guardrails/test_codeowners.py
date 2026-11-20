"""CODEOWNERS ties the required approval to the Owner (D41).

Level 1-2: every path needs a code owner's review, so a second agent account's
approval doesn't count. Level 3 with agent-merge: only rule, plan and sensitive
paths do, so ticket PRs merge on the verdict while plans and rules still need
the Owner.
"""

from __future__ import annotations

from helpers import FILES, PLUGIN_ROOT

GUARDRAILS = PLUGIN_ROOT / "docs" / "guardrails"


def owned(path) -> dict[str, list[str]]:
    rules = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            pattern, *owners = line.split()
            rules[pattern] = owners
    return rules


def test_level_1_owns_everything():
    rules = owned(FILES / "protect-main" / "CODEOWNERS")
    assert rules == {"*": ["@example-owner"]}


def test_agent_merge_owns_rules_plans_and_sensitive_paths():
    rules = owned(FILES / "agent-merge" / "CODEOWNERS")
    for pattern in ("/.github/", "/.claude/", "/AGENTS.md", "/CLAUDE.md", "/docs/agents/",
                    "/docs/tickets/", "/docs/milestones/", "/docs/decisions.md"):
        assert rules.get(pattern) == ["@example-owner"], pattern
    assert "*" not in rules


def test_recipes_require_code_owner_review():
    for recipe in ("protect-main", "agent-merge"):
        text = (GUARDRAILS / f"{recipe}.md").read_text()
        assert "Require review from Code Owners" in text, recipe
        assert f"files/{recipe}/CODEOWNERS" in text, recipe
