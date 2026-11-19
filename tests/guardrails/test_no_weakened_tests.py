"""Recipe "no-weakened-tests": every test passing on the base exists and passes on the PR (JUnit comparison)."""

from helpers import run_check, ticket


def junit(path, cases):
    """cases: {"cls::name": "pass" | "fail" | "skip"}"""
    rows = []
    for test_id, status in cases.items():
        cls, name = test_id.split("::")
        inner = {"pass": "", "fail": "<failure message='x'/>", "skip": "<skipped/>"}[status]
        rows.append(f'<testcase classname="{cls}" name="{name}">{inner}</testcase>')
    path.write_text("<testsuites><testsuite>" + "".join(rows) + "</testsuite></testsuites>")
    return str(path)


def check(tmp_path, base_cases, head_cases, *extra):
    base = junit(tmp_path / "base.xml", base_cases)
    head = junit(tmp_path / "head.xml", head_cases)
    return run_check("no-weakened-tests", "compare_junit.py", "--base", base, "--head", head, *extra)


def test_same_or_more_tests_pass(tmp_path):
    proc = check(tmp_path, {"t::a": "pass", "t::b": "pass"}, {"t::a": "pass", "t::b": "pass", "t::c": "pass"})
    assert proc.returncode == 0, proc.stdout


def test_removed_test_fails(tmp_path):
    proc = check(tmp_path, {"t::a": "pass", "t::b": "pass"}, {"t::a": "pass"})
    assert proc.returncode == 1 and "t::b" in proc.stdout and "To fix:" in proc.stdout


def test_newly_failing_test_fails(tmp_path):
    assert check(tmp_path, {"t::a": "pass"}, {"t::a": "fail"}).returncode == 1


def test_newly_skipped_test_fails(tmp_path):
    assert check(tmp_path, {"t::a": "pass"}, {"t::a": "skip"}).returncode == 1


def test_tests_that_already_failed_on_base_are_not_required(tmp_path):
    assert check(tmp_path, {"t::a": "fail"}, {}).returncode == 0


def test_rename_listed_in_the_ticket_is_allowed(tmp_path):
    t = ticket(tmp_path, Test_renames=["t::old -> t::new"])
    proc = check(tmp_path, {"t::old": "pass"}, {"t::new": "pass"}, "--ticket", str(t))
    assert proc.returncode == 0, proc.stdout


def test_rename_target_must_pass(tmp_path):
    t = ticket(tmp_path, Test_renames=["t::old -> t::new"])
    assert check(tmp_path, {"t::old": "pass"}, {"t::new": "fail"}, "--ticket", str(t)).returncode == 1


def test_unreadable_head_report_fails(tmp_path):
    base = junit(tmp_path / "base.xml", {"t::a": "pass"})
    (tmp_path / "head.xml").write_text("<not xml")
    proc = run_check("no-weakened-tests", "compare_junit.py", "--base", base, "--head", str(tmp_path / "head.xml"))
    assert proc.returncode == 1 and "To fix:" in proc.stdout


def test_missing_head_report_fails(tmp_path):
    base = junit(tmp_path / "base.xml", {"t::a": "pass"})
    proc = run_check("no-weakened-tests", "compare_junit.py", "--base", base, "--head", str(tmp_path / "nope.xml"))
    assert proc.returncode == 1
