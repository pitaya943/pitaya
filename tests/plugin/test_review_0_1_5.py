"""The first batch of fixes from the review of 0.1.4 (D59 to D61): what the docs and templates must now say.

The checks themselves are tested under tests/guardrails/: the history proof (N01) in
test_verdict.py and test_workflows.py, sync PRs in commit-author and progress-file (N02),
and the unset MACHINE_ACCOUNT (F13).
"""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
FILES = PLUGIN / "docs" / "guardrails" / "files"


def read(rel: str) -> str:
    return (PLUGIN / rel).read_text()


# --- N04: every branch class the checks recognise is documented and granted ---------

def branch_prefixes() -> set[str]:
    """Branch prefixes the shared "Find the ticket" step treats specially, plus ticket/."""
    text = (FILES / "scope" / "scope.yml").read_text()
    found = set(re.findall(r'\$\{HEAD_REF#([a-z]+)/\}', text))
    assert {"milestone", "plan", "sync"} <= found
    return found | {"ticket"}


@pytest.mark.parametrize("rel", ["templates/AGENTS.md", "docs/concepts/layout.md", "docs/concepts/states.md",
                                 "docs/guardrails/README.md", "skills/help/SKILL.md"])
def test_every_branch_prefix_the_checks_recognise_is_documented(rel):
    text = read(rel)
    missing = sorted(p for p in branch_prefixes() if f"`{p}/" not in text)
    assert not missing, f"{rel} doesn't mention: {missing}"


def test_agents_md_grants_the_sync_branch():
    branches = read("templates/AGENTS.md").split("## Branches", 1)[1].split("\n## ", 1)[0]
    assert "`sync/<slug>`" in branches


# --- F22: one answer on where ticket PRs go and who merges main ---------------------

def test_states_send_ticket_prs_to_the_milestone_branch_at_every_level():
    text = read("docs/concepts/states.md")
    assert "or main below Level 3" not in text
    assert "PR opened into milestone/M<n>" in text


def test_roles_agree_that_only_the_owner_merges_main():
    text = read("docs/concepts/roles.md")
    assert "unless the autonomy setting says otherwise" not in text
    assert "Whatever it says, only the Owner merges `main`" in read("docs/concepts/autonomy.md")


# --- F06: below Level 3 the milestone branch needs the Owner's approval -------------

def test_milestone_ruleset_requires_an_approval_below_level_3():
    text = read("docs/guardrails/protect-main.md").split("### Milestone branches", 1)[1]
    row = next(line for line in text.splitlines() if line.startswith("| Require a pull request before merging"))
    assert "Required approvals: 1" in row and "below Level 3" in row
    assert "Required approvals: 0" in row and "verdict" in row


def test_agent_merge_drops_the_approval_in_the_step_that_requires_the_verdict():
    text = read("docs/guardrails/agent-merge.md")
    step = next(line for line in text.splitlines() if "require the `verdict` status" in line)
    assert "Required approvals" in step and "0" in step and "same" in step


def test_setup_hands_over_the_milestone_approval():
    assert "1 approval below Level 3" in read("skills/setup/SKILL.md")


# --- F05, what was left: creating the milestone branch under its ruleset ------------

def test_protect_main_says_what_creating_a_branch_needs_and_proves_it():
    text = read("docs/guardrails/protect-main.md")
    assert "Do not require status checks on creation" in text
    proof = text.split("## How to prove it works", 1)[1].split("\n## ", 1)[0]
    assert "milestone/" in proof and "create" in proof.lower()


# --- F09: no allowed git command writes a file, reads one outside git or runs a program ---
#
# Verify round 1 showed that deny rules alone don't hold: git accepts any unambiguous prefix of
# a long option (`git fetch --upload-p=...`) and implies `--no-index` for a path outside the
# work tree (`git diff /dev/null .env`). So `git diff` and `git fetch` aren't allowed at all,
# and the payloads below are run against real git, in their abbreviated and implied forms too.

import subprocess  # noqa: E402

