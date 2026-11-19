"""Recipe "scope": a PR changes only the paths its ticket lists."""

from helpers import run_check, ticket


def check(repo, base, head, ticket_path):
    return run_check("scope", "check_scope.py", "--base", base, "--head", head,
                     "--ticket", str(ticket_path), cwd=repo.path)


def test_in_scope_changes_pass(repo, tmp_path):
    base = repo.commit("base")
    repo.write("src/app/main.py", "x = 1\n")
    repo.write("tests/test_main.py", "def test(): pass\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["src/**", "tests/test_main.py"]))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS" in proc.stdout


def test_out_of_scope_change_fails_and_says_how_to_fix(repo, tmp_path):
    base = repo.commit("base")
    repo.write("src/a.py", "x = 1\n")
    repo.write("README.md", "changed\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["src/**"]))
    assert proc.returncode == 1
    assert "README.md" in proc.stdout and "src/a.py" not in proc.stdout.split("To fix:")[0].split("outside")[-1]
    assert "To fix:" in proc.stdout


def test_single_star_does_not_cross_directories(repo, tmp_path):
    base = repo.commit("base")
    repo.write("src/deep/a.py", "x = 1\n")
    head = repo.commit()
    assert check(repo, base, head, ticket(tmp_path, Scope=["src/*"])).returncode == 1
    assert check(repo, base, head, ticket(tmp_path, Scope=["src/*/*"])).returncode == 0


def test_deleted_files_count_as_changes(repo, tmp_path):
    repo.write("docs/old.md", "x\n")
    base = repo.commit("base")
    repo.remove("docs/old.md")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path, Scope=["src/**"]))
    assert proc.returncode == 1 and "docs/old.md" in proc.stdout


def test_missing_scope_section_fails(repo, tmp_path):
    base = repo.commit("base")
    repo.write("src/a.py", "x\n")
    head = repo.commit()
    proc = check(repo, base, head, ticket(tmp_path))
    assert proc.returncode == 1
    assert "Scope" in proc.stdout and "To fix:" in proc.stdout
