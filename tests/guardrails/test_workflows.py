"""The copyable workflows parse, and their shared "Find the ticket" step behaves as documented."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from helpers import FILES, Repo

WORKFLOWS = sorted(FILES.glob("*/*.yml"))


def steps(path: Path) -> list[dict]:
    """Minimal reader: the run block of each named step (no YAML library needed)."""
    text = path.read_text()
    out = []
    for match in re.finditer(r"^      - name: (.+?)\n(.*?)(?=^      - |\Z)", text, re.M | re.S):
        name, body = match.group(1), match.group(2)
        run = re.search(r"^        run: \|\n(.*)", body, re.M | re.S)
        out.append({"name": name, "run": "\n".join(l[10:] for l in run.group(1).splitlines()) if run else None})
    return out


def find_step(path: Path) -> str | None:
    for step in steps(path):
        if step["name"] == "Find the ticket":
            return step["run"]
    return None


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_workflow_job_is_named_after_its_recipe(path):
    recipe = path.parent.name
    text = path.read_text()
    assert f"name: {recipe}\n" in text and f"  {recipe}:\n    name: {recipe}\n" in text


def test_find_steps_are_identical():
    blocks = {p.name: find_step(p) for p in WORKFLOWS if find_step(p)}
    assert len(blocks) >= 6
    assert len(set(blocks.values())) == 1


def run_find(repo: Repo, tmp_path: Path, head_ref: str, author: str,
             **extra: str) -> tuple[subprocess.CompletedProcess, str]:
    script = find_step(FILES / "scope" / "scope.yml")
    output = tmp_path / "github_output"
    output.write_text("")
    env = dict(os.environ, HEAD_REF=head_ref, BASE_REF="main", PR_AUTHOR=author,
               MACHINE_ACCOUNT="example-bot", OWNER_ACCOUNTS="example-owner",
               GITHUB_OUTPUT=str(output), RUNNER_TEMP=str(tmp_path),
               GITHUB_REPOSITORY="example-owner/example", GH_TOKEN="")
    env.update(extra)
    proc = subprocess.run(["bash", "-c", script], cwd=repo.path, env=env, capture_output=True, text=True)
    return proc, output.read_text()


@pytest.fixture
def tickets_repo(repo):
    repo.write("docs/tickets/T-1.md", "## Scope\n\n- `src/**`\n")
    repo.commit("tickets")
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def test_ticket_file_is_read_from_the_base_branch(tickets_repo, tmp_path):
    tickets_repo.write("docs/tickets/T-1.md", "## Scope\n\n- `**`\n")  # edited on the PR branch
    tickets_repo.commit("widen my own scope")
    proc, out = run_find(tickets_repo, tmp_path, "ticket/T-1-thing", "example-bot")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skip=false" in out
    assert (tmp_path / "ticket.md").read_text() == "## Scope\n\n- `src/**`\n"


def test_owner_branch_without_ticket_is_skipped(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", "example-owner")
    assert proc.returncode == 0 and "skip=true" in out


def test_machine_account_branch_without_ticket_fails(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", "example-bot")
    assert proc.returncode == 1 and "To fix:" in proc.stdout


def test_find_step_reports_the_ticket_file(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "ticket/T-1-thing", "example-bot")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ticket_path=docs/tickets/T-1.md" in out


@pytest.mark.parametrize("recipe", ["scope", "read-only-paths"])
def test_ticket_path_is_passed_to_the_check(recipe):
    text = (FILES / recipe / f"{recipe}.yml").read_text()
    assert "TICKET_PATH: ${{ steps.ticket.outputs.ticket_path }}" in text
    assert '--ticket-path "$TICKET_PATH"' in text


# --- plan PRs: ticket files reach main through a plan/<slug> branch (D36) --------

def test_plan_branch_with_only_planning_files_is_skipped(tickets_repo, tmp_path):
    tickets_repo.write("docs/tickets/T-2.md", "# T-2\n\nStatus: open\n")
    tickets_repo.write("docs/agents/glossary.md", "| term |\n")
    tickets_repo.commit("plan")
    proc, out = run_find(tickets_repo, tmp_path, "plan/login", "example-bot")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skip=true" in out
    assert "plan PR" in proc.stdout


def test_plan_branch_that_changes_code_fails(tickets_repo, tmp_path):
    tickets_repo.write("docs/tickets/T-2.md", "# T-2\n")
    tickets_repo.write("src/app.py", "x = 1\n")
    tickets_repo.commit("plan with code")
    proc, out = run_find(tickets_repo, tmp_path, "plan/login", "example-bot")
    assert proc.returncode == 1
    assert "src/app.py" in proc.stdout and "To fix:" in proc.stdout
    assert "skip=true" not in out


def test_plan_branch_may_not_touch_other_docs(tickets_repo, tmp_path):
    tickets_repo.write("docs/agents/harness.md", "changed\n")
    tickets_repo.commit("plan touching the harness file")
    proc, _ = run_find(tickets_repo, tmp_path, "plan/x", "example-bot")
    assert proc.returncode == 1 and "docs/agents/harness.md" in proc.stdout


def test_plan_branch_may_add_milestone_files(tickets_repo, tmp_path):
    tickets_repo.write("docs/milestones/M1.md", "# M1\n\nStatus: active\n")
    tickets_repo.commit("roadmap")
    proc, out = run_find(tickets_repo, tmp_path, "plan/roadmap", "example-bot")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skip=true" in out


def test_step_outputs_never_go_inline_into_run_scripts():
    # A branch or file name can carry shell metacharacters; pass outputs through env (D40).
    for path in WORKFLOWS:
        for line in path.read_text().splitlines():
            if "${{ steps." in line:
                assert re.match(r"\s+[A-Z_]+: \$\{\{ steps\.", line) or line.strip().startswith("if:"), f"{path.name}: {line.strip()}"


# --- audit batch C (D41): who may skip, which ticket a PR may claim --------------

def test_an_owner_account_is_matched_case_insensitively(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", "Example-Owner", OWNER_ACCOUNTS="other, example-owner")
    assert proc.returncode == 0 and "skip=true" in out


@pytest.mark.parametrize("author", ["example-verifier", "someone-else"])
def test_any_other_account_on_a_non_ticket_branch_fails(tickets_repo, tmp_path, author):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", author)
    assert proc.returncode == 1 and "To fix:" in proc.stdout
    assert "skip=true" not in out


def test_without_owner_accounts_the_step_fails_closed(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", "example-owner", OWNER_ACCOUNTS="")
    assert proc.returncode == 1 and "OWNER_ACCOUNTS" in proc.stdout
    assert "skip=true" not in out


def test_file_tickets_never_fall_back_to_issues(tickets_repo, tmp_path):
    # With docs/tickets/ on the base branch, an issue an agent opened can't stand in for a ticket.
    proc, out = run_find(tickets_repo, tmp_path, "ticket/57-anything", "example-bot", PATH=stub_gh(tmp_path))
    assert proc.returncode == 1 and "To fix:" in proc.stdout
    assert "skip=false" not in out


def test_a_ticket_file_added_by_the_pr_does_not_count(tickets_repo, tmp_path):
    tickets_repo.write("docs/tickets/T-9.md", "## Scope\n\n- `**`\n")
    tickets_repo.commit("my own ticket")
    proc, out = run_find(tickets_repo, tmp_path, "ticket/T-9-wide", "example-bot")
    assert proc.returncode == 1 and "skip=false" not in out


def test_a_done_ticket_cannot_be_claimed(repo, tmp_path):
    repo.write("docs/tickets/T-2.md", "# T-2\n\nStatus: done\n\n## Scope\n\n- `**`\n")
    repo.commit("tickets")
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    proc, out = run_find(repo, tmp_path, "ticket/T-2-again", "example-bot")
    assert proc.returncode == 1 and "done" in proc.stdout and "To fix:" in proc.stdout


def stub_gh(tmp_path: Path, pr_list: str = "", issue_body: str = "## Scope\\n\\n- `**`",
            issue_state: str = "OPEN") -> str:
    """A fake gh on PATH: `pr list` prints branch names, `issue view` an issue's state or body."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(
        "#!/bin/sh\n"
        f"case \"$1 $2\" in\n"
        f"  'pr list') printf '%s' '{pr_list}' ;;\n"
        f"  'issue view') case \"$*\" in *state*) echo '{issue_state}' ;; *) printf '{issue_body}\\n' ;; esac ;;\n"
        "esac\n")
    gh.chmod(0o755)
    return f"{bin_dir}{os.pathsep}{os.environ['PATH']}"