SETTINGS = [PLUGIN / "templates/.claude/settings.json", REPO_ROOT / ".claude/settings.json"]
IDS = ["template", "this repository"]

# (command, what it does when it runs): "reads" prints the secret, "writes" creates OUT, "runs" creates PWNED
PAYLOADS = [
    ("git diff --output=OUT", "writes"),
    ("git show HEAD --output=OUT", "writes"),
    ("git log -1 -p --output OUT", "writes"),
    ("git diff --no-index /dev/null .env", "reads"),
    ("git diff /dev/null .env", "reads"),            # --no-index is implied: a path outside the work tree
    ("git diff -- /dev/null .env", "reads"),
    ("git fetch --upload-pack=touch${IFS}PWNED;false .", "runs"),
    ("git fetch --upload-p=touch${IFS}PWNED;false .", "runs"),  # an abbreviated option
    ("git fetch --upl=touch${IFS}PWNED;false .", "runs"),   # the shortest prefix git accepts
]
EVERYDAY = ["git status --short", "git log --oneline -20", "git log -p -3 -- src/app.py",
            "git show HEAD:docs/tickets/T-001.md", "git show --stat HEAD"]


def bash_rules(settings: dict, kind: str) -> list[str]:
    return [r[5:-1] for r in settings["permissions"][kind] if r.startswith("Bash(") and r.endswith(")")]


def matches(command: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(command, p) for p in patterns)


def unprompted(command: str, settings: dict) -> bool:
    """True when the rules let this command run with no prompt: allowed, and not denied."""
    return matches(command, bash_rules(settings, "allow")) and not matches(command, bash_rules(settings, "deny"))


