"""The architecture pages (D49): who may read and write what, where state lives, the repo layout,
options in the decision log, ADRs for big decisions, and a read-only /help.

They answer questions every new user and agent asks, so these tests keep them in step with the
skills and templates they describe: a path a skill names must appear in the access matrix, every
template must appear in the layout, and every state diagram must say where its state is stored.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
CONCEPTS = PLUGIN / "docs" / "concepts"
SKILLS = PLUGIN / "skills"
TEMPLATES = PLUGIN / "templates"

# Paths in the skills that point at the plugin's own docs, not at the user's repository.
PLUGIN_DOCS = ("docs/levels.md", "docs/suggestion.md", "docs/guardrails/", "docs/concepts/")
PROJECT_PATH = re.compile(r"`((?:docs|\.claude|\.github)/[^` ]*|AGENTS\.md|CLAUDE\.md)`")


def read(path: Path) -> str:
    return path.read_text()


def matrix_areas() -> list[str]:
    """The paths in the first column of the access matrix."""
    areas = []
    for line in read(CONCEPTS / "access.md").splitlines():
        if line.startswith("| `"):
            first = line.split("|")[1]
            areas += re.findall(r"`([^`]+)`", first)
    return areas


def skill_paths() -> set[str]:
    found = set()
    for md in SKILLS.rglob("*.md"):
        for path in PROJECT_PATH.findall(read(md)):
            if not path.startswith(PLUGIN_DOCS):
                found.add(path)
    return found


# --- access.md -----------------------------------------------------------------

def test_access_matrix_names_every_role():
    text = read(CONCEPTS / "access.md")
    for role in ("Owner", "Chief", "Builder", "Verifier", "Adversary"):
        assert role in text, role


@pytest.mark.parametrize("path", sorted(skill_paths()))
def test_every_path_a_skill_names_is_in_the_access_matrix(path):
    areas = matrix_areas()
    covered = any(path == a or (a.endswith("/") and path.startswith(a)) for a in areas)
    assert covered, f"{path} is named by a skill but has no row in concepts/access.md"


def test_access_page_separates_the_layers_and_lists_crossings():
    text = read(CONCEPTS / "access.md")
    assert "control plane" in text and "data plane" in text
    assert "## Crossing the line" in text
    # The page must be honest about what is enforced and what is only written down.
    assert "enforced" in text.lower() and "prose" in text.lower()


# --- states.md -----------------------------------------------------------------

def test_states_page_draws_each_machine_and_says_where_state_lives():
    text = read(CONCEPTS / "states.md")
    for machine in ("## Ticket", "## Milestone", "## Autopilot run"):
        assert machine in text, machine
    assert text.count("stateDiagram-v2") >= 3
    assert "## Where state lives" in text
    for store in ("Status:", "ticket/<id>-", "milestone/M<n>", "tracking issue", "needs-owner"):
        assert store in text, store


# --- layout.md -----------------------------------------------------------------

def test_layout_names_every_copied_template():
    text = read(CONCEPTS / "layout.md")
    for p in TEMPLATES.rglob("*"):
        rel = p.relative_to(TEMPLATES).as_posix()
        if p.is_file() and not rel.endswith("README.md"):
            name = rel.rsplit("/", 1)[-1]
            assert name in text, rel


def test_layout_names_the_branches_and_both_layers():
    text = read(CONCEPTS / "layout.md")
    for branch in ("main", "milestone/M<n>", "ticket/<id>-<slug>", "plan/<slug>"):
        assert branch in text, branch
    assert "control plane" in text and "data plane" in text


# --- options and ADRs ------------------------------------------------------------

def test_decision_log_asks_for_options_only_when_there_were_real_ones():
    text = read(SKILLS / "build" / "pr-template.md")
    assert "Options" in text and "two or more" in text


def test_adr_template_has_the_standard_sections():
    text = read(SKILLS / "plan" / "adr-template.md")
    for section in ("## Context", "## Options", "## Decision", "## Consequences", "Status:"):
        assert section in text, section


def test_big_decisions_get_an_adr_linked_from_the_decision_log():
    assert "docs/adr/" in read(TEMPLATES / "docs" / "decisions.md")
    for skill in ("plan/SKILL.md", "ask-owner/SKILL.md"):
        assert "adr-template.md" in read(SKILLS / skill) or "docs/adr/" in read(SKILLS / skill), skill


def test_plan_prs_may_add_adrs():
    assert "docs/adr/" in read(SKILLS / "plan" / "tickets.md")


# --- /help -----------------------------------------------------------------------

def test_help_is_read_only_and_uses_the_state_table():
    text = read(SKILLS / "help" / "SKILL.md")
    assert "read-only" in text.lower() or "read only" in text.lower()
    assert "states.md" in text
    assert "Never" in text and "write" in text.lower()


WORKFLOWS = sorted((PLUGIN / "docs" / "guardrails" / "files").glob("*/*.yml"))


@pytest.mark.parametrize("workflow", [w for w in WORKFLOWS if "plan PR may change only" in w.read_text()],
                         ids=lambda w: w.name)
def test_plan_pr_allowlist_includes_adrs(workflow):
    text = workflow.read_text()
    allow = re.search(r"grep -vE '([^']+)'", text).group(1)  # the plan PR allowlist, as the step runs it
    assert re.search(allow, "docs/adr/0001-pick-a-queue.md")
    assert not re.search(allow, "docs/adr/drafts/0001.md") and not re.search(allow, "src/adr.md")
    assert "docs/adr/*.md" in text  # and the failure message says so


def test_adrs_are_read_only_in_ticket_prs():
    script = PLUGIN / "docs" / "guardrails" / "files" / "read-only-paths" / "check_read_only.py"
    assert '"docs/adr/**"' in script.read_text()
    assert "docs/adr/**" in read(PLUGIN / "docs" / "guardrails" / "read-only-paths.md")


# --- each role's skills stay inside its column (gaps found after D49) -------------------------

ROLE_OF = {
    "plan": "Chief", "design": "Chief", "report": "Chief", "retro": "Chief", "autopilot": "Chief",
    "build": "Builder", "verify": "Verifier", "setup": "Owner",
}
NEGATION = re.compile(r"\b(never|don't|do not|must not|nor)\b", re.I)


def matrix() -> dict[str, dict[str, str]]:
    """Each path in the access matrix mapped to its cell per role."""
    rows, header = {}, None
    for line in read(CONCEPTS / "access.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == "Path":
            header = cells
        elif header and line.startswith("| `"):
            for area in re.findall(r"`([^`]+)`", cells[0]):
                rows[area] = dict(zip(header, cells))
    return rows


def row_for(path: str, rows: dict) -> dict | None:
    """The most specific matrix row that covers `path`."""
    hits = [a for a in rows if path == a or (a.endswith("/") and path.startswith(a))]
    return rows[max(hits, key=len)] if hits else None


def role_paths():
    for skill, role in ROLE_OF.items():
        for md in (SKILLS / skill).rglob("*.md"):
            text = read(md)
            for match in PROJECT_PATH.finditer(text):
                path = match.group(1)
                before = text[max(0, match.start() - 60):match.start()].rsplit(".", 1)[-1]
                if path.startswith(PLUGIN_DOCS) or NEGATION.search(before):
                    continue  # plugin docs, or a path named only to forbid it ("never edit `x`")
                yield pytest.param(role, path, id=f"{skill}:{path}")


@pytest.mark.parametrize("role,path", sorted(set(role_paths()), key=lambda p: p.id))
def test_a_role_only_uses_paths_its_column_allows(role, path):
    row = row_for(path, matrix())
    assert row is not None, path
    assert row[role][:1] in ("R", "W"), f"{role} uses {path}, but access.md marks it {row[role]!r}"


def test_verifier_skips_handoff_notes_even_when_they_are_on_the_branch():
    checklist = read(SKILLS / "verify" / "checklist.md")
    assert "docs/handoff/" in checklist
    handoff = read(SKILLS / "handoff" / "SKILL.md")
    assert "last resort" in handoff and "verifier" in handoff.lower()
    access = read(CONCEPTS / "access.md")
    assert "docs/handoff/" in access.split("## Crossing the line")[0].split("Isolation")[1]


def test_autopilot_rebuilds_state_from_the_states_page():
    assert "states.md" in read(SKILLS / "autopilot" / "tick.md")
