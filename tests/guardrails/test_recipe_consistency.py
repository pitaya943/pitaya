"""Recipes that must agree with the rest of the harness (audit batch D, D43)."""

from __future__ import annotations

from helpers import FILES, PLUGIN_ROOT

GUARDRAILS = PLUGIN_ROOT / "docs" / "guardrails"


def test_progress_file_check_runs_on_every_pr():
    # A required check with a paths filter never reports on other PRs, so they wait forever.
    text = (FILES / "progress-file" / "progress-file.yml").read_text()
    assert "paths:" not in text
    assert "OWNER_ACCOUNTS" in text and "vars.MACHINE_ACCOUNT" not in text.split("jobs:")[1].split("steps:")[0]


def test_progress_files_live_outside_read_only_paths():
    for path in (FILES / "progress-file" / "progress-file.yml", GUARDRAILS / "progress-file.md"):
        text = path.read_text()
        assert "docs/progress/features.json" in text, path.name
        assert "docs/agents/features.json" not in text and "docs/agents/progress.md" not in text, path.name


def test_parallel_work_requires_up_to_date_branches():
    text = (GUARDRAILS / "protect-main.md").read_text()
    row = next(l for l in text.splitlines() if l.startswith("| Require branches to be up to date"))
    assert "Level 2" in row and "merge queue" in row


def test_serial_resources_workflow_maps_resources_to_paths():
    text = (FILES / "serial-resources" / "serial-resources.yml").read_text()
    assert "--resources" in text and "migrations=" in text


def test_autopilot_claims_a_ticket_before_starting_a_builder():
    text = (PLUGIN_ROOT / "skills" / "autopilot" / "tick.md").read_text()
    assert "Claim" in text and "ticket/<id>-<slug>" in text
