"""The Level 1 templates and the script /setup uses to copy them (docs/design.md sections 8 and 10, D4, D20).

The script never overwrites a file the project already has: it reports it as
unchanged, stale (an older template version) or different, and leaves the
choice to the user. settings.json is the one exception: it is merged
additively, so the project's own rules survive.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugin"
TEMPLATES = PLUGIN_ROOT / "templates"
SCRIPT = PLUGIN_ROOT / "skills" / "setup" / "scripts" / "install_templates.py"
VERSION = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
HEADER_RE = re.compile(r"pitaya template (\S+)")

LEVEL1 = {
    "AGENTS.md",
    "CLAUDE.md",
    "docs/decisions.md",
    ".claude/settings.json",
    ".claude/hooks/no_push_main.py",
    ".claude/hooks/no_destructive.py",
    ".claude/hooks/ask_on_rule_files.py",
    ".claude/hooks/ask_on_merge.py",
    ".github/workflows/tests.yml",
    "docs/agents/glossary.md",
    "docs/agents/learnings.md",
    "docs/agents/architecture.md",
}


def install(target: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--target", str(target), *args],
                          capture_output=True, text=True, timeout=30)


# --- the templates themselves ------------------------------------------------

# README.md files document the templates for whoever browses them; they are never copied.
TEMPLATE_DOCS = {"docs/agents/README.md"}


def test_level1_template_set():
    shipped = {p.relative_to(TEMPLATES).as_posix() for p in TEMPLATES.rglob("*") if p.is_file()}
    assert shipped == LEVEL1 | TEMPLATE_DOCS


def test_memory_folder_readme_explains_where_harness_md_comes_from():
    text = (TEMPLATES / "docs/agents/README.md").read_text()
    assert "harness.md" in text
    assert "skills/setup/harness-template.md" in text


def test_template_readmes_are_not_copied(tmp_path):
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    assert proc.returncode == 0, proc.stderr
    for rel in TEMPLATE_DOCS:
        assert not (tmp_path / rel).exists(), rel
        assert rel not in proc.stdout


@pytest.mark.parametrize("rel", sorted(LEVEL1 - {".claude/settings.json", "CLAUDE.md"}))
def test_template_header_names_this_version(rel):
    head = "\n".join((TEMPLATES / rel).read_text().splitlines()[:3])
    match = HEADER_RE.search(head)
    assert match, f"{rel} has no 'pitaya template <version>' header"
    assert match.group(1) == VERSION


def test_claude_md_only_imports_agents_md():
    # Claude Code's import syntax: an at-sign followed by the path.
    assert (TEMPLATES / "CLAUDE.md").read_text().strip() == "@" + "AGENTS.md"


def test_agents_md_is_a_short_map():
    text = (TEMPLATES / "AGENTS.md").read_text()
    assert len(text.splitlines()) <= 100
    assert "docs/agents/harness.md" in text
    assert "<TEST_COMMAND>" in text


def test_settings_json_shape():
    settings = json.loads((TEMPLATES / ".claude" / "settings.json").read_text())
    deny = settings["permissions"]["deny"]
    for rule in ("Read(./.env)", "Read(./.env.*)", "Read(~/.ssh/**)", "Read(~/.aws/**)"):
        assert rule in deny
    allow = settings["permissions"]["allow"]
    assert "Bash(git status *)" in allow
    assert not any(r.startswith(("Bash(git push", "Bash(git commit", "Bash(rm")) for r in allow)
    commands = [h["command"] for group in settings["hooks"]["PreToolUse"] for h in group["hooks"]]
    for hook in ("no_push_main.py", "no_destructive.py", "ask_on_rule_files.py"):
        assert any(hook in c and "${CLAUDE_PROJECT_DIR}" in c for c in commands), hook


def test_workflow_runs_the_test_command():
    text = (TEMPLATES / ".github" / "workflows" / "tests.yml").read_text()
    assert "run: <TEST_COMMAND>" in text
    assert "pull_request" in text


# --- the install script ------------------------------------------------------

def test_fresh_install_creates_every_file(tmp_path):
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    assert proc.returncode == 0, proc.stderr
    for rel in LEVEL1:
        assert (tmp_path / rel).is_file(), rel
        assert f"created  {rel}" in proc.stdout
    assert "pytest -q" in (tmp_path / "AGENTS.md").read_text()
    assert "run: pytest -q" in (tmp_path / ".github/workflows/tests.yml").read_text()
    assert "<TEST_COMMAND>" not in (tmp_path / "AGENTS.md").read_text()
    allow = json.loads((tmp_path / ".claude/settings.json").read_text())["permissions"]["allow"]
    assert "Bash(pytest -q)" in allow


def test_hooks_are_executable_after_install(tmp_path):
    install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    for name in ("no_push_main.py", "no_destructive.py", "ask_on_rule_files.py"):
        assert os.access(tmp_path / ".claude/hooks" / name, os.X_OK), name


def test_second_run_reports_unchanged(tmp_path):
    install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    assert proc.returncode == 0
    assert "created" not in proc.stdout
    assert proc.stdout.count("unchanged") == len(LEVEL1)


def test_existing_different_file_is_kept(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# Our own rules\n")
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    assert proc.returncode == 0
    assert (tmp_path / "AGENTS.md").read_text() == "# Our own rules\n"
    assert "differs  AGENTS.md" in proc.stdout


def test_stale_copy_is_reported_not_overwritten(tmp_path):
    install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    hook = tmp_path / ".claude/hooks/no_destructive.py"
    old = hook.read_text().replace(f"pitaya template {VERSION}", "pitaya template 0.0.1", 1)
    hook.write_text(old)
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    assert hook.read_text() == old
    assert f"stale    .claude/hooks/no_destructive.py (0.0.1 -> {VERSION})" in proc.stdout


def test_settings_json_is_merged_additively(tmp_path):
    (tmp_path / ".claude").mkdir()
    own = {"permissions": {"allow": ["Bash(make *)"], "deny": ["Read(./private/**)"]}, "model": "x"}
    (tmp_path / ".claude/settings.json").write_text(json.dumps(own))
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    assert proc.returncode == 0
    merged = json.loads((tmp_path / ".claude/settings.json").read_text())
    assert merged["model"] == "x"
    assert "Bash(make *)" in merged["permissions"]["allow"]
    assert "Read(./private/**)" in merged["permissions"]["deny"]
    assert "Read(./.env)" in merged["permissions"]["deny"]
    assert len(merged["hooks"]["PreToolUse"]) >= 2
    assert "merged   .claude/settings.json" in proc.stdout
    # A second run adds nothing more.
    again = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    assert json.loads((tmp_path / ".claude/settings.json").read_text()) == merged
    assert "unchanged .claude/settings.json" in again.stdout or "unchanged  .claude/settings.json" in again.stdout


def test_check_mode_writes_nothing(tmp_path):
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q", "--check")
    assert proc.returncode == 0
    assert list(tmp_path.iterdir()) == []
    assert "would create" in proc.stdout


def test_no_decisions_flag_skips_the_log(tmp_path):
    install(tmp_path, "--level", "1", "--test-command", "pytest -q", "--no-decisions")
    assert not (tmp_path / "docs/decisions.md").exists()


def test_level0_copies_nothing(tmp_path):
    proc = install(tmp_path, "--level", "0")
    assert proc.returncode == 0
    assert list(tmp_path.iterdir()) == []


def test_level1_needs_a_test_command(tmp_path):
    proc = install(tmp_path, "--level", "1")
    assert proc.returncode == 2
    assert "--test-command" in proc.stderr
    assert list(tmp_path.iterdir()) == []


def test_installed_hooks_work_in_the_target(tmp_path):
    install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
               "tool_input": {"command": "git reset --hard"}, "cwd": str(tmp_path)}
    proc = subprocess.run([sys.executable, str(tmp_path / ".claude/hooks/no_destructive.py")],
                          input=json.dumps(payload), capture_output=True, text=True)
    assert json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


MEMORY = ("docs/agents/glossary.md", "docs/agents/learnings.md", "docs/agents/architecture.md")


def test_agents_md_points_to_every_memory_file():
    text = (TEMPLATES / "AGENTS.md").read_text()
    for rel in MEMORY + ("docs/agents/harness.md", "docs/decisions.md"):
        assert f"`{rel}`" in text, rel


def test_glossary_template_has_a_term_table():
    text = (TEMPLATES / "docs/agents/glossary.md").read_text()
    assert "| Term | Meaning | Avoid |" in text


def test_learnings_template_is_append_only_with_a_source_column():
    text = (TEMPLATES / "docs/agents/learnings.md").read_text()
    assert "Append only" in text and "| Source |" in text


def test_architecture_template_has_a_module_table():
    text = (TEMPLATES / "docs/agents/architecture.md").read_text()
    assert "| Module | Path | Purpose |" in text


def test_skip_leaves_a_file_out(tmp_path):
    # Found while installing pitaya on itself: a project that already has CI doesn't want tests.yml.
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q",
                   "--skip", ".github/workflows/tests.yml", "--skip", "docs/decisions.md")
    assert proc.returncode == 0, proc.stderr
    assert not (tmp_path / ".github/workflows/tests.yml").exists()
    assert not (tmp_path / "docs/decisions.md").exists()
    assert "skipped  .github/workflows/tests.yml" in proc.stdout
    assert (tmp_path / "AGENTS.md").exists()


def test_skip_rejects_an_unknown_path(tmp_path):
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q", "--skip", "nope.txt")
    assert proc.returncode == 2
    assert "nope.txt" in proc.stderr
    assert list(tmp_path.iterdir()) == []


def test_settings_deny_nested_env_files():
    deny = json.loads((TEMPLATES / ".claude/settings.json").read_text())["permissions"]["deny"]
    assert "Read(./**/.env)" in deny and "Read(./**/.env.*)" in deny


# --- withdrawn allow rules are reported, never removed (noted by the verdicts on the 0.1.5 PR) ---

@pytest.mark.parametrize("rule", ["Bash(git diff *)", "Bash(git fetch *)"])
def test_a_withdrawn_allow_rule_is_reported_and_left_alone(tmp_path, rule):
    """0.1.5 stopped allowing `git diff` and `git fetch`; a project set up before still has the rules."""
    (tmp_path / ".claude").mkdir()
    own = {"permissions": {"allow": [rule, "Bash(make *)"]}}
    (tmp_path / ".claude/settings.json").write_text(json.dumps(own))
    for extra in (["--check"], []):
        proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q", *extra)
        assert proc.returncode == 0
        line = next((l for l in proc.stdout.splitlines() if l.startswith("withdrawn")), "")
        assert rule in line and ".claude/settings.json" in line and "by hand" in line, proc.stdout
    assert rule in json.loads((tmp_path / ".claude/settings.json").read_text())["permissions"]["allow"]


def test_no_withdrawn_rule_is_reported_for_a_fresh_install(tmp_path):
    proc = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    again = install(tmp_path, "--level", "1", "--test-command", "pytest -q")
    assert not [l for l in (proc.stdout + again.stdout).splitlines() if l.startswith("withdrawn")]


def test_the_template_allows_no_rule_it_has_withdrawn():
    import importlib.util
    spec = importlib.util.spec_from_file_location("install_templates", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    before, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = before
    allow = json.loads((TEMPLATES / ".claude/settings.json").read_text())["permissions"]["allow"]
    assert module.WITHDRAWN_ALLOW and not set(module.WITHDRAWN_ALLOW) & set(allow)


def test_setup_says_what_to_do_with_a_withdrawn_rule():
    assert "`withdrawn`" in (PLUGIN_ROOT / "skills/setup/SKILL.md").read_text()
