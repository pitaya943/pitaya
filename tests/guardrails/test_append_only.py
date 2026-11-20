"""Recipe "append-only": listed files only gain lines in a PR."""

from helpers import run_check, ticket


def check(repo, base, head, files="CHANGELOG.md", ticket_path=None):
    args = ["--base", base, "--head", head, "--files", files]
    if ticket_path:
        args += ["--ticket", str(ticket_path)]
    return run_check("append-only", "check_append_only.py", *args, cwd=repo.path)


def test_added_lines_pass(repo):
    repo.write("CHANGELOG.md", "# Changelog\n\n- one\n")
    base = repo.commit("base")
    repo.write("CHANGELOG.md", "# Changelog\n\n- one\n- two\n")
    head = repo.commit()
    proc = check(repo, base, head)
    assert proc.returncode == 0, proc.stdout


def test_changed_line_fails(repo):
    repo.write("CHANGELOG.md", "# Changelog\n\n- one\n")
    base = repo.commit("base")
    repo.write("CHANGELOG.md", "# Changelog\n\n- ONE\n")
    head = repo.commit()
    proc = check(repo, base, head)
    assert proc.returncode == 1 and "- one" in proc.stdout and "To fix:" in proc.stdout


def test_removed_line_fails(repo):
    repo.write("CHANGELOG.md", "a\nb\n")
    base = repo.commit("base")
    repo.write("CHANGELOG.md", "a\n")
    head = repo.commit()
    assert check(repo, base, head).returncode == 1


def test_deleted_file_fails(repo):
    repo.write("CHANGELOG.md", "a\n")
    base = repo.commit("base")
    repo.remove("CHANGELOG.md")
    head = repo.commit()
    assert check(repo, base, head).returncode == 1


def test_new_file_and_untouched_files_pass(repo):
    base = repo.commit("base")
    repo.write("CHANGELOG.md", "new\n")
    repo.write("src/a.py", "x\n")
    head = repo.commit()
    assert check(repo, base, head).returncode == 0


def test_ticket_can_add_append_only_files(repo, tmp_path):
    repo.write("docs/log.md", "a\n")
    base = repo.commit("base")
    repo.write("docs/log.md", "b\n")
    head = repo.commit()
    t = ticket(tmp_path, Append_only_files=["docs/log.md"])
    assert check(repo, base, head, files="", ticket_path=t).returncode == 1


def test_a_line_inserted_inside_old_entries_fails(repo):
    # D43: append-only means additions after the last existing line, not inside old entries.
    repo.write("docs/decisions.md", "| D1 | old |\n| D2 | old |\n")
    base = repo.commit("base")
    repo.write("docs/decisions.md", "| D1 | old |\n| D1b | slipped in |\n| D2 | old |\n")
    head = repo.commit()
    proc = check(repo, base, head, files="docs/decisions.md")
    assert proc.returncode == 1 and "D1b" in proc.stdout and "To fix:" in proc.stdout
