#!/usr/bin/env python3
# pitaya template 0.1.10 · .claude/hooks/no_push_main.py
"""PreToolUse hook: stop pushes to the default branch, force pushes and remote deletes.

What it guards against: an agent pushing straight to `main` (skipping review)
or rewriting shared history with a force push.

How it decides: it parses each Bash command, finds `git push`, and denies it
when the destination is a protected branch (main, master, or whatever
origin/HEAD points to), or when the push forces, deletes or mirrors refs.
A plain push of a feature branch is let through.

Limits: only Claude Code runs hooks. The ruleset on `main` is still the
guarantee at merge time; this hook just stops the attempt early and explains
what to do instead.

When to remove: when the ruleset on `main` is in place and transcripts show
agents no longer attempt direct or forced pushes over several releases.

Protocol: reads PreToolUse JSON on stdin; prints a hookSpecificOutput
decision to stdout, or nothing to let the call through. Exits 1 with a
message on stderr when the input can't be read or shell_words.py, the parser
the hooks share, isn't next to this file (fails open, loudly).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # importing the shared parser must not leave __pycache__ in .claude/hooks/
sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared parser sits next to this file
try:
    from shell_words import commands
except ImportError:  # fail open, but say so
    print("no_push_main.py could not check this call: .claude/hooks/shell_words.py, which the pitaya hooks share, "
          "is missing. Re-run /setup, or copy it from the pitaya templates.", file=sys.stderr)
    sys.exit(1)

PROTECTED = {"main", "master"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def git_subcommand(words: list[str]) -> tuple[str | None, list[str], str | None]:
    """For a git command, return (subcommand, its arguments, the -C directory if any)."""
    if not words or Path(words[0]).name != "git":
        return None, [], None
    i, directory = 1, None
    while i < len(words) and words[i].startswith("-"):
        opt = words[i]
        if opt in GIT_OPTS_WITH_VALUE:
            if opt == "-C" and i + 1 < len(words):
                directory = words[i + 1]
            i += 2
        else:
            i += 1
    if i >= len(words):
        return None, [], directory
    return words[i], words[i + 1:], directory


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def protected_branches(cwd: Path) -> set[str]:
    names = set(PROTECTED)
    head = git(cwd, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if head.startswith("origin/"):
        names.add(head.removeprefix("origin/"))
    return names


def check_push(args: list[str], cwd: Path) -> str | None:
    """Return a reason to deny this `git push`, or None to allow it."""
    positional, has_repo, skip = [], False, False
    for i, arg in enumerate(args):
        if skip:
            skip = False
            continue
        if arg == "--repo" or arg.startswith("--repo="):
            has_repo, skip = True, arg == "--repo"
            continue
        if arg.startswith("--"):
            name = arg.split("=", 1)[0]
            if name in ("--force", "--force-with-lease", "--force-if-includes"):
                return "a force push rewrites history that others may rely on"
            if name in ("--delete", "--mirror", "--all", "--prune"):
                return f"`git push {name}` can delete or overwrite remote branches"
        elif arg.startswith("-") and len(arg) > 1:
            if "f" in arg[1:]:
                return "a force push rewrites history that others may rely on"
            if "d" in arg[1:]:
                return "`git push -d` deletes a remote branch"
        else:
            positional.append(arg)

    current = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    protected = protected_branches(cwd)
    # With --repo, the remote is named by the option, so every positional word is a refspec.
    refspecs = (positional if has_repo else positional[1:]) or ["HEAD"]
    for spec in refspecs:
        if spec.startswith("+"):
            return f"the refspec `{spec}` forces the push"
        if spec.startswith(":"):
            return f"the refspec `{spec}` deletes a remote branch"
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        dst = dst.removeprefix("refs/heads/")
        if dst == "HEAD":
            dst = current
        if dst in protected:
            return f"it pushes to `{dst}`, the protected default branch"
    return None


def decide(payload: dict) -> dict | None:
    if payload.get("tool_name") != "Bash":
        return None
    command = (payload.get("tool_input") or {}).get("command") or ""
    cwd = Path(payload.get("cwd") or ".")
    for words in commands(command):
        sub, args, directory = git_subcommand(words)
        if sub != "push":
            continue
        where = (cwd / directory) if directory else cwd
        reason = check_push(args, where)
        if reason:
            return {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked by .claude/hooks/no_push_main.py: {reason}. "
                    "Push your own branch without forcing, then open a pull request; "
                    "whoever docs/agents/harness.md names under Autonomy merges it. "
                    "If a rewrite or direct push is really needed, ask the user to run it."
                ),
            }
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        decision = decide(payload)
    except Exception as exc:  # fail open, but say so
        print(f"no_push_main.py could not check this call: {exc}", file=sys.stderr)
        return 1
    if decision:
        print(json.dumps({"hookSpecificOutput": decision}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
