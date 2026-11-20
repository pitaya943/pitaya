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
               MACHINE_ACCOUNT="example-bot", DEFAULT_BRANCH="main",
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


# --- agent-merge: the workflow records each FAIL and reads it back (F02, F20; D63) ---------
#
# The step runs against a fake `gh` that serves the pull request, its comments and the commit
# statuses from files, and appends every status the step writes. Git is real.

import json  # noqa: E402
import shutil  # noqa: E402
import sys  # noqa: E402

FAKE_GH = r'''#!/usr/bin/env python3
import json, os, subprocess, sys
state = os.environ["FAKE_GH_STATE"]
args = sys.argv[1:]
if args[:2] == ["issue", "view"]:
    print(open(os.path.join(state, "issue.md")).read(), end="")
    sys.exit(0)
assert args[0] == "api", args
path = args[1].split("/", 3)[3]  # after repos/<owner>/<repo>/
fields = dict(a.split("=", 1) for i, a in enumerate(args) if i and args[i - 1] == "-f")
jq = args[args.index("--jq") + 1] if "--jq" in args else None
statuses_file = os.path.join(state, "statuses.json")
statuses = json.load(open(statuses_file))
if path.startswith("statuses/"):
    statuses.setdefault(path.split("/")[1], []).insert(0, dict(fields, id=sum(map(len, statuses.values())) + 1))
    json.dump(statuses, open(statuses_file, "w"))
    sys.exit(0)
if path.startswith("commits/") and path.endswith("/statuses"):
    if os.environ.get("FAKE_GH_BREAK_STATUSES"):
        sys.exit(1)
    data = statuses.get(path.split("/")[1], [])
else:
    data = json.load(open(os.path.join(state, path.replace("/", "_") + ".json")))
out = json.dumps(data)
if jq:
    out = subprocess.run(["jq", "-c", jq], input=out, capture_output=True, text=True, check=True).stdout
print(out, end="" if out.endswith("\n") else "\n")
'''


class VerdictRun:
    """A clone with the base checked out, as the workflow has it, and the fake GitHub's state."""

    def __init__(self, tmp_path: Path, ticket: str = ""):
        (tmp_path / "origin").mkdir()
        origin = Repo(tmp_path / "origin")
        origin.write("app.py", "x = 1\n")
        if ticket:
            origin.write("docs/tickets/T-1.md", ticket)
        origin.commit("start")
        origin.git("checkout", "-q", "-b", "milestone/M1")
        origin.git("checkout", "-q", "-b", "ticket/T-1-a")
        origin.write("a.py", "a = 1\n")
        self.head = origin.commit("the ticket")
        origin.git("update-ref", "refs/pull/7/head", self.head)
        origin.git("checkout", "-q", "main")
        self.origin = origin
        self.work = tmp_path / "work"
        subprocess.run(["git", "clone", "-q", str(origin.path), str(self.work)], check=True, capture_output=True)
        guard = self.work / ".github" / "guardrails"
        guard.mkdir(parents=True)
        shutil.copy(FILES / "agent-merge" / "check_verdict.py", guard)
        self.state = tmp_path / "state"
        self.state.mkdir()
        self.tmp = tmp_path
        (self.state / "statuses.json").write_text("{}")
        self.put("pulls_7", {"head": {"sha": self.head, "ref": "ticket/T-1-a"}, "base": {"ref": "milestone/M1"}})
        self.put("issues_7_comments", [])
        self.put("pulls_7_reviews", [])
        bin_dir = tmp_path / "fakebin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text(FAKE_GH.replace("#!/usr/bin/env python3", f"#!{sys.executable}"))
        (bin_dir / "gh").chmod(0o755)
        self.path = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"

    def put(self, name: str, data) -> None:
        (self.state / f"{name}.json").write_text(json.dumps(data))

    def comments(self, *comments: dict) -> None:
        self.put("issues_7_comments", list(comments))

    def verdict(self, result: str, sha: str | None = None, session: str = "verifier-1") -> dict:
        stamp = "2026-11-20T10:00:00Z"
        return {"user": {"login": "example-bot"}, "created_at": stamp, "updated_at": stamp,
                "body": f"## Verification: {result}\n\n- Session: {session}\n- Head commit: {sha or self.head}\n"}

    def run(self, **env: str) -> subprocess.CompletedProcess:
        return run_step("agent-merge", "Check the verdict and set the status on the head commit", self.tmp, self.work,
                        PATH=self.path, FAKE_GH_STATE=str(self.state), GH_TOKEN="", PR="7", VERIFIERS="example-bot",
                        DEFAULT_BRANCH="main", GITHUB_REPOSITORY="example-owner/example", **env)

    def statuses(self, sha: str | None = None, context: str = "verdict") -> list[str]:
        """The states written for a context on a commit, newest first."""
        data = json.loads((self.state / "statuses.json").read_text())
        return [s["state"] for s in data.get(sha or self.head, []) if s["context"] == context]


