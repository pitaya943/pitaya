"""Recipe "done-when": every test ID the ticket lists exists in the PR's results and passes."""

from helpers import run_check, ticket
from test_no_weakened_tests import junit


def check(tmp_path, cases, ids):
    report = junit(tmp_path / "head.xml", cases)
    t = ticket(tmp_path, Test_IDs=ids) if ids is not None else ticket(tmp_path)
    return run_check("done-when", "check_done_when.py", "--junit", report, "--ticket", str(t))


def test_all_listed_tests_pass(tmp_path):
    proc = check(tmp_path, {"t::a": "pass", "t::b": "pass", "t::c": "pass"}, ["t::a", "t::b"])
    assert proc.returncode == 0, proc.stdout


def test_missing_test_fails(tmp_path):
    proc = check(tmp_path, {"t::a": "pass"}, ["t::a", "t::b"])
    assert proc.returncode == 1 and "t::b" in proc.stdout and "To fix:" in proc.stdout


def test_failing_or_skipped_test_fails(tmp_path):
    assert check(tmp_path, {"t::a": "fail"}, ["t::a"]).returncode == 1
    assert check(tmp_path, {"t::a": "skip"}, ["t::a"]).returncode == 1


def test_ticket_without_test_ids_fails(tmp_path):
    proc = check(tmp_path, {"t::a": "pass"}, None)
    assert proc.returncode == 1 and "Test IDs" in proc.stdout
