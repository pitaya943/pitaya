"""Cloud sessions load no plugins, only what the repository commits (D51).

`vendor_plugin.py` copies the plugin's skills, docs and templates into the
project's `.claude/`, so `.claude/` takes the place of the plugin root: every
relative link in the skills still resolves, and `/setup`'s installer still
finds its templates. Like the template installer, it never overwrites a file
the project changed; it upgrades only copies it can prove are its own,
recorded with a hash in `.claude/pitaya.json`.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
SCRIPT = PLUGIN / "skills" / "setup" / "scripts" / "vendor_plugin.py"
VERSION = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]
LINK = re.compile(r"\]\(([^)#:]+\.md)(?:#[^)]*)?\)")


def vendor(target: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--target", str(target), *args],
                          capture_output=True, text=True, timeout=60)


def lines(proc) -> dict[str, str]:
    out = {}
    for line in proc.stdout.splitlines()[1:]:
        status, _, rel = line.strip().partition(" ")
        out[rel.strip().split(" ")[0]] = status
    return out


def manifest(target: Path) -> dict:
    return json.loads((target / ".claude" / "pitaya.json").read_text())


def test_fresh_copy_puts_the_plugin_under_dot_claude(tmp_path):
    proc = vendor(tmp_path)
    assert proc.returncode == 0, proc.stderr
    claude = tmp_path / ".claude"
    for skill in json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["skills"]:
        assert (claude / skill.removeprefix("./") / "SKILL.md").is_file(), skill
    assert (claude / "docs" / "levels.md").is_file()
    assert (claude / "templates" / "AGENTS.md").is_file()
    data = manifest(tmp_path)
    assert data["version"] == VERSION
    assert "skills/help/SKILL.md" in data["files"]
    assert not any("__pycache__" in rel for rel in data["files"])


def test_relative_links_in_the_vendored_skills_resolve(tmp_path):
    vendor(tmp_path)
    for md in (tmp_path / ".claude" / "skills").rglob("*.md"):
        for target in LINK.findall(md.read_text()):
            assert (md.parent / target).resolve().exists(), f"{md}: {target}"


def test_rerun_changes_nothing(tmp_path):
    vendor(tmp_path)
    second = vendor(tmp_path)
    assert set(lines(second).values()) == {"unchanged"}


def test_check_writes_nothing(tmp_path):
    proc = vendor(tmp_path, "--check")
    assert proc.returncode == 0, proc.stderr
    assert not (tmp_path / ".claude").exists()


def test_a_projects_own_skill_is_left_alone(tmp_path):
    own = tmp_path / ".claude" / "skills" / "build" / "SKILL.md"
    own.parent.mkdir(parents=True)
    own.write_text("our own build skill\n")
    proc = vendor(tmp_path)
    assert lines(proc)["skills/build/SKILL.md"] == "differs"
    assert own.read_text() == "our own build skill\n"
    assert "skills/build/SKILL.md" not in manifest(tmp_path)["files"]


def test_upgrade_replaces_only_unmodified_copies(tmp_path):
    vendor(tmp_path)
    claude = tmp_path / ".claude"
    data = manifest(tmp_path)
    # Pretend an older version was vendored: its copy, and its recorded hash.
    old = claude / "skills" / "help" / "SKILL.md"
    old.write_text("help from an older version\n")
    data["files"]["skills/help/SKILL.md"] = hashlib.sha256(old.read_bytes()).hexdigest()
    # And a copy the project edited by hand after vendoring.
    edited = claude / "skills" / "tdd" / "SKILL.md"
    edited.write_text(edited.read_text() + "\nour local rule\n")
    (claude / "pitaya.json").write_text(json.dumps(data))

    report = lines(vendor(tmp_path))
    assert report["skills/help/SKILL.md"] == "stale"
    assert report["skills/tdd/SKILL.md"] == "differs"
    assert old.read_text() == "help from an older version\n"

    report = lines(vendor(tmp_path, "--upgrade"))
    assert report["skills/help/SKILL.md"] == "upgraded"
    assert report["skills/tdd/SKILL.md"] == "differs"
    assert old.read_bytes() == (PLUGIN / "skills" / "help" / "SKILL.md").read_bytes()
    assert "our local rule" in edited.read_text()


def test_setup_installs_templates_from_the_vendored_copy(tmp_path):
    vendor(tmp_path)
    installer = tmp_path / ".claude" / "skills" / "setup" / "scripts" / "install_templates.py"
    proc = subprocess.run([sys.executable, str(installer), "--target", str(tmp_path), "--level", "1",
                           "--test-command", "pytest -q", "--check"], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert f"pitaya templates {VERSION}" in proc.stdout
    assert "would create AGENTS.md" in proc.stdout


# --- skills work without the plugin's tools ----------------------------------------

SKILLS = PLUGIN / "skills"


def test_every_gh_command_names_the_github_tool_alternative():
    for md in SKILLS.rglob("*.md"):
        for n, line in enumerate(md.read_text().splitlines(), 1):
            if re.search(r"`gh ", line):
                assert "GitHub tool" in line, f"{md.relative_to(PLUGIN)}:{n} names gh without the GitHub tool"


def test_skills_that_name_other_skills_say_the_prefix_is_optional():
    for rel in ("autopilot/SKILL.md", "help/SKILL.md"):
        assert "without the `pitaya:` prefix" in (SKILLS / rel).read_text(), rel
    assert "without the `pitaya:` prefix" in (PLUGIN / "templates" / "AGENTS.md").read_text()


def test_readme_explains_cloud_sessions():
    text = (PLUGIN / "README.md").read_text()
    assert "## Cloud sessions" in text and "vendor_plugin.py" in text