@pytest.fixture
def verdict_run(tmp_path):
    return VerdictRun(tmp_path)


def test_agent_merge_sets_success_on_a_pass(verdict_run):
    verdict_run.comments(verdict_run.verdict("PASS"))
    proc = verdict_run.run()
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert verdict_run.statuses() == ["success"]
    assert verdict_run.statuses(context="verdict-fail") == []


def test_agent_merge_records_a_fail_on_its_commit(verdict_run):
    verdict_run.comments(verdict_run.verdict("FAIL"))
    verdict_run.run()
    assert verdict_run.statuses() == ["failure"]
    assert verdict_run.statuses(context="verdict-fail") == ["failure"]


def test_a_deleted_fail_still_blocks_the_head(verdict_run):
    """F02: the verifier's account deletes the FAIL comment and posts a PASS on the same head."""
    verdict_run.comments(verdict_run.verdict("FAIL"))
    verdict_run.run()
    verdict_run.comments(verdict_run.verdict("PASS"))  # the FAIL comment is gone
    proc = verdict_run.run()
    assert verdict_run.statuses()[0] == "failure", proc.stdout + proc.stderr
    assert "recorded" in proc.stdout


def test_a_fail_is_recorded_once(verdict_run):
    verdict_run.comments(verdict_run.verdict("FAIL"))
    verdict_run.run()
    verdict_run.run()
    assert verdict_run.statuses(context="verdict-fail") == ["failure"]


def test_a_deleted_fail_on_a_passed_head_stops_the_carry(verdict_run):
    """PASS and FAIL on the same head, the FAIL deleted, then "Update branch": the PASS must not carry."""
    run = verdict_run
    passed = run.head
    run.comments(run.verdict("PASS"), run.verdict("FAIL"))
    run.run()
    origin = run.origin
    origin.git("checkout", "-q", "milestone/M1")
    origin.write("b.py", "b = 1\n")
    origin.commit("another ticket merged")
    origin.git("checkout", "-q", "ticket/T-1-a")
    origin.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")
    run.head = origin.git("rev-parse", "HEAD")
    origin.git("update-ref", "refs/pull/7/head", run.head)
    origin.git("checkout", "-q", "main")
    run.put("pulls_7", {"head": {"sha": run.head, "ref": "ticket/T-1-a"}, "base": {"ref": "milestone/M1"}})
    run.comments(run.verdict("PASS", sha=passed))  # the FAIL comment is gone
    proc = run.run()
    assert run.statuses() == ["failure"], proc.stdout + proc.stderr


def test_the_same_carry_passes_without_the_fail(verdict_run):
    """The control for the test above: without the recorded FAIL the PASS carries."""
    run = verdict_run
    passed = run.head
    origin = run.origin
    origin.git("checkout", "-q", "milestone/M1")
    origin.write("b.py", "b = 1\n")
    origin.commit("another ticket merged")
    origin.git("checkout", "-q", "ticket/T-1-a")
    origin.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")
    run.head = origin.git("rev-parse", "HEAD")
    origin.git("update-ref", "refs/pull/7/head", run.head)
    origin.git("checkout", "-q", "main")
    run.put("pulls_7", {"head": {"sha": run.head, "ref": "ticket/T-1-a"}, "base": {"ref": "milestone/M1"}})
    run.comments(run.verdict("PASS", sha=passed))
    proc = run.run()
    assert run.statuses() == ["success"], proc.stdout + proc.stderr


def test_agent_merge_fails_closed_when_the_record_cannot_be_read(verdict_run):
    verdict_run.comments(verdict_run.verdict("PASS"))
    proc = verdict_run.run(FAKE_GH_BREAK_STATUSES="1")
    assert verdict_run.statuses() == ["failure"], proc.stdout + proc.stderr