@pytest.fixture
def secret_repo(tmp_path):
    def git(*args):
        subprocess.run(["git", "-c", "user.name=example-bot", "-c", "user.email=bot@example.com", *args],
                       cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q", "-b", "main")
    (tmp_path / "app.py").write_text("x = 1\n")
    git("add", "app.py")
    git("commit", "-q", "-m", "start")
    (tmp_path / ".env").write_text("SECRET=demo\n")
    return tmp_path


def run(command: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", command], cwd=cwd, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("command, effect", PAYLOADS)
def test_each_payload_really_does_damage_with_git(command, effect, secret_repo):
    """Keeps the list honest: every payload works against real git, so each one has to be kept from running unasked."""
    proc = run(command, secret_repo)
    done = {"reads": "SECRET=demo" in proc.stdout, "writes": (secret_repo / "OUT").exists(),
            "runs": (secret_repo / "PWNED").exists()}[effect]
    assert done, f"{command!r} did nothing here: {proc.stdout}{proc.stderr}"


@pytest.mark.parametrize("path", SETTINGS, ids=IDS)
@pytest.mark.parametrize("command", [c for c, _ in PAYLOADS])
def test_no_payload_runs_without_a_prompt(command, path):
    assert not unprompted(command, json.loads(path.read_text())), command


@pytest.mark.parametrize("path", SETTINGS, ids=IDS)
def test_git_diff_and_fetch_are_not_allowed_by_pattern(path):
    """Neither can be made safe by denying option names: see the abbreviated and implied payloads."""
    allow = bash_rules(json.loads(path.read_text()), "allow")
    assert not [r for r in allow if r.startswith(("git diff", "git fetch"))]


@pytest.mark.parametrize("path", SETTINGS, ids=IDS)
def test_everyday_read_only_git_commands_still_run_without_a_prompt(path):
    settings = json.loads(path.read_text())
    for command in EVERYDAY:
        assert unprompted(command, settings), command


@pytest.mark.parametrize("sub", ["log -1", "show"])
@pytest.mark.parametrize("option", ["--output", "--ext-diff", "--no-index"])
def test_git_log_and_show_accept_no_short_form_of_a_denied_option(sub, option, secret_repo):
    """`git log` and `git show` stay allowed, so the deny rules must cover every spelling git accepts.

    They do: unlike `git fetch`, these commands reject an abbreviated long option, and they
    have no implied form. Each prefix of each denied option must fail and leave nothing behind.
    """
    for end in range(4, len(option)):
        proc = run(f"git {sub} {option[:end]}=OUT /dev/null .env", secret_repo)
        assert proc.returncode != 0, f"git {sub} accepted {option[:end]}"
        assert "SECRET=demo" not in proc.stdout and not (secret_repo / "OUT").exists()
    proc = run(f"git {sub} /dev/null .env", secret_repo)  # no implied --no-index here
    assert "SECRET=demo" not in proc.stdout


def test_ext_diff_runs_a_program_and_is_denied(secret_repo):
    """`--ext-diff` makes `git log -p` and `git show` run the configured external diff program.

    The rule lost its test when `git diff` left the allow list (noted by the verdicts on the 0.1.5 PR).
    """
    script = secret_repo / "ext.sh"
    script.write_text("#!/bin/sh\ntouch PWNED\n")
    script.chmod(0o755)
    subprocess.run(["git", "config", "diff.external", "./ext.sh"], cwd=secret_repo, check=True)
    for command in ("git show HEAD --ext-diff", "git log -1 -p --ext-diff"):
        (secret_repo / "PWNED").unlink(missing_ok=True)
        run(command, secret_repo)
        assert (secret_repo / "PWNED").exists(), f"{command!r} didn't run the external program here"
        for path in SETTINGS:
            assert not unprompted(command, json.loads(path.read_text())), command
    (secret_repo / "PWNED").unlink()
    run("git show HEAD", secret_repo)  # without the option the program doesn't run
    assert not (secret_repo / "PWNED").exists()


def test_suggestion_says_the_allow_rules_are_narrowed():
    assert "--output" in read("docs/suggestion.md")


# --- found by the consistency audit before the PR (decision log) --------------------

def test_every_place_that_names_the_branches_to_allow_names_all_of_them():
    """autopilot asks for them when AGENTS.md has no grant; the README tells cloud users what to allow."""
    ask = next(line for line in read("skills/autopilot/SKILL.md").splitlines() if "ask the user once to allow" in line)
    cloud = read("README.md").split("## Cloud sessions", 1)[1].split("\n## ", 1)[0]
    for name, text in (("autopilot", ask), ("README", cloud)):
        missing = sorted(p for p in branch_prefixes() if f"`{p}/" not in text)
        assert not missing, f"{name} doesn't name: {missing}"


def test_autonomy_says_which_ruleset_drops_its_approval():
    line = next(l for l in read("docs/concepts/autonomy.md").splitlines() if "to 0 only together" in l)
    assert "`milestone/*`" in line


def test_agents_merge_sync_prs_where_they_merge_ticket_prs():
    assert "ticket and sync PRs" in read("docs/concepts/autonomy.md")
    assert "sync PR" in read("docs/concepts/roles.md")


@pytest.mark.parametrize("rel", ["docs/guardrails/commit-author.md", "docs/guardrails/progress-file.md"])
def test_recipes_say_an_unset_machine_account_fails_every_pr(rel):
    assert "fails on every pull request" in read(rel)


def test_every_description_of_the_permissions_mentions_the_git_deny_rules():
    manifest = json.loads(read("docs/components.json"))
    guards = json.dumps(manifest)
    assert "--output" in guards
    assert "--output" in read("docs/levels.md") and "--output" in read("docs/concepts/access.md")


def test_docs_say_git_diff_and_fetch_ask_and_why():
    """Fix round 1: every description of the permissions matches the rules after diff and fetch left the allow list."""
    for rel in ("docs/suggestion.md", "docs/concepts/access.md"):
        text = read(rel)
        assert "`git diff`" in text and "`git fetch`" in text, rel
    changelog = read("CHANGELOG.md").split("## 0.1.5", 1)[1].split("\n## ", 1)[0]
    assert "Bash(git diff *)" in changelog and "by hand" in changelog
