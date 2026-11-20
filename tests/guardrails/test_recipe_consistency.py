"""Recipes that must agree with the rest of the harness (audit batch D, D43)."""

from __future__ import annotations

from helpers import FILES, PLUGIN_ROOT

GUARDRAILS = PLUGIN_ROOT / "docs" / "guardrails"


def test_progress_file_check_runs_on_every_pr():
    # A required check with a paths filter never reports on other PRs, so they wait forever.
    text = (FILES / "progress-file" / "progress-file.yml").read_text()
    assert "paths:" not in text
    assert "MACHINE_ACCOUNT" in text and "if: github.event.pull_request.user.login" not in text


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


# --- 0.1.9, F27: helpers copied between the checks stay one implementation ---

# Each check is one file a project copies on its own, so a helper several checks need is copied
# into each. These names are different functions that happen to share a name.
NOT_SHARED = {"main", "load"}


def copied_functions() -> dict[str, dict[str, str]]:
    """{function name: {check file: its source}} for every top-level function in the checks."""
    import ast
    out: dict[str, dict[str, str]] = {}
    for path in sorted(FILES.glob("*/*.py")):
        source = path.read_text()
        for node in ast.parse(source).body:
            if isinstance(node, ast.FunctionDef):
                out.setdefault(node.name, {})[path.name] = ast.get_source_segment(source, node)
    return out


def test_the_checks_share_helpers_at_all():
    shared = {name for name, copies in copied_functions().items() if len(copies) > 1} - NOT_SHARED
    assert {"ticket_section", "glob_to_regex", "changed_files"} <= shared


def test_helpers_copied_between_checks_are_identical():
    """A fix to one copy that doesn't reach the others is how `find_ticket` and the hooks' parser drifted."""
    for name, copies in copied_functions().items():
        if len(copies) > 1 and name not in NOT_SHARED:
            assert len(set(copies.values())) == 1, f"{name} differs between {', '.join(sorted(copies))}"


def test_serial_resources_reads_globs_like_scope_does(repo, tmp_path):
    """The drift this test found: the serial check's copy didn't know `?`, so `package?lock.json` matched nothing."""
    from helpers import run_check, ticket
    repo.write("a.txt", "a\n")
    base = repo.commit("base")
    repo.write("package-lock.json", "{}\n")
    head = repo.commit("lockfile")
    proc = run_check("serial-resources", "check_serial.py", "--ticket", str(ticket(tmp_path, scope=["**"])),
                     "--others", str(tmp_path / "none"), "--resources", "lockfile=package?lock.json",
                     "--base", base, "--head", head, cwd=repo.path)
    assert proc.returncode == 1 and "lockfile" in proc.stdout, proc.stdout
