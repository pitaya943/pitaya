"""Helpers for the guardrail recipe tests: run a copyable check, build a small git repo, write a ticket."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FILES = REPO_ROOT / "docs" / "guardrails" / "files"


def run_check(recipe: str, script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(FILES / recipe / script), *args],
                          capture_output=True, text=True, cwd=cwd, timeout=30)


class Repo:
    """A throwaway git repo with helpers to write files and commit."""

    def __init__(self, path: Path):
        self.path = path
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        env_args = ["-c", "user.name=example-bot", "-c", "user.email=bot@example.com"]
        out = subprocess.run(["git", *env_args, *args], cwd=self.path, check=True, capture_output=True, text=True)
        return out.stdout.strip()

    def write(self, rel: str, text: str) -> None:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def remove(self, rel: str) -> None:
        self.git("rm", "-q", rel)

    def commit(self, message: str = "change") -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")


def ticket(tmp_path: Path, **sections: list[str]) -> Path:
    """Write a ticket body with the given sections, e.g. ticket(p, Scope=["src/**"])."""
    parts = ["## Goal\n\nDo the thing.\n", "## Done when\n\n1. It works.\n"]
    for title, items in sections.items():
        heading = title.replace("_", " ")
        parts.append(f"## {heading}\n\n" + "".join(f"- `{item}`\n" for item in items))
    path = tmp_path / "ticket.md"
    path.write_text("\n".join(parts))
    return path
