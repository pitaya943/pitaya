"""The fifth batch of fixes from the review of 0.1.4 (D69, D70): duplication and maintenance.

F32: the project's test command is written once, in `.github/scripts/test.sh`, and CI, the JUnit
checks, `AGENTS.md`, the harness file and the allow rule all run that script. F28: actions are
pinned by commit, the plugin install names a version, and a third-party review action gets a
workflow of its own. F26 and F27 are tested next to the code they changed
(`tests/guardrails/`, `tests/templates/test_hooks.py`).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
TEMPLATES = PLUGIN / "templates"
FILES = PLUGIN / "docs" / "guardrails" / "files"
INSTALL = PLUGIN / "skills" / "setup" / "scripts" / "install_templates.py"
PAGES = sorted(p for p in PLUGIN.rglob("*.md") if p.name != "CHANGELOG.md")

TEST_SCRIPT = ".github/scripts/test.sh"
RUN_TESTS = f"sh {TEST_SCRIPT}"
PLACEHOLDER = "<TEST_COMMAND>"


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


def install(target: Path, command: str = "pytest -q", *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(INSTALL), "--target", str(target), "--level", "1",
                           "--test-command", command, *args], capture_output=True, text=True, timeout=30)


# --- F32: the test command lives in one place ---------------------------------

def test_the_test_script_is_a_template():
    text = (TEMPLATES / TEST_SCRIPT).read_text()
    assert text.startswith("#!/bin/sh\n")
    assert PLACEHOLDER in text
    assert "JUNIT" in text  # Level 2: how the same command writes JUnit XML


def test_only_the_test_script_holds_the_command():
    """Every other shipped file names the script; none repeats the command."""
    holders = [p.relative_to(PLUGIN).as_posix() for p in PLUGIN.rglob("*")
               if p.is_file() and p.suffix in {".md", ".yml", ".json", ".sh", ".py"} and p.name != "CHANGELOG.md"
               and p != INSTALL and PLACEHOLDER in p.read_text()]
    assert holders == [f"templates/{TEST_SCRIPT}"]


def test_install_writes_the_command_into_the_script_and_nowhere_else(tmp_path):
    proc = install(tmp_path, "python -m pytest -q --maxfail=3")
    assert proc.returncode == 0, proc.stderr
    script = (tmp_path / TEST_SCRIPT).read_text()
    assert "python -m pytest -q --maxfail=3" in script and PLACEHOLDER not in script
    for path in tmp_path.rglob("*"):
        if path.is_file() and path != tmp_path / TEST_SCRIPT:
            assert "--maxfail=3" not in path.read_text(), path.relative_to(tmp_path)


def test_installed_ci_agents_md_and_the_allow_rule_all_run_the_script(tmp_path):
    install(tmp_path)
    assert f"run: {RUN_TESTS}" in (tmp_path / ".github/workflows/tests.yml").read_text()
    assert f"`{RUN_TESTS}`" in (tmp_path / "AGENTS.md").read_text()
    allow = json.loads((tmp_path / ".claude/settings.json").read_text())["permissions"]["allow"]
    assert f"Bash({RUN_TESTS})" in allow
    assert "Bash(pytest -q)" not in allow


def test_the_installed_script_runs_the_command_and_returns_its_result(tmp_path):
    install(tmp_path, 'test "$PITAYA_ANSWER" = 42')
    run = lambda answer: subprocess.run(["sh", TEST_SCRIPT], cwd=tmp_path, capture_output=True, text=True,
                                        env={"PATH": "/usr/bin:/bin", "PITAYA_ANSWER": answer})
    assert run("42").returncode == 0
    assert run("41").returncode != 0


def test_a_script_the_project_changed_is_never_overwritten(tmp_path):
    """The script is the project's from then on: a later `/setup` with another command reports, and leaves it."""
    install(tmp_path, "pytest -q")
    proc = install(tmp_path, "npm test")
    assert f"differs  {TEST_SCRIPT}" in proc.stdout
    assert "pytest -q" in (tmp_path / TEST_SCRIPT).read_text()


@pytest.mark.parametrize("recipe", ["done-when", "no-weakened-tests"])
def test_the_junit_workflows_run_the_script(recipe):
    text = (FILES / recipe / f"{recipe}.yml").read_text()
    assert "TEST_COMMAND" not in text
    runs = re.findall(r"^\s+run: (JUNIT=.*)$", text, re.M)
    assert runs and all(RUN_TESTS in line and line.endswith("|| true") for line in runs), runs
    assert len(runs) == (2 if recipe == "no-weakened-tests" else 1)