def test_a_ticket_another_open_pr_works_on_cannot_be_claimed(tickets_repo, tmp_path):
    path = stub_gh(tmp_path, pr_list="ticket/T-1-first")
    proc, out = run_find(tickets_repo, tmp_path, "ticket/T-1-second", "example-bot", PATH=path, PR_NUMBER="8")
    assert proc.returncode == 1 and "ticket/T-1-first" in proc.stdout


def test_the_only_pr_on_a_ticket_passes_the_claim_check(tickets_repo, tmp_path):
    path = stub_gh(tmp_path)
    proc, out = run_find(tickets_repo, tmp_path, "ticket/T-1-thing", "example-bot", PATH=path, PR_NUMBER="8")
    assert proc.returncode == 0 and "skip=false" in out


def test_commit_author_runs_for_every_pr_but_the_owners():
    text = (FILES / "commit-author" / "commit-author.yml").read_text()
    assert "OWNER_ACCOUNTS" in text
    assert "if: github.event.pull_request.user.login == vars.MACHINE_ACCOUNT" not in text


def test_issue_tickets_must_be_open(repo, tmp_path):
    repo.commit("no ticket files")
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    proc, out = run_find(repo, tmp_path, "ticket/12-x", "example-bot", PATH=stub_gh(tmp_path, issue_state="CLOSED"))
    assert proc.returncode == 1 and "CLOSED" in proc.stdout


def test_open_issue_tickets_still_work(repo, tmp_path):
    repo.commit("no ticket files")
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    proc, out = run_find(repo, tmp_path, "ticket/12-x", "example-bot", PATH=stub_gh(tmp_path))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skip=false" in out and "Scope" in (tmp_path / "ticket.md").read_text()
