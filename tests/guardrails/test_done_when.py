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


# P10 (W8): IDs written as pytest paths, and parametrized tests, must match what JUnit reports.

def test_pytest_path_ids_match_junit_classnames(tmp_path):
    cases = {"tests.test_cli::test_a": "pass", "tests.sub.test_x.TestC::test_b": "pass"}
    ids = ["tests/test_cli.py::test_a", "tests/sub/test_x.py::TestC::test_b"]
    proc = check(tmp_path, cases, ids)
    assert proc.returncode == 0, proc.stdout


def test_an_id_without_parameters_needs_every_case_to_pass(tmp_path):
    passing = {"t::a[1]": "pass", "t::a[2-x]": "pass"}
    assert check(tmp_path, passing, ["t::a"]).returncode == 0
    proc = check(tmp_path, {"t::a[1]": "pass", "t::a[2]": "fail"}, ["t::a"])
    assert proc.returncode == 1 and "t::a[2]: failed" in proc.stdout


def test_a_parametrized_id_still_matches_one_case_exactly(tmp_path):
    assert check(tmp_path, {"t::a[1]": "pass", "t::a[2]": "fail"}, ["t::a[1]"]).returncode == 0


def test_a_name_prefix_is_not_a_parametrized_match(tmp_path):
    proc = check(tmp_path, {"t::a_longer": "pass"}, ["t::a"])
    assert proc.returncode == 1 and "t::a: missing" in proc.stdout