def test_agent_merge_reads_an_issue_tickets_risk(tmp_path):
    """With issue tickets the Risk line is in the issue body; the step hands it to the check."""
    run = VerdictRun(tmp_path)
    (run.state / "issue.md").write_text("Risk: high\n")
    origin = run.origin
    origin.git("checkout", "-q", "-b", "ticket/12-a", "ticket/T-1-a")
    passed = origin.git("rev-parse", "HEAD")
    origin.git("checkout", "-q", "milestone/M1")
    origin.write("b.py", "b = 1\n")
    origin.commit("another ticket merged")
    origin.git("checkout", "-q", "ticket/12-a")
    origin.git("merge", "-q", "--no-ff", "--no-edit", "milestone/M1")
    run.head = origin.git("rev-parse", "HEAD")
    origin.git("update-ref", "refs/pull/7/head", run.head)
    origin.git("checkout", "-q", "main")
    run.put("pulls_7", {"head": {"sha": run.head, "ref": "ticket/12-a"}, "base": {"ref": "milestone/M1"}})
    run.comments(run.verdict("PASS", sha=passed))
    proc = run.run()
    assert run.statuses() == ["failure"] and "Risk: high" in proc.stdout, proc.stdout + proc.stderr


def test_agent_merge_runs_one_at_a_time_per_pull_request():
    """F20: two runs that overlap each wrote the status from their own snapshot; the older could win."""
    text = (FILES / "agent-merge" / "agent-merge.yml").read_text()
    block = text.split("\nconcurrency:\n", 1)[1].split("\n\n", 1)[0]
    assert "group: verdict-${{ github.event.pull_request.number || github.event.issue.number }}" in block
    assert "cancel-in-progress: false" in block


# --- F07: a branch name skips the ticket checks only on the base it belongs to --------------

INTO_MILESTONE = dict(BASE_REF="milestone/M1", DEFAULT_BRANCH="main")


def test_a_milestone_branch_into_another_branch_is_not_a_milestone_pr(milestone_repo, tmp_path):
    """An agent that names its branch milestone/x and targets the milestone used to skip every ticket check."""
    milestone_repo.git("checkout", "-q", "-b", "milestone/x", "milestone/M1")
    milestone_repo.write("src/anything.py", "unchecked = True\n")
    milestone_repo.commit("work on a branch named like a milestone")
    proc, out = run_find(milestone_repo, tmp_path, "milestone/x", "example-bot", **INTO_MILESTONE)
    assert proc.returncode == 1 and "To fix:" in proc.stdout, proc.stdout + proc.stderr
    assert "skip=true" not in out


def test_a_persons_milestone_named_branch_is_still_left_to_people(milestone_repo, tmp_path):
    proc, out = run_find(milestone_repo, tmp_path, "milestone/x", "example-owner", **INTO_MILESTONE)
    assert proc.returncode == 0 and "skip=true" in out
    assert "milestone PR" not in proc.stdout  # skipped as a person's PR, not as a milestone PR


def test_a_plan_pr_into_a_milestone_branch_is_still_a_plan_pr(milestone_repo, tmp_path):
    """The Level 4 cut: the plan PR for the next milestone targets its branch."""
    milestone_repo.git("checkout", "-q", "-b", "plan/next", "milestone/M1")
    milestone_repo.write("docs/tickets/T-7.md", "# T-7\n\nStatus: open\n")
    milestone_repo.commit("cut")
    proc, out = run_find(milestone_repo, tmp_path, "plan/next", "example-bot", **INTO_MILESTONE)
    assert proc.returncode == 0 and "skip=true" in out, proc.stdout + proc.stderr


def test_a_plan_branch_into_any_other_branch_is_not_a_plan_pr(milestone_repo, tmp_path):
    repo = milestone_repo
    repo.git("checkout", "-q", "-b", "ticket/T-1-a", "milestone/M1")
    repo.git("update-ref", "refs/remotes/origin/ticket/T-1-a", "HEAD")
    repo.git("checkout", "-q", "-b", "plan/x")
    repo.write("docs/tickets/T-1.md", "## Scope\n\n- `**`\n")
    repo.commit("widen a ticket from inside its own branch")
    proc, out = run_find(repo, tmp_path, "plan/x", "example-bot", BASE_REF="ticket/T-1-a", DEFAULT_BRANCH="main")
    assert proc.returncode == 1 and "To fix:" in proc.stdout, proc.stdout + proc.stderr
    assert "skip=true" not in out


