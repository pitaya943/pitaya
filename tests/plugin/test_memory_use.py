"""Skills read and write the memory files at the right moments (docs/design.md, D30).

Readers: plan and build read the glossary, architecture and learnings before
they start. Writers: plan keeps the glossary and architecture current; retro
turns accepted proposals into learnings; build, verify and handoff only
propose, because ticket PRs can't change docs/agents/.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "skills"
GLOSSARY, LEARNINGS, ARCHITECTURE = "docs/agents/glossary.md", "docs/agents/learnings.md", "docs/agents/architecture.md"


def skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


@pytest.mark.parametrize("name", ["plan", "build"])
def test_planner_and_builder_read_all_memory(name):
    text = skill(name)
    for rel in (GLOSSARY, LEARNINGS, ARCHITECTURE):
        assert rel in text, (name, rel)


def test_retro_writes_learnings():
    assert LEARNINGS in skill("retro")


def test_plan_keeps_glossary_and_architecture_current():
    text = skill("plan")
    assert "update" in text.lower() and GLOSSARY in text and ARCHITECTURE in text


@pytest.mark.parametrize("name", ["build", "handoff"])
def test_builders_propose_learnings(name):
    assert "learning" in skill(name).lower()


def test_verdict_has_learning_proposals():
    assert "## Learning proposals" in (SKILLS / "verify" / "verdict-template.md").read_text()


def test_setup_drafts_architecture_and_glossary():
    text = skill("setup")
    assert ARCHITECTURE in text and GLOSSARY in text
