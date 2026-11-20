"""plugin/docs/components.json: every part of the harness, its level and its dependencies (D33).

The manifest is the one source for what each level includes and what each
part needs first. These tests keep it honest:

* it covers every skill, every copied template and every recipe exactly once;
* ids are unique, references resolve, there are no cycles, and a component
  never requires one from a higher level (so every level preset is closed);
* dependencies that can be read off the shipped files are declared: a recipe
  with a workflow needs protect-main (its check must be required), a workflow
  that reads MACHINE_ACCOUNT needs machine-account, one that finds the ticket
  needs tickets, and so on. The manifest may declare more, never less.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
MANIFEST = PLUGIN / "docs" / "components.json"
GUARDRAILS = PLUGIN / "docs" / "guardrails"
KINDS = {"skill", "template", "filled", "recipe"}


def manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def components() -> dict[str, dict]:
    return {c["id"]: c for c in manifest()["components"]}


def recipes() -> list[str]:
    return sorted(p.stem for p in GUARDRAILS.glob("*.md") if p.name != "README.md")


# --- shape ---------------------------------------------------------------------

def test_version_matches_the_plugin():
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert manifest()["version"] == plugin["version"]


def test_ids_are_unique():
    ids = [c["id"] for c in manifest()["components"]]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("cid", sorted(components()))
def test_component_shape(cid):
    c = components()[cid]
    assert c["kind"] in KINDS
    assert c["level"] in (0, 1, 2, 3, 4)
    assert isinstance(c["summary"], str) and c["summary"] and len(c["summary"]) <= 120
    assert (PLUGIN / c["doc"]).is_file(), c["doc"]
    for key in ("requires", "recommends", "needs", "files"):
        assert isinstance(c.get(key, []), list), key


def test_needs_are_defined():
    defined = manifest()["needs"]
    for c in components().values():
        for need in c.get("needs", []):
            assert need in defined, (c["id"], need)


def test_references_resolve_and_are_not_self():
    known = components()
    for c in known.values():
        for key in ("requires", "recommends"):
            for ref in c.get(key, []):
                assert ref in known, (c["id"], key, ref)
                assert ref != c["id"]


def test_no_cycles():
    known = components()
    state: dict[str, int] = {}

    def visit(cid: str, path: list[str]) -> None:
        assert state.get(cid) != 1, " -> ".join(path + [cid])
        if state.get(cid) == 2:
            return
        state[cid] = 1
        for ref in known[cid].get("requires", []):
            visit(ref, path + [cid])
        state[cid] = 2

    for cid in known:
        visit(cid, [])


def test_requires_never_point_to_a_higher_level():
    known = components()
    for c in known.values():
        for ref in c.get("requires", []):
            assert known[ref]["level"] <= c["level"], (c["id"], ref)


# --- coverage --------------------------------------------------------------------

def test_every_skill_is_one_component():
    skills = {p.parent.name for p in (PLUGIN / "skills").glob("*/SKILL.md")}
    # Skill ids carry a "skill:" prefix: the evidence skill and the evidence recipe are different parts.
    listed = {c["id"]: c for c in components().values() if c["kind"] == "skill"}
    assert set(listed) == {f"skill:{s}" for s in skills}
    for cid, c in listed.items():
        assert c["doc"] == f"skills/{cid.removeprefix('skill:')}/SKILL.md"


def test_every_recipe_is_one_component():
    listed = {c["id"]: c for c in components().values() if c["kind"] == "recipe"}
    assert sorted(listed) == recipes()
    for name, c in listed.items():
        assert c["doc"] == f"docs/guardrails/{name}.md"


def test_every_copied_template_belongs_to_one_component():
    root = PLUGIN / "templates"
    shipped = sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                     if p.is_file() and p.name != "README.md")
    owned = [f for c in components().values() if c["kind"] == "template" for f in c["files"]]
    assert sorted(owned) == shipped


def test_harness_file_is_filled_in_from_its_template():
    c = components()["harness-file"]
    assert c["kind"] == "filled"
    assert c["files"] == ["docs/agents/harness.md"]
    assert c["doc"] == "skills/setup/harness-template.md"


def test_recipe_levels_match_their_header():
    for name in recipes():
        header = (GUARDRAILS / f"{name}.md").read_text().split("\n", 3)[2]
        assert header.startswith(f"Level: {components()[name]['level']}."), name


# --- dependencies derived from the shipped files ---------------------------------

def workflows(name: str) -> str:
    return "\n".join(p.read_text() for p in sorted((GUARDRAILS / "files" / name).glob("*.yml")))


def scripts(name: str) -> str:
    return "\n".join(p.read_text() for p in sorted((GUARDRAILS / "files" / name).glob("*.py")))


def derived(name: str) -> tuple[set[str], set[str]]:
    """(requires, needs) that the recipe's own files imply."""
    requires: set[str] = set()
    needs: set[str] = set()
    yml, py = workflows(name), scripts(name)
    text = (GUARDRAILS / f"{name}.md").read_text()
    if yml:
        requires.add("protect-main")  # its check only blocks a merge once it's required
    if "vars.MACHINE_ACCOUNT" in yml or "vars.OWNER_ACCOUNTS" in yml:
        requires.add("machine-account")  # its recipe sets both variables
    if "find_ticket" in yml:
        needs.add("tickets")
    if "vars.VERIFIER_ACCOUNTS" in yml:
        needs.add("verifier-account")
    if re.search(r"junit", text, re.IGNORECASE):
        needs.add("junit-xml")
    # A ticket section read without an "or" fallback is mandatory for every ticket.
    for line in py.splitlines():
        m = re.search(r'ticket_section\(.*"([^"]+)"\)(\s+or\b)?', line)
        if m and not m.group(2) and not line.lstrip().startswith("def "):
            needs.add("ticket-" + m.group(1).lower().replace(" ", "-"))
    return requires, needs


