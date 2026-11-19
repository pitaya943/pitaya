"""Recipe "progress-file": agents may only flip "passes" in the feature list (Anthropic's long-running harness)."""

import json

from helpers import run_check


def features(path, items):
    path.write_text(json.dumps({"features": items}))
    return str(path)


F1 = {"id": "F-1", "description": "Split a bill", "steps": ["call split_bill"], "passes": False}
F2 = {"id": "F-2", "description": "Reject bad input", "steps": ["call with -1"], "passes": False}


def check(tmp_path, base, head):
    return run_check("progress-file", "check_feature_list.py",
                     "--base", features(tmp_path / "base.json", base),
                     "--head", features(tmp_path / "head.json", head))


def test_flipping_passes_is_allowed(tmp_path):
    proc = check(tmp_path, [F1, F2], [dict(F1, passes=True), F2])
    assert proc.returncode == 0, proc.stdout


def test_removing_a_feature_fails(tmp_path):
    proc = check(tmp_path, [F1, F2], [F1])
    assert proc.returncode == 1 and "F-2" in proc.stdout and "To fix:" in proc.stdout


def test_editing_a_description_fails(tmp_path):
    proc = check(tmp_path, [F1], [dict(F1, description="Split a bill, roughly")])
    assert proc.returncode == 1 and "description" in proc.stdout


def test_editing_steps_fails(tmp_path):
    assert check(tmp_path, [F1], [dict(F1, steps=[])]).returncode == 1


def test_adding_a_feature_fails(tmp_path):
    proc = check(tmp_path, [F1], [F1, F2])
    assert proc.returncode == 1 and "F-2" in proc.stdout


def test_reordering_is_fine(tmp_path):
    assert check(tmp_path, [F1, F2], [F2, F1]).returncode == 0


def test_unreadable_head_fails(tmp_path):
    base = features(tmp_path / "base.json", [F1])
    (tmp_path / "head.json").write_text("{not json")
    proc = run_check("progress-file", "check_feature_list.py", "--base", base, "--head", str(tmp_path / "head.json"))
    assert proc.returncode == 1 and "To fix:" in proc.stdout