def test_the_harness_template_names_the_script_as_the_test_command():
    line = next(l for l in read("skills/setup/harness-template.md").splitlines() if l.startswith("- Test command:"))
    assert f"`{RUN_TESTS}`" in line
    assert "pytest" not in line


def test_the_script_is_a_rule_file_everywhere_one_is_listed():
    """`.github/` is already read-only in ticket PRs and asked about by the hook; the pages say the script is there."""
    assert "scripts/test.sh" in read("docs/concepts/layout.md")  # a tree: the folder is the line above
    assert TEST_SCRIPT in read("docs/guardrails/read-only-paths.md")
    assert TEST_SCRIPT in read("docs/concepts/access.md")


def test_setup_and_the_recipes_send_the_reader_to_the_script():
    assert TEST_SCRIPT in read("skills/setup/SKILL.md")
    for recipe in ("done-when", "no-weakened-tests"):
        text = read(f"docs/guardrails/{recipe}.md")
        assert TEST_SCRIPT in text and "TEST_COMMAND" not in text, recipe


def test_no_page_still_tells_the_reader_to_set_test_command():
    for page in PAGES:
        assert "TEST_COMMAND" not in page.read_text(), page.relative_to(PLUGIN)


# --- F28: actions pinned by commit, the plugin install pinned to a release ------

AT = "@"  # built at runtime so the personal-data scan doesn't read `uses:` lines as mentions
WORKFLOW_FILES = sorted([*TEMPLATES.rglob("*.yml"), *FILES.rglob("*.yml"), *(REPO_ROOT / ".github").rglob("*.yml")])
USES_RE = re.compile(r"^\s*(?:- )?uses:\s*(\S+?)" + AT + r"(\S+)(.*)$", re.M)
PINNED_RE = re.compile(r"[0-9a-f]{40}")
VERSION = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]
# One commit per action across everything pitaya ships, so an update is one search and replace.
# Each was read from the action's repository with `git ls-remote --tags` when it was pinned.
PINS = {
    "actions/checkout": ("d23441a48e516b6c34aea4fa41551a30e30af803", "v6.1.0"),
    "actions/setup-python": ("6d4fd22b20465ccc0f7354476588e8df7c9ca0e0", "v7.1.0"),
    "actions/upload-artifact": ("cf430e030ddbb5b0abf93d22962f4752f3646cd9", "v7.0.2"),
    "actions/download-artifact": ("9000827ccba6bdab643e8b6fd33ac0654aef8333", "v8.0.2"),
}


def test_the_workflows_are_found():
    assert len(WORKFLOW_FILES) >= 12
    assert sum(len(USES_RE.findall(p.read_text())) for p in WORKFLOW_FILES) >= 25


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_every_action_is_pinned_by_commit(path):
    """A tag such as v6 can be moved to other code; a commit can't. The comment says which release it is."""
    for action, ref, rest in USES_RE.findall(path.read_text()):
        assert PINNED_RE.fullmatch(ref), f"{action} is referenced by `{ref}`, not by a commit"
        assert action in PINS, f"{action} has no entry in PINS"
        commit, release = PINS[action]
        assert ref == commit, f"{action}: every workflow pins the same commit"
        assert rest.strip() == f"# {release}", f"{action}: the comment after the commit names the release"


def test_the_setup_step_the_comments_show_is_pinned_too():
    """The templates tell the reader which setup steps to add; the `uses:` line they show is pinned."""
    shown = [line for path in WORKFLOW_FILES for line in path.read_text().splitlines()
             if re.match(r"\s*#\s+uses:", line)]
    assert len(shown) >= 4
    for line in shown:
        assert re.search(AT + r"[0-9a-f]{40}  # v\d+\.\d+\.\d+$", line), line.strip()


def test_the_recipes_say_how_pinned_actions_are_updated():
    text = read("docs/guardrails/README.md")
    assert "## Pinned actions" in text
    part = text.split("## Pinned actions", 1)[1].split("\n## ", 1)[0]
    for word in ("commit", "Dependabot", "git ls-remote"):
        assert word in part, word


@pytest.mark.parametrize("path", ["plugin/README.md", "README.md"])
def test_the_install_commands_name_this_release(path):
    """The default branch moves with every merge; a release tag is what the Owner published."""
    text = (REPO_ROOT / path).read_text()
    adds = re.findall(r"plugin marketplace add (\S+)", text)
    assert adds, path
    for source in adds:
        assert source.rstrip("`.,") == f"<owner>/pitaya#v{VERSION}", source


def test_the_readme_says_what_the_tag_is_for_and_how_to_upgrade():
    text = " ".join(read("README.md").split())
    assert "release tag" in text
    assert "claude plugin marketplace update" not in text or "tag" in text
    assert re.search(r"[Tt]o upgrade", text)


