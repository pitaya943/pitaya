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
