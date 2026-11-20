"""The three Level 1 hooks (docs/design.md section 8, D6), driven the way Claude Code drives them.

Each hook reads the PreToolUse JSON on stdin. It prints a hookSpecificOutput
decision ("deny" or "ask") to stdout, or prints nothing to let the call
through. Every rule is tested both ways: the call it must stop, and a
near-miss it must allow.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugin"
HOOKS = PLUGIN_ROOT / "templates" / ".claude" / "hooks"


def run_hook(name: str, payload: dict, cwd: Path | None = None, env: dict | None = None) -> dict | None:
    proc = subprocess.run(
        [sys.executable, str(HOOKS / name)],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=cwd, env=env, timeout=20,
    )
    assert proc.returncode == 0, proc.stderr
    if not proc.stdout.strip():
        return None
    out = json.loads(proc.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    return out


def bash(command: str, cwd: Path) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash",
            "tool_input": {"command": command}, "cwd": str(cwd)}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo on branch `feature`, with origin/HEAD pointing at `main`."""
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q", "-b", "main")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "init")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git("checkout", "-q", "-b", "feature")
    return tmp_path


def switch(repo: Path, branch: str) -> None:
    subprocess.run(["git", "checkout", "-q", branch], cwd=repo, check=True, capture_output=True)


# --- no_push_main.py -----------------------------------------------------------

@pytest.mark.parametrize("command", [
    "git push origin main",
    "git push origin HEAD:main",
    "git push origin feature:refs/heads/main",
    "git push origin +feature",                  # forced refspec
    "git push --force origin feature",
    "git push -f origin feature",
    "git push --force-with-lease origin feature",
    "git push origin :feature",                  # deleting a branch
    "git push --delete origin feature",
    "git push --all origin",
    "git push --mirror origin",
    "npm test && git push origin main",          # compound command
    "git -C . push origin master",
])
def test_push_hook_denies(repo, command):
    out = run_hook("no_push_main.py", bash(command, repo))
    assert out and out["permissionDecision"] == "deny", command
    assert "pull request" in out["permissionDecisionReason"].lower()  # says what to do instead


@pytest.mark.parametrize("command", [
    "git push origin feature",
    "git push -u origin feature",
    "git push origin HEAD",                      # current branch is feature
    "git push",                                  # implicit current branch
    "git status",
    "echo 'git push origin main'",               # quoted text, not a push
    "git log origin/main",
])
def test_push_hook_allows(repo, command):
    assert run_hook("no_push_main.py", bash(command, repo)) is None, command


@pytest.mark.parametrize("command", ["git push", "git push origin HEAD", "git push -u origin HEAD"])
def test_push_hook_uses_the_current_branch(repo, command):
    switch(repo, "main")
    out = run_hook("no_push_main.py", bash(command, repo))
    assert out and out["permissionDecision"] == "deny"


def test_push_hook_reads_the_default_branch_from_origin(repo):
    subprocess.run(["git", "update-ref", "refs/remotes/origin/trunk", "HEAD"], cwd=repo, check=True)
    subprocess.run(["git", "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk"], cwd=repo, check=True)
    out = run_hook("no_push_main.py", bash("git push origin trunk", repo))
    assert out and out["permissionDecision"] == "deny"


def test_push_hook_ignores_other_tools(repo):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Read",
               "tool_input": {"file_path": "x"}, "cwd": str(repo)}
    assert run_hook("no_push_main.py", payload) is None


# --- no_destructive.py ---------------------------------------------------------

@pytest.mark.parametrize("command", [
    "rm -rf /",
    "rm -rf ~",
    "rm -fr ~/",
    "rm -r -f $HOME",
    "rm -rf /*",
    "sudo rm -rf /",
    "rm -rf .",
    "git reset --hard",
    "git reset --hard origin/main",
    "git clean -fdx",
    "git clean -f -d",
    "git clean -xf",
    "cd /tmp && rm -rf ~",
])
def test_destructive_hook_denies(repo, command):
    out = run_hook("no_destructive.py", bash(command, repo))
    assert out and out["permissionDecision"] == "deny", command
    assert "instead" in out["permissionDecisionReason"].lower()