def test_a_third_party_review_action_gets_a_workflow_of_its_own():
    text = " ".join(read("docs/guardrails/second-model-review.md").split())
    row = next(l for l in read("docs/guardrails/second-model-review.md").splitlines() if l.startswith("| `grok-action`"))
    assert "workflow of its own" in row
    for needed in ("`contents: read`", "commit", "no other secret"):
        assert needed in text, needed


# --- what the verdicts on 0.1.7 and 0.1.8 left for this batch -------------------

def flat(rel: str) -> str:
    return " ".join(read(rel).split())


def test_a_rejected_push_is_not_always_a_takeover():
    """GitHub's "Update branch" moves the head too; a builder fixing a red CI after it must not stop."""
    dont = flat("skills/build/SKILL.md").split("## Don't", 1)[1]
    assert '"Update branch"' in dont and "git merge" in dont
    assert "another builder" in dont and "stop" in dont
    assert "never a rebase" in dont
    tick = flat("skills/autopilot/tick.md")
    assert "merges in an \"Update branch\"" in tick
    assert "no check notices" in tick  # the trust assumption, said where it applies (D59)


def test_the_verify_app_template_says_where_a_verifiers_screenshots_go():
    text = flat("docs/guardrails/files/verify-app/SKILL-template.md")
    assert "`evidence/<PR>-<short sha>`" in text and "never on the pull request's branch" in text


def test_a_pr_waiting_for_a_serial_resource_gets_no_ci_retry():
    """F26 gives the two PRs an order; autopilot must not spend CI retries on the one that waits."""
    for rel in ("docs/concepts/states.md", "skills/autopilot/tick.md"):
        text = flat(rel)
        assert "`serial-resources`" in text and "no CI retry" in text, rel


def test_the_serial_resources_recipe_describes_the_order():
    text = flat("docs/guardrails/serial-resources.md")
    assert "lower number" in text and "every other open PR" not in text
    message = "FAIL serial-resources: a pull request opened earlier is changing the same resource, and goes first:"
    assert message in (FILES / "serial-resources" / "check_serial.py").read_text()
    assert message in read("docs/guardrails/serial-resources.md")


def test_the_autonomy_note_says_what_else_an_agent_merges():
    """The Level 3 value names ticket PRs; the docs also let agents merge sync PRs and the report PR."""
    note = flat("skills/setup/harness-template.md").split("- Autonomy:", 1)[1].split("## Work", 1)[0]
    assert "sync PR" in note and "report PR" in note


def test_the_pages_describe_a_cut_as_the_check_does():
    for rel in ("docs/guardrails/agent-merge.md", "docs/concepts/autonomy.md", "skills/autopilot/tick.md"):
        text = flat(rel)
        assert "names plan PRs" not in text, rel
    assert "without setting it to `done`" in flat("docs/guardrails/agent-merge.md")
    assert "can't close it" in flat("skills/autopilot/tick.md")
    skill = flat("skills/autopilot/SKILL.md")
    assert "lets agents merge plan PRs, and only while it adds tickets" not in skill
    assert "without closing it" in skill
    for rel in ("skills/autopilot/SKILL.md", "skills/build/SKILL.md"):
        assert "`serial-resources`" in flat(rel), rel  # found by the audit: the wait was in two pages of four


def test_the_decision_log_and_the_trial_record_cover_the_batch():
    decisions = (REPO_ROOT / "docs" / "decisions.md").read_text()
    for row in ("| D69 |", "| D70 |"):
        assert row in decisions, row
    d69 = next(l for l in decisions.splitlines() if l.startswith("| D69 |"))
    for issue in ("#43", "#45", "#47"):
        assert issue in d69, issue
    assert "builder's session" in d69
    trial = (REPO_ROOT / "docs" / "trials" / "w8.md").read_text()
    for finding in ("F26", "F27", "F28", "F32"):
        line = next(l for l in trial.splitlines() if l.startswith(f"| {finding} |"))
        assert "0.1.9" in line and "open: batch 5" not in line, line


def test_the_test_script_does_not_trip_over_unset_variables(tmp_path):
    """Many commands read optional variables (`pytest $PYTEST_ARGS`); the wrapper must not change what they do."""
    install(tmp_path, 'test -z "$PITAYA_NOT_SET" && echo ran')
    proc = subprocess.run(["sh", TEST_SCRIPT], cwd=tmp_path, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    assert proc.returncode == 0 and "ran" in proc.stdout, proc.stderr


def test_the_test_script_stops_at_the_first_failing_line(tmp_path):
    install(tmp_path, "false\necho after")
    proc = subprocess.run(["sh", TEST_SCRIPT], cwd=tmp_path, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    assert proc.returncode != 0 and "after" not in proc.stdout
