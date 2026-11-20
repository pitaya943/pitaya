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
               MACHINE_ACCOUNT="example-bot",
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


RUN_BLOCK = re.compile(r"^(\s+)run: (?:\||>-)\n((?:\1  .*\n|\s*\n)*)", re.M)


def test_step_and_job_outputs_never_go_inline_into_run_scripts():
    # A branch or file name can carry shell metacharacters; pass outputs through env (D40).
    for path in WORKFLOWS:
        text = path.read_text()
        for match in RUN_BLOCK.finditer(text):
            for ref in ("${{ steps.", "${{ needs."):
                assert ref not in match.group(2), f"{path.name}: {match.group(2).strip()[:80]}"
        for line in text.splitlines():
            if line.strip().startswith("run:") and ("${{ steps." in line or "${{ needs." in line):
                raise AssertionError(f"{path.name}: {line.strip()}")


# --- D41/D44: who the checks apply to, which ticket a PR may claim ---------------
# One machine account (D44): MACHINE_ACCOUNT (comma separated for several agent
# accounts) names the agents; their PRs must name an open ticket. Anyone else is a
# person, whose PRs are reviewed by people.

def test_the_machine_account_is_matched_case_insensitively(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", "Example-Bot")
    assert proc.returncode == 1 and "To fix:" in proc.stdout


@pytest.mark.parametrize("agents", ["example-verifier, example-bot", "EXAMPLE-BOT"])
def test_every_listed_agent_account_must_use_a_ticket(tickets_repo, tmp_path, agents):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", "example-bot", MACHINE_ACCOUNT=agents)
    assert proc.returncode == 1 and "skip=true" not in out


def test_a_person_on_a_non_ticket_branch_is_skipped(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", "someone-else")
    assert proc.returncode == 0 and "skip=true" in out


def test_without_machine_account_the_step_fails_closed(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "fix/typo", "example-owner", MACHINE_ACCOUNT="")
    assert proc.returncode == 1 and "MACHINE_ACCOUNT" in proc.stdout
    assert "skip=true" not in out


def test_a_milestone_pr_is_left_to_the_owner(tickets_repo, tmp_path):
    proc, out = run_find(tickets_repo, tmp_path, "milestone/M2", "example-bot")
    assert proc.returncode == 0 and "skip=true" in out and "milestone" in proc.stdout.lower()


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


def test_commit_author_checks_every_agent_pr_and_matches_case_insensitively():
    text = (FILES / "commit-author" / "commit-author.yml").read_text()
    assert "OWNER_ACCOUNTS" not in text
    assert "if: github.event.pull_request.user.login == vars.MACHINE_ACCOUNT" not in text
    assert "tr '[:upper:]' '[:lower:]'" in text


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


# --- audit batch B (D42): the PR never runs or rewrites the checks that judge it --

def jobs(path: Path) -> dict[str, str]:
    text = path.read_text().split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([\w-]+):\n", text, flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_checks_are_loaded_from_the_base_branch(path):
    text = path.read_text()
    if "guardrails/" not in text.split("\njobs:\n", 1)[1]:
        return
    for name, body in jobs(path).items():
        if "python3 .github/guardrails/" in body:
            # allowed only in a job that checks out nothing but the base commit
            assert "ref: ${{ github.event.pull_request.base.sha" in body, f"{name}: run the base branch's copy of the check"
    for name, body in jobs(path).items():
        if '"$RUNNER_TEMP/guardrails/' in body:
            assert "Load the checks from the base branch" in body, name


def test_load_step_prefers_the_base_copy(tickets_repo, tmp_path):
    tickets_repo.write(".github/guardrails/check_scope.py", "print('base')\n")
    tickets_repo.commit("install the check")
    tickets_repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    tickets_repo.write(".github/guardrails/check_scope.py", "print('rewritten by the PR')\n")
    tickets_repo.commit("weaken the check")
    script = next(s["run"] for s in steps(FILES / "scope" / "scope.yml") if s["name"] == "Load the checks from the base branch")
    env = dict(os.environ, BASE_REF="main", RUNNER_TEMP=str(tmp_path))
    proc = subprocess.run(["bash", "-c", script], cwd=tickets_repo.path, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "guardrails" / "check_scope.py").read_text() == "print('base')\n"


@pytest.mark.parametrize("recipe", ["no-weakened-tests", "done-when"])
def test_pr_tests_never_share_a_job_with_the_comparison(recipe):
    for name, body in jobs(FILES / recipe / f"{recipe}.yml").items():
        runs_pr_tests = '$TEST_COMMAND' in body and "base.sha" not in body.split("$TEST_COMMAND")[0][-400:]
        if runs_pr_tests:
            assert "guardrails/" not in body, f"job {name} runs the PR's tests and a check"


def test_agent_merge_runs_in_the_base_context_on_reviews():
    text = (FILES / "agent-merge" / "agent-merge.yml").read_text()
    assert "pull_request_target:" in text and "pull_request_review:" in text
    assert "\n  pull_request:" not in text  # never the PR's own copy of the workflow
    assert "ref: ${{ github.event.pull_request.base.sha || github.event.repository.default_branch }}" in text


# --- sync PRs: bring main into a milestone branch (P14, D58) ------------------------

@pytest.fixture
def milestone_repo(repo):
    """main and milestone/M1 have each moved on since the milestone started."""
    repo.write("docs/tickets/T-1.md", "## Scope\n\n- `src/**`\n")
    repo.commit("start")
    repo.git("checkout", "-q", "-b", "milestone/M1")
    repo.write("src/ticket.py", "done = True\n")
    repo.commit("a ticket merged into the milestone")
    repo.git("checkout", "-q", "main")
    repo.write("docs/tickets/T-2.md", "## Scope\n\n- `src/**`\n")
    repo.commit("a plan PR merged into main")
    repo.git("update-ref", "refs/remotes/origin/main", "main")
    repo.git("update-ref", "refs/remotes/origin/milestone/M1", "milestone/M1")
    repo.git("checkout", "-q", "-b", "sync/M1-main", "milestone/M1")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "main")
    return repo


SYNC = dict(BASE_REF="milestone/M1", DEFAULT_BRANCH="main")


def test_sync_pr_that_only_merges_main_is_skipped(milestone_repo, tmp_path):
    proc, out = run_find(milestone_repo, tmp_path, "sync/M1-main", "example-bot", **SYNC)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skip=true" in out and "sync PR" in proc.stdout


def test_sync_pr_that_adds_anything_else_fails(milestone_repo, tmp_path):
    milestone_repo.write("src/ticket.py", "done = False  # slipped in with the sync\n")
    milestone_repo.commit("an unreviewed change")
    proc, out = run_find(milestone_repo, tmp_path, "sync/M1-main", "example-bot", **SYNC)
    assert proc.returncode == 1 and "To fix:" in proc.stdout
    assert "skip=true" not in out


def test_sync_pr_with_a_change_hidden_in_the_merge_commit_fails(milestone_repo, tmp_path):
    milestone_repo.write("src/ticket.py", "done = 'amended'\n")
    milestone_repo.git("add", "-A")
    milestone_repo.git("commit", "-q", "--amend", "--no-edit")
    proc, out = run_find(milestone_repo, tmp_path, "sync/M1-main", "example-bot", **SYNC)
    assert proc.returncode == 1 and "skip=true" not in out


def test_sync_branch_into_main_is_not_a_sync_pr(milestone_repo, tmp_path):
    proc, out = run_find(milestone_repo, tmp_path, "sync/M1-main", "example-bot",
                         BASE_REF="main", DEFAULT_BRANCH="main")
    assert proc.returncode == 1 and "skip=true" not in out


# --- the sync proof covers history, not only the tree (review finding N01, D61) -----

def test_sync_pr_with_an_ours_merge_of_an_unmerged_commit_fails(milestone_repo, tmp_path):
    """`git merge -s ours` keeps the tree but records the commit as merged; main's later copy would be dropped."""
    repo = milestone_repo
    repo.git("checkout", "-q", "-b", "owner/correction", "main")
    repo.write("docs/tickets/T-2.md", "## Scope\n\n- `src/narrow/**`\n")
    repo.commit("a correction the Owner hasn't merged yet")
    repo.git("checkout", "-q", "sync/M1-main")
    repo.git("merge", "-q", "-s", "ours", "--no-edit", "owner/correction")
    proc, out = run_find(repo, tmp_path, "sync/M1-main", "example-bot", **SYNC)
    assert proc.returncode == 1 and "To fix:" in proc.stdout, proc.stdout + proc.stderr
    assert "skip=true" not in out


def test_sync_pr_updated_with_its_milestone_is_still_skipped(milestone_repo, tmp_path):
    repo = milestone_repo
    repo.git("checkout", "-q", "milestone/M1")
    repo.write("src/other.py", "other = True\n")
    repo.commit("another ticket merged into the milestone")
    repo.git("update-ref", "refs/remotes/origin/milestone/M1", "milestone/M1")
    repo.git("checkout", "-q", "sync/M1-main")
    repo.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")  # "Update branch"
    proc, out = run_find(repo, tmp_path, "sync/M1-main", "example-bot", **SYNC)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skip=true" in out


# --- an unset MACHINE_ACCOUNT fails every check that needs it (review finding F13, D61) ---

def run_step(recipe: str, name: str, tmp_path: Path, cwd: Path, **env: str) -> subprocess.CompletedProcess:
    script = next(s["run"] for s in steps(FILES / recipe / f"{recipe}.yml") if s["name"] == name)
    output = tmp_path / "github_output"
    output.write_text("")
    full = dict(os.environ, GITHUB_OUTPUT=str(output), RUNNER_TEMP=str(tmp_path), **env)
    return subprocess.run(["bash", "-c", script], cwd=cwd, env=full, capture_output=True, text=True)


@pytest.mark.parametrize("recipe, step", [("commit-author", "Who opened it"),
                                          ("progress-file", "Check the feature list")])
def test_checks_outside_the_find_step_fail_closed_without_machine_account(recipe, step, repo, tmp_path):
    repo.commit("start")
    proc = run_step(recipe, step, tmp_path, repo.path, MACHINE_ACCOUNT="", PR_AUTHOR="example-bot", BASE_REF="main")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "MACHINE_ACCOUNT" in proc.stdout and "To fix:" in proc.stdout


def test_commit_author_and_progress_file_know_the_default_branch():
    author = (FILES / "commit-author" / "commit-author.yml").read_text()
    assert '--default "origin/$DEFAULT_BRANCH"' in author and "--git-dir ." in author
    progress = (FILES / "progress-file" / "progress-file.yml").read_text()
    assert "origin/$DEFAULT_BRANCH:docs/progress/features.json" in progress and "--owner" in progress