@pytest.mark.parametrize("command", [
    "rm -rf build",
    "rm -rf ./node_modules",
    "rm file.txt",
    "rm -r /tmp/scratch",
    "git reset --soft HEAD~1",
    "git reset HEAD file.txt",
    "git clean -n",
    "git clean -nd",
    "git clean -nfd",                            # dry run, even with -f
    "echo 'rm -rf /'",
])
def test_destructive_hook_allows(repo, command):
    assert run_hook("no_destructive.py", bash(command, repo)) is None, command


# --- ask_on_rule_files.py ------------------------------------------------------

def edit(path: str, cwd: Path, tool: str = "Edit") -> dict:
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": {key: path}, "cwd": str(cwd)}


@pytest.mark.parametrize("rel", [
    "AGENTS.md", "CLAUDE.md", "docs/agents/harness.md", "src/AGENTS.md",
    ".claude/settings.json", ".claude/hooks/no_push_main.py",
    ".github/workflows/tests.yml",
])
@pytest.mark.parametrize("tool", ["Edit", "Write", "MultiEdit"])
def test_rule_hook_asks_for_rule_files(repo, rel, tool):
    out = run_hook("ask_on_rule_files.py", edit(str(repo / rel), repo, tool))
    assert out and out["permissionDecision"] == "ask", (rel, tool)
    assert rel.split("/")[-1] in out["permissionDecisionReason"]


@pytest.mark.parametrize("rel", ["src/app.py", "docs/guide.md", "README.md", "tests/test_x.py", "docs/agents/notes.md"])
def test_rule_hook_allows_other_files(repo, rel):
    assert run_hook("ask_on_rule_files.py", edit(str(repo / rel), repo)) is None


def test_rule_hook_accepts_relative_paths(repo):
    out = run_hook("ask_on_rule_files.py", edit("AGENTS.md", repo))
    assert out and out["permissionDecision"] == "ask"


@pytest.mark.parametrize("command", [
    "sed -i 's/a/b/' AGENTS.md",
    "echo x >> docs/agents/harness.md",
    "rm .claude/hooks/no_push_main.py",
    "mv .github/workflows/tests.yml /tmp/",
    "cat new > CLAUDE.md",
])
def test_rule_hook_asks_for_shell_writes(repo, command):
    out = run_hook("ask_on_rule_files.py", bash(command, repo))
    assert out and out["permissionDecision"] == "ask", command


@pytest.mark.parametrize("command", ["cat AGENTS.md", "grep -n Level docs/agents/harness.md", "sed -i 's/a/b/' src/app.py"])
def test_rule_hook_allows_shell_reads(repo, command):
    assert run_hook("ask_on_rule_files.py", bash(command, repo)) is None, command


# --- shared behaviour ----------------------------------------------------------

ALL_HOOKS = ["no_push_main.py", "no_destructive.py", "ask_on_rule_files.py", "ask_on_merge.py"]


@pytest.mark.parametrize("name", ALL_HOOKS)
def test_hook_lets_malformed_input_through(name):
    proc = subprocess.run([sys.executable, str(HOOKS / name)], input="not json",
                          capture_output=True, text=True, timeout=20)
    # Fail open, loudly: a broken hook must not wedge the session, but it reports the problem.
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert proc.stderr.strip()


@pytest.mark.parametrize("name", ALL_HOOKS)
def test_hook_documents_when_to_remove_it(name):
    text = (HOOKS / name).read_text()
    assert "When to remove" in text  # design principle R6


# --- ask_on_merge.py (D37) -------------------------------------------------------

def write_autonomy(repo: Path, line: str) -> None:
    (repo / "docs" / "agents").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "agents" / "harness.md").write_text(f"# Harness\n\n- Autonomy: {line}\n")


@pytest.mark.parametrize("command", [
    "gh pr merge 12 --squash",
    "gh pr merge --auto --merge",
    "cd x && gh pr merge 3",
    "gh api -X PUT repos/o/r/pulls/12/merge",
])
def test_merge_hook_asks_by_default(repo, command):
    out = run_hook("ask_on_merge.py", bash(command, repo))
    assert out and out["permissionDecision"] == "ask"
    assert "Autonomy" in out["permissionDecisionReason"]


