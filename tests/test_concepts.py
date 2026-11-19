"""The concept pages exist and the index links each one (docs/design.md, section 4)."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
CONCEPTS = PLUGIN_ROOT / "docs" / "concepts"
PAGES = ("roles.md", "autonomy.md", "escalation.md")


def test_concept_pages_exist_and_are_indexed():
    index = (CONCEPTS / "README.md").read_text()
    for page in PAGES:
        assert (CONCEPTS / page).is_file(), page
        assert f"({page})" in index, page


def test_roles_page_maps_every_role_to_skills():
    text = (CONCEPTS / "roles.md").read_text()
    for role in ("Owner", "Chief", "Builder", "Verifier"):
        assert f"**{role}**" in text, role