@pytest.mark.parametrize("name", recipes())
def test_declares_what_its_files_imply(name):
    c = components()[name]
    requires, needs = derived(name)
    assert requires <= set(c.get("requires", [])), requires - set(c.get("requires", []))
    assert needs <= set(c.get("needs", [])), needs - set(c.get("needs", []))


@pytest.mark.parametrize("name", recipes())
def test_recipes_it_names_as_prerequisites_are_declared(name):
    text = (GUARDRAILS / f"{name}.md").read_text()
    when = text.split("## When it's worth adding", 1)[1].split("\n## ", 1)[0]
    named = set(re.findall(r"\]\(([-\w]+)\.md\)", when)) | {
        r for r in recipes() if re.search(rf"\b{re.escape(r)}\b", when)}
    named.discard(name)
    c = components()[name]
    declared = set(c.get("requires", [])) | set(c.get("recommends", []))
    # A recipe may also name one it is needed *before*; that one declares the link instead.
    dependents = {d for d, other in components().items() if name in other.get("requires", [])}
    assert named <= declared | dependents, named - declared - dependents


def test_agent_merge_requires_the_checks_its_prerequisites_name():
    c = components()["agent-merge"]
    assert {"scope", "read-only-paths", "no-weakened-tests", "done-when", "skill:verify"} <= set(c["requires"])


def test_skill_levels_match_suggestion_md():
    """A skill with its own row in suggestion.md sits in that row's level section."""
    text = (PLUGIN / "docs" / "suggestion.md").read_text()
    marks = list(re.finditer(r"^## Level (\d)\b", text, re.MULTILINE))
    found = {}
    for i, m in enumerate(marks):
        body = text[m.start(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        for name in re.findall(r"^\| \*\*`([-\w]+)` skill\*\*", body, re.MULTILINE):
            found[f"skill:{name}"] = int(m.group(1))
    assert found, "no skill rows found in suggestion.md"
    assert {cid: components()[cid]["level"] for cid in found} == found
