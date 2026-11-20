"""Recipe "serial-resources": only one open ticket at a time changes a given shared resource."""

from helpers import run_check, ticket


def other(directory, name, resources):
    directory.mkdir(exist_ok=True)
    body = "## Goal\n\nOther.\n\n## Serial resources\n\n" + "".join(f"- `{r}`\n" for r in resources)
    (directory / f"{name}.md").write_text(body)


def check(tmp_path, mine, others_dir, known="migrations,lockfile"):  # names only, no paths
    t = ticket(tmp_path, Serial_resources=mine) if mine is not None else ticket(tmp_path)
    return run_check("serial-resources", "check_serial.py", "--ticket", str(t),
                     "--others", str(others_dir), "--known", known)


def test_no_overlap_passes(tmp_path):
    others = tmp_path / "others"
    other(others, "pr-7", ["lockfile"])
    proc = check(tmp_path, ["migrations"], others)
    assert proc.returncode == 0, proc.stdout


def test_overlap_with_another_open_ticket_fails(tmp_path):
    others = tmp_path / "others"
    other(others, "pr-7", ["migrations"])
    proc = check(tmp_path, ["migrations"], others)
    assert proc.returncode == 1 and "pr-7" in proc.stdout and "To fix:" in proc.stdout


def test_unknown_resource_fails(tmp_path):
    proc = check(tmp_path, ["database"], tmp_path / "none")
    assert proc.returncode == 1 and "database" in proc.stdout


def test_ticket_without_serial_resources_passes(tmp_path):
    others = tmp_path / "others"
    other(others, "pr-7", ["migrations"])
    assert check(tmp_path, None, others).returncode == 0


def test_missing_others_directory_means_no_other_tickets(tmp_path):
    assert check(tmp_path, ["migrations"], tmp_path / "missing").returncode == 0


# --- D43: resources are detected from the diff, not only declared -----------------

def diff_check(repo, tmp_path, mine, resources="migrations=migrations/**;lockfile=poetry.lock"):
    base = repo.commit("base")
    repo.write("migrations/0002_add.sql", "ALTER TABLE x;\n")
    head = repo.commit()
    t = ticket(tmp_path, Serial_resources=mine) if mine else ticket(tmp_path)
    return run_check("serial-resources", "check_serial.py", "--ticket", str(t),
                     "--others", str(tmp_path / "none"), "--resources", resources,
                     "--base", base, "--head", head, cwd=repo.path)


def test_touching_an_undeclared_resource_fails(repo, tmp_path):
    proc = diff_check(repo, tmp_path, None)
    assert proc.returncode == 1 and "migrations" in proc.stdout and "To fix:" in proc.stdout


def test_touching_a_declared_resource_passes(repo, tmp_path):
    proc = diff_check(repo, tmp_path, ["migrations"])
    assert proc.returncode == 0, proc.stdout


def test_resource_names_come_from_the_mapping(repo, tmp_path):
    proc = diff_check(repo, tmp_path, ["schema"])
    assert proc.returncode == 1 and "unknown" in proc.stdout