def test_a_plan_pr_may_change_an_open_ticket(tickets_repo, tmp_path):
    tickets_repo.write("docs/tickets/T-1.md", "## Scope\n\n- `src/**`\n- `docs/guide.md`\n")
    tickets_repo.commit("re-plan an open ticket")
    proc, out = run_find(tickets_repo, tmp_path, "plan/replan", "example-bot")
    assert proc.returncode == 0 and "skip=true" in out, proc.stdout + proc.stderr


def test_a_plan_pr_may_not_change_a_done_ticket(repo, tmp_path):
    repo.write("docs/tickets/T-2.md", "# T-2\n\nStatus: done\n\n## Scope\n\n- `src/**`\n")
    repo.commit("tickets")
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    repo.write("docs/tickets/T-2.md", "# T-2\n\nStatus: open\n\n## Scope\n\n- `**`\n")
    repo.commit("reopen and widen a finished ticket")
    proc, out = run_find(repo, tmp_path, "plan/again", "example-bot")
    assert proc.returncode == 1 and "T-2" in proc.stdout and "To fix:" in proc.stdout
    assert "skip=true" not in out


def test_a_plan_pr_may_not_delete_a_done_ticket(repo, tmp_path):
    repo.write("docs/tickets/T-2.md", "# T-2\n\nStatus: done\n")
    repo.commit("tickets")
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    repo.remove("docs/tickets/T-2.md")
    repo.commit("drop the record")
    proc, out = run_find(repo, tmp_path, "plan/tidy", "example-bot")
    assert proc.returncode == 1 and "skip=true" not in out


def test_a_plan_pr_may_not_change_a_ticket_an_open_pr_works_on(tickets_repo, tmp_path):
    tickets_repo.write("docs/tickets/T-1.md", "## Scope\n\n- `**`\n")
    tickets_repo.commit("change a ticket under its builder")
    path = stub_gh(tmp_path, pr_list="ticket/T-1-first")
    proc, out = run_find(tickets_repo, tmp_path, "plan/replan", "example-bot", PATH=path, PR_NUMBER="9")
    assert proc.returncode == 1 and "ticket/T-1-first" in proc.stdout and "To fix:" in proc.stdout
    assert "skip=true" not in out


def test_a_plan_pr_that_adds_tickets_is_not_stopped_by_other_open_prs(tickets_repo, tmp_path):
    tickets_repo.write("docs/tickets/T-2.md", "# T-2\n\nStatus: open\n")
    tickets_repo.commit("a new ticket")
    path = stub_gh(tmp_path, pr_list="ticket/T-1-first")
    proc, out = run_find(tickets_repo, tmp_path, "plan/more", "example-bot", PATH=path, PR_NUMBER="9")
    assert proc.returncode == 0 and "skip=true" in out, proc.stdout + proc.stderr


# --- found by the consistency audit before the 0.1.6 PR ----------------------------------

def test_a_plan_pr_into_main_may_not_change_a_ticket_done_on_a_milestone_branch(milestone_repo, tmp_path):
    """A ticket's PR marks it done on the milestone branch; main still says open until the sign-off."""
    repo = milestone_repo
    repo.git("checkout", "-q", "milestone/M1")
    repo.write("docs/tickets/T-1.md", "Status: done\n\n## Scope\n\n- `src/**`\n")
    repo.commit("T-1 merged into the milestone, marked done")
    repo.git("update-ref", "refs/remotes/origin/milestone/M1", "milestone/M1")
    repo.git("checkout", "-q", "-b", "plan/rewrite", "main")
    repo.write("docs/tickets/T-1.md", "## Scope\n\n- `**`\n")
    repo.commit("re-plan a ticket that is finished on its milestone")
    proc, out = run_find(repo, tmp_path, "plan/rewrite", "example-bot")
    assert proc.returncode == 1 and "T-1" in proc.stdout and "done" in proc.stdout, proc.stdout + proc.stderr
    assert "skip=true" not in out


def test_multi_account_codeowners_cover_the_files_tools_load_by_themselves():
    text = (FILES / "multi-account" / "CODEOWNERS-agent-merge").read_text()
    for pattern in ("/.mcp.json", ".gitattributes", "/.gitmodules", "/.githooks/", "/.devcontainer/",
                    "/.cursor/", "/.codex/", "GEMINI.md"):
        assert any(line.split()[0] == pattern for line in text.splitlines() if line and not line.startswith("#")), pattern
