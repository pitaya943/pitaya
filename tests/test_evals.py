"""The harness's own eval set: each task has a starting state, a ticket and a grading sheet (D17)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS = REPO_ROOT / "evals"
TASKS = sorted(p for p in (EVALS / "tasks").iterdir() if p.is_dir()) if (EVALS / "tasks").is_dir() else []


def test_there_is_at_least_one_task():
    assert TASKS


@pytest.mark.parametrize("task", TASKS, ids=lambda p: p.name)
def test_task_has_its_parts(task):
    for name in ("task.md", "ticket.md", "grading.md"):
        assert (task / name).is_file(), name


@pytest.mark.parametrize("task", TASKS, ids=lambda p: p.name)
def test_grading_is_a_checklist_of_observable_outcomes(task):
    lines = [l for l in (task / "grading.md").read_text().splitlines() if l.startswith("- [ ]")]
    assert len(lines) >= 3


def test_results_log_has_a_row_format():
    text = (EVALS / "results.md").read_text()
    assert "| Date | Task | Harness version | Model | Score | Notes |" in text


def test_readme_explains_how_to_run():
    text = (EVALS / "README.md").read_text()
    for word in ("before", "after", "transcript"):
        assert word in text.lower(), word
