"""Link checks for every Markdown file in the repo.

Relative links must resolve and Markdown anchors must match a heading, using
GitHub's slug rules (lowercase, punctuation dropped, spaces to '-').
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def all_docs() -> list[Path]:
    skip = {".git", ".pytest_cache", "node_modules"}
    return sorted(p for p in REPO_ROOT.rglob("*.md") if not skip & set(p.relative_to(REPO_ROOT).parts))


DOCS = all_docs()


def github_slug(heading: str) -> str:
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def broken_links(doc: Path) -> list[str]:
    text = FENCE_RE.sub("", doc.read_text(encoding="utf-8"))
    problems = []
    for target in LINK_RE.findall(text):
        if re.match(r"[a-z]+:", target):
            continue  # external URL
        path_part, _, anchor = target.partition("#")
        dest = (doc.parent / path_part).resolve() if path_part else doc
        if not dest.exists():
            problems.append(f"{target}: target does not exist")
            continue
        if anchor and dest.suffix == ".md":
            slugs = {github_slug(h) for h in HEADING_RE.findall(dest.read_text(encoding="utf-8"))}
            if anchor not in slugs:
                problems.append(f"{target}: no heading with anchor #{anchor}")
    return problems


@pytest.mark.parametrize("doc", DOCS, ids=[str(p.relative_to(REPO_ROOT)) for p in DOCS])
def test_relative_links_resolve(doc):
    assert broken_links(doc) == []


def test_link_check_catches_bad_targets(tmp_path):
    (tmp_path / "other.md").write_text("# Real heading\n")
    doc = tmp_path / "doc.md"
    doc.write_text("[a](missing.md) [b](other.md#wrong) [c](other.md#real-heading) [d](https://example.com)\n")
    assert broken_links(doc) == ["missing.md: target does not exist", "other.md#wrong: no heading with anchor #wrong"]


def test_changelog_has_a_dated_section_for_the_plugin_version():
    """A release needs its notes: the CHANGELOG names the shipped version, with a date, not "Unreleased"."""
    import json
    import re
    version = json.loads((REPO_ROOT / "plugin" / ".claude-plugin" / "plugin.json").read_text())["version"]
    text = (REPO_ROOT / "plugin" / "CHANGELOG.md").read_text()
    assert re.search(rf"^## {re.escape(version)} \(\d{{4}}-\d{{2}}-\d{{2}}\)$", text, re.M), version
    assert "Unreleased" not in text


def test_the_design_status_line_names_the_plugin_version_and_the_newest_decision():
    """The verdict on 0.1.9: the design's `Status:` line stayed at 0.1.8 through a release, and no test saw it."""
    import json
    import re
    version = json.loads((REPO_ROOT / "plugin" / ".claude-plugin" / "plugin.json").read_text())["version"]
    status = next(l for l in (REPO_ROOT / "docs" / "design.md").read_text().splitlines() if l.startswith("- Status:"))
    assert status.startswith(f"- Status: {version}, "), status
    major, minor, patch = (int(part) for part in version.split("."))
    if patch:  # the releases before this one, as a range that ends just below it
        assert f"to {major}.{minor}.{patch - 1} were released" in status, status
    rows = re.findall(r"(?m)^\| D(\d+) \|", (REPO_ROOT / "docs" / "decisions.md").read_text())
    assert rows, "docs/decisions.md has no D-rows"
    assert f"–D{max(int(n) for n in rows)} in" in status, status
