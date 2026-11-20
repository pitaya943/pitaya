"""Recipe "read-only-paths": rule files, specs and CI can't change in a ticket PR."""

import pytest

from helpers import run_check, ticket


def check(repo, base, head, ticket_path, *extra):
    return run_check("read-only-paths", "check_read_only.py", "--base", base, "--head", head,
                     "--ticket", str(ticket_path), *extra, cwd=repo.path)


@pytest.mark.parametrize("path", [
    "AGENTS.md", "CLAUDE.md", "src/AGENTS.md", "docs/agents/harness.md",
    ".claude/settings.json", ".github/workflows/ci.yml", "docs/decisions.md",
])
def test_default_read_only_paths_fail(repo, tmp_path, path):
    base = repo.commit("base")
    repo.write(path, "changed\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["**"]))
    assert proc.returncode == 1, path
    assert path in proc.stdout and "To fix:" in proc.stdout


def test_other_paths_pass(repo, tmp_path):
    base = repo.commit("base")
    repo.write("src/a.py", "x\n")
    head = repo.commit()
    assert check(repo, base, head, ticket(tmp_path, Scope=["src/**"])).returncode == 0


def test_exact_path_in_scope_is_allowed(repo, tmp_path):
    base = repo.commit("base")
    repo.write(".github/workflows/ci.yml", "changed\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=[".github/workflows/ci.yml"]))
    assert proc.returncode == 0, proc.stdout


def test_a_glob_in_scope_does_not_unlock_read_only_paths(repo, tmp_path):
    base = repo.commit("base")
    repo.write(".github/workflows/ci.yml", "changed\n")
    head = repo.commit()
    assert check(repo, base, head, ticket(tmp_path, Scope=[".github/**"])).returncode == 1


def test_extra_paths_from_the_command_line(repo, tmp_path):
    base = repo.commit("base")
    repo.write("docs/spec/rules.md", "changed\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["docs/**"]), "--also", "docs/spec/**")
    assert proc.returncode == 1 and "docs/spec/rules.md" in proc.stdout


# --- ticket files are read-only, except the PR's own Status line (D35) -----------

TICKET_FILE = "docs/tickets/T-001.md"
TICKET_TEXT = "# T-001: Add login\n\nStatus: open\nIssue: #12\n\n## Scope\n\n- `src/**`\n"


def test_ticket_files_are_read_only(repo, tmp_path):
    repo.write(TICKET_FILE, TICKET_TEXT)
    base = repo.commit("base")
    repo.write("docs/tickets/T-002.md", "# T-002\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["**"]))
    assert proc.returncode == 1 and "docs/tickets/T-002.md" in proc.stdout


def test_own_ticket_status_line_is_allowed(repo, tmp_path):
    repo.write(TICKET_FILE, TICKET_TEXT)
    base = repo.commit("base")
    repo.write(TICKET_FILE, TICKET_TEXT.replace("Status: open", "Status: done"))
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["src/**"]), "--ticket-path", TICKET_FILE)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_own_ticket_other_change_is_refused(repo, tmp_path):
    repo.write(TICKET_FILE, TICKET_TEXT)
    base = repo.commit("base")
    repo.write(TICKET_FILE, TICKET_TEXT + "\n## Done when\n\n1. Anything.\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["src/**"]), "--ticket-path", TICKET_FILE)
    assert proc.returncode == 1 and TICKET_FILE in proc.stdout


def test_milestone_files_are_read_only(repo, tmp_path):
    base = repo.commit("base")
    repo.write("docs/milestones/M1.md", "# M1\n\nStatus: done\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["**"]))
    assert proc.returncode == 1 and "docs/milestones/M1.md" in proc.stdout


# --- review of 0.1.4, F21 and F14: files tools load by themselves, and test configuration -----

@pytest.mark.parametrize("path", [
    ".mcp.json", ".gitattributes", ".gitmodules", ".githooks/pre-commit", ".devcontainer/devcontainer.json",
    ".cursor/rules/style.mdc", ".codex/config.toml", "GEMINI.md", "packages/api/GEMINI.md",
])
def test_files_tools_load_by_themselves_are_read_only(repo, tmp_path, path):
    base = repo.commit("base")
    repo.write(path, "changed\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["**"]))
    assert proc.returncode == 1 and path in proc.stdout, path


@pytest.mark.parametrize("path", [
    "conftest.py", "tests/conftest.py", "pytest.ini", "tox.ini", "pyproject.toml", "setup.cfg",
    "package.json", "packages/web/package.json", "jest.config.js", "vitest.config.ts", "Makefile",
])
def test_test_configuration_is_read_only(repo, tmp_path, path):
    """A pytest hook in conftest.py that reports failures as passes changes no test ID."""
    base = repo.commit("base")
    repo.write(path, "changed\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["**"]))
    assert proc.returncode == 1 and path in proc.stdout, path


def test_a_ticket_that_names_the_test_configuration_file_may_change_it(repo, tmp_path):
    base = repo.commit("base")
    repo.write("pyproject.toml", "[project]\ndependencies = ['x']\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["src/**", "pyproject.toml"]))
    assert proc.returncode == 0, proc.stdout


@pytest.mark.parametrize("path", ["src/config.py", "tests/test_app.py", "docs/Makefile.md", "src/package.json.md"])
def test_ordinary_files_with_similar_names_pass(repo, tmp_path, path):
    base = repo.commit("base")
    repo.write(path, "changed\n")
    head = repo.commit()
    assert check(repo, base, head, ticket(tmp_path, Scope=["**"])).returncode == 0, path


def test_the_hook_and_the_check_agree_on_the_control_plane():
    """One list of rule files, in two enforcers: every path the hook asks about is read-only in a ticket PR."""
    import importlib.util
    import sys
    from helpers import FILES, PLUGIN_ROOT

    def load(path):
        # No bytecode: a __pycache__ next to a template would be copied into projects.
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        before, sys.dont_write_bytecode = sys.dont_write_bytecode, True
        try:
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = before
        return module

    check_mod = load(FILES / "read-only-paths" / "check_read_only.py")
    hook = load(PLUGIN_ROOT / "templates" / ".claude" / "hooks" / "ask_on_rule_files.py")
    patterns = [check_mod.glob_to_regex(g) for g in check_mod.READ_ONLY_PATHS]
    samples = ([f"{d}x/y" for d in hook.RULE_DIRS] + sorted(hook.RULE_FILES)
               + sorted(hook.RULE_NAMES) + [f"sub/{n}" for n in sorted(hook.RULE_NAMES)])
    missing = [s for s in samples if not any(p.match(s) for p in patterns)]
    assert not missing, missing
