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


# --- a requirement change the Owner already merged isn't the agent's (review finding N02, D61) ---

def check_owner(tmp_path, base, head, owner):
    return run_check("progress-file", "check_feature_list.py",
                     "--base", features(tmp_path / "base.json", base),
                     "--head", features(tmp_path / "head.json", head),
                     "--owner", features(tmp_path / "owner.json", owner))


F1_NEW = dict(F1, description="Split a bill in whole cents")


def test_a_change_identical_to_the_default_branch_passes(tmp_path):
    """A sync PR brings the Owner's edit of F-1 and new F-2 into a milestone that marked F-1 as passing."""
    base = [dict(F1, passes=True)]
    proc = check_owner(tmp_path, base, [dict(F1_NEW, passes=True), F2], [F1_NEW, F2])
    assert proc.returncode == 0, proc.stdout


def test_a_removal_the_default_branch_also_made_passes(tmp_path):
    assert check_owner(tmp_path, [F1, F2], [F1], [F1]).returncode == 0


def test_a_change_that_differs_from_the_default_branch_too_fails(tmp_path):
    proc = check_owner(tmp_path, [F1], [dict(F1, description="Split a bill, roughly")], [F1_NEW])
    assert proc.returncode == 1 and "description" in proc.stdout


def test_a_feature_the_default_branch_does_not_have_cannot_be_added(tmp_path):
    assert check_owner(tmp_path, [F1], [F1, F2], [F1]).returncode == 1


def test_a_feature_the_default_branch_still_has_cannot_be_removed(tmp_path):
    assert check_owner(tmp_path, [F1, F2], [F1], [F1, F2]).returncode == 1
