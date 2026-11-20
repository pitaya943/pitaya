"""CODEOWNERS is optional hardening for repositories with more than one agent account (D44).

With one machine account, GitHub's rule that authors can't approve their own
pull requests already keeps the Owner's approval on `main`. With several agent
accounts, one could approve another's work, so the multi-account recipe adds
CODEOWNERS and code-owner review.
"""

from __future__ import annotations

import json

from helpers import FILES, PLUGIN_ROOT

GUARDRAILS = PLUGIN_ROOT / "docs" / "guardrails"


def owned(path) -> dict[str, list[str]]:
    rules = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            pattern, *owners = line.split()
            rules[pattern] = owners
    return rules


def test_multi_account_recipe_ships_both_codeowners_files():
    assert owned(FILES / "multi-account" / "CODEOWNERS") == {"*": ["@example-owner"]}
    narrow = owned(FILES / "multi-account" / "CODEOWNERS-agent-merge")
    for pattern in ("/.github/", "/.claude/", "/AGENTS.md", "/CLAUDE.md", "/docs/agents/",
                    "/docs/tickets/", "/docs/milestones/", "/docs/decisions.md"):
        assert narrow.get(pattern) == ["@example-owner"], pattern
    text = (GUARDRAILS / "multi-account.md").read_text()
    assert "Require review from Code Owners" in text


def test_protect_main_needs_no_codeowners_with_one_agent_account():
    text = (GUARDRAILS / "protect-main.md").read_text()
    assert "Require review from Code Owners" not in text
    assert "multi-account" in text
    assert not (FILES / "protect-main").exists()


def test_multi_account_is_an_optional_component():
    comps = {c["id"]: c for c in json.loads((PLUGIN_ROOT / "docs" / "components.json").read_text())["components"]}
    assert comps["multi-account"]["kind"] == "recipe"
    assert "machine-account" in comps["multi-account"]["requires"]
