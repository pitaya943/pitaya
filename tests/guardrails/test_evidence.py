"""Recipe "evidence": the PR description has evidence, and screenshots when the ticket requires them."""

from helpers import run_check, ticket

FENCE = "`" * 3


def body(tmp_path, text):
    path = tmp_path / "body.md"
    path.write_text(text)
    return str(path)


def check(repo, tmp_path, pr_body, screenshots=None, base=None, head=None):
    t = ticket(tmp_path, Screenshots=[screenshots]) if screenshots else ticket(tmp_path)
    base = base or repo.commit("base")
    head = head or base
    return run_check("evidence", "check_evidence.py", "--pr-body", body(tmp_path, pr_body),
                     "--ticket", str(t), "--base", base, "--head", head, cwd=repo.path)


def test_code_block_counts_as_evidence(repo, tmp_path):
    text = f"## What\n\nx\n\n## Evidence\n\n{FENCE}text\n$ pytest -q\n3 passed\n{FENCE}\n"
    proc = check(repo, tmp_path, text)
    assert proc.returncode == 0, proc.stdout


def test_link_counts_as_evidence(repo, tmp_path):
    assert check(repo, tmp_path, "## Evidence\n\nSee [the CI run](https://example.com/run/1).\n").returncode == 0


def test_missing_section_fails(repo, tmp_path):
    proc = check(repo, tmp_path, "## What\n\nTrust me, it works.\n")
    assert proc.returncode == 1 and "## Evidence" in proc.stdout and "To fix:" in proc.stdout


def test_section_without_proof_fails(repo, tmp_path):
    assert check(repo, tmp_path, "## Evidence\n\nI ran the tests and they passed.\n").returncode == 1


def test_required_screenshot_missing_fails(repo, tmp_path):
    text = f"## Evidence\n\n{FENCE}\nok\n{FENCE}\n"
    proc = check(repo, tmp_path, text, screenshots="required")
    assert proc.returncode == 1 and "screenshot" in proc.stdout.lower()


def test_required_screenshot_as_image_link_passes(repo, tmp_path):
    text = "## Evidence\n\n![login page](https://example.com/shot.png)\n"
    assert check(repo, tmp_path, text, screenshots="required").returncode == 0


def test_required_screenshot_as_committed_file_passes(repo, tmp_path):
    base = repo.commit("base")
    repo.write("docs/evidence/12/login.png", "png")
    head = repo.commit()
    text = f"## Evidence\n\n{FENCE}\nok\n{FENCE}\n"
    assert check(repo, tmp_path, text, screenshots="required", base=base, head=head).returncode == 0


def test_not_required_means_no_screenshot_needed(repo, tmp_path):
    text = f"## Evidence\n\n{FENCE}\nok\n{FENCE}\n"
    assert check(repo, tmp_path, text, screenshots="not required").returncode == 0