def test_merge_hook_asks_for_the_github_tool(repo):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "mcp__github__merge_pull_request",
               "tool_input": {"pullNumber": 12}, "cwd": str(repo)}
    out = run_hook("ask_on_merge.py", payload)
    assert out and out["permissionDecision"] == "ask"


def test_merge_hook_asks_when_only_the_owner_merges(repo):
    write_autonomy(repo, "Only the Owner merges `main`.")
    assert run_hook("ask_on_merge.py", bash("gh pr merge 12", repo))["permissionDecision"] == "ask"


def test_merge_hook_allows_when_agents_may_merge(repo):
    write_autonomy(repo, "Agents merge after CI is green and the verdict is PASS.")
    assert run_hook("ask_on_merge.py", bash("gh pr merge 12 --squash", repo)) is None


@pytest.mark.parametrize("command", ["gh pr view 12", "gh pr list", "git merge feature", "echo gh pr merge"])
def test_merge_hook_allows_other_commands(repo, command):
    assert run_hook("ask_on_merge.py", bash(command, repo)) is None


# --- audit batch A (D40): bypasses and the shipped template ----------------------

TEMPLATE_HARNESS = PLUGIN_ROOT / "skills" / "setup" / "harness-template.md"


def test_merge_hook_asks_with_the_shipped_harness_template(repo):
    (repo / "docs" / "agents").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "agents" / "harness.md").write_text(TEMPLATE_HARNESS.read_text())
    out = run_hook("ask_on_merge.py", bash("gh pr merge 5 --squash", repo))
    assert out and out["permissionDecision"] == "ask"


def test_merge_hook_reads_the_field_value_not_the_whole_line(repo):
    write_autonomy(repo, 'Only the Owner merges `main`. (Alternative: "Agents merge after CI is green".)')
    assert run_hook("ask_on_merge.py", bash("gh pr merge 5", repo))["permissionDecision"] == "ask"


@pytest.mark.parametrize("command", [
    'bash -c "gh pr merge 5"',
    "sh -c 'cd x && gh pr merge 5'",
    'eval "gh pr merge 5"',
    "gh -R owner/repo pr merge 5",
    "gh --repo owner/repo pr merge 5",
    "gh --repo=owner/repo pr merge 5",
    "gh api graphql -f query='mutation { mergePullRequest(input: {pullRequestId: \"x\"}) { clientMutationId } }'",
    "gh api graphql -f query='mutation { enablePullRequestAutoMerge(input: {}) { clientMutationId } }'",
])
def test_merge_hook_sees_through_wrappers_and_flags(repo, command):
    out = run_hook("ask_on_merge.py", bash(command, repo))
    assert out and out["permissionDecision"] == "ask", command


@pytest.mark.parametrize("tool", ["mcp__github__enable_pr_auto_merge", "mcp__github__merge_pull_request"])
def test_merge_hook_asks_for_merge_tools(repo, tool):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {}, "cwd": str(repo)}
    assert run_hook("ask_on_merge.py", payload)["permissionDecision"] == "ask"


def test_settings_route_auto_merge_tools_to_the_merge_hook():
    settings = json.loads((PLUGIN_ROOT / "templates" / ".claude" / "settings.json").read_text())
    import re as _re
    matchers = [g["matcher"] for g in settings["hooks"]["PreToolUse"]
                if any("ask_on_merge.py" in h["command"] for h in g["hooks"]) and g["matcher"] != "Bash"]
    assert any(_re.fullmatch(m, "mcp__github__enable_pr_auto_merge") for m in matchers), matchers


@pytest.mark.parametrize("command", [
    'bash -c "git push origin main"',
    "sh -c 'git push -f origin feature'",
    "git push --repo=origin main",
    "git push --repo origin main",
])
def test_push_hook_sees_through_wrappers_and_repo_option(repo, command):
    out = run_hook("no_push_main.py", bash(command, repo))
    assert out and out["permissionDecision"] == "deny", command


def test_destructive_hook_sees_through_wrappers(repo):
    out = run_hook("no_destructive.py", bash('bash -c "git reset --hard HEAD~1"', repo))
    assert out and out["permissionDecision"] == "deny"


@pytest.mark.parametrize("rel", [".github/guardrails/check_scope.py", ".github/CODEOWNERS"])
def test_rule_hook_covers_all_of_github(repo, rel):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit",
               "tool_input": {"file_path": str(repo / rel)}, "cwd": str(repo)}
    assert run_hook("ask_on_rule_files.py", payload, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))["permissionDecision"] == "ask"


@pytest.mark.parametrize("command", [
    "python3 -c \"open('.claude/settings.json', 'w').write('{}')\"",
    "node -e \"require('fs').writeFileSync('AGENTS.md', '')\"",
    'bash -c "echo x > .claude/settings.json"',
])
def test_rule_hook_asks_when_a_script_names_a_rule_file(repo, command):
    out = run_hook("ask_on_rule_files.py", bash(command, repo), env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
    assert out and out["permissionDecision"] == "ask", command


# --- review of 0.1.4, F24 (D62, Q5): the plainly accidental wipes ------------------------

@pytest.mark.parametrize("command", [
    "rm -rf .git",
    "rm -rf ./.git",
    "rm -rf .git/",
    "rm -rf ./*",
    "rm -rf *",
    'rm -rf "$PWD"',
    "rm -rf $PWD/",
    "find . -delete",
    "find -delete",
    "find . -mindepth 1 -delete",
    "find . -type f -delete",
    "find ./ -depth -delete",
    "git checkout -- .",
    "git checkout .",
    "git checkout HEAD -- .",
    "git restore .",
    "git restore --worktree .",
    "git restore --staged --worktree .",
    "git restore -SW .",
    "git restore --source=HEAD~1 .",
    'bash -c "find . -delete"',
])
def test_destructive_hook_denies_accidental_wipes(repo, command):
    out = run_hook("no_destructive.py", bash(command, repo))
    assert out and out["permissionDecision"] == "deny", command
    assert "instead" in out["permissionDecisionReason"].lower()


@pytest.mark.parametrize("command", [
    "rm -rf .gitignore.bak",
    "rm -rf build/*",
    "rm -rf ./dist/*",
    "rm .git/index.lock",                        # not recursive
    "find . -name '*.pyc' -delete",
    "find . -name __pycache__ -type d -delete",
    "find build -delete",
    "find . -type f -newer stamp -delete",
    "find . -type f",
    "git checkout main",
    "git checkout -b ticket/T-1-x",
    "git checkout -- src/app.py",
    "git checkout HEAD -- docs/",
    "git restore src/app.py",
    "git restore --staged .",                    # only unstages; the files keep their content
    "git restore -S .",
    "git stash",
])
def test_destructive_hook_allows_near_misses(repo, command):
    assert run_hook("no_destructive.py", bash(command, repo)) is None, command


# --- review of 0.1.4, F21: the control plane is every file a tool loads or runs by itself ---

CONTROL_PLANE = [".mcp.json", ".gitattributes", ".gitmodules", ".githooks/pre-commit", ".devcontainer/devcontainer.json",
                 ".cursor/rules/style.mdc", ".codex/config.toml", "GEMINI.md", "packages/api/GEMINI.md"]


@pytest.mark.parametrize("rel", CONTROL_PLANE)
def test_rule_hook_asks_for_files_tools_load_by_themselves(repo, rel):
    out = run_hook("ask_on_rule_files.py", edit(str(repo / rel), repo, "Write"))
    assert out and out["permissionDecision"] == "ask", rel


@pytest.mark.parametrize("command", ["echo '{}' > .mcp.json", "cp hook.sh .githooks/pre-commit", "rm .gitattributes"])
def test_rule_hook_asks_for_shell_writes_to_them(repo, command):
    out = run_hook("ask_on_rule_files.py", bash(command, repo))
    assert out and out["permissionDecision"] == "ask", command


@pytest.mark.parametrize("rel", ["src/mcp.json", "docs/cursor/notes.md", "conftest.py", "package.json", ".gitignore"])
def test_rule_hook_still_allows_ordinary_files(repo, rel):
    """Test configuration stays editable in a session: the read-only check guards it in ticket PRs instead."""
    assert run_hook("ask_on_rule_files.py", edit(str(repo / rel), repo)) is None, rel
