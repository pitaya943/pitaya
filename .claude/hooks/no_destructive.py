#!/usr/bin/env python3
# pitaya template 0.1.7 · .claude/hooks/no_destructive.py
"""PreToolUse hook: stop the few shell commands that wipe work and can't be undone.

What it guards against: one command destroying the working tree, the home
directory or uncommitted changes: a recursive `rm` of `/`, `~`, `$HOME`,
`$PWD`, `.`, `..`, `*`, `./*` or `.git`; `find` with `-delete` over the whole
tree and nothing to narrow it; `git reset --hard`; `git checkout` or
`git restore` of `.`, which throws away every uncommitted change; and
`git clean` that forces deletion of directories or ignored files.

How it decides: it parses each Bash command into simple commands and checks
each one. Quoted text (`echo 'rm -rf /'`) is not a command and is let through.

Limits: it catches slips, the plainly accidental forms of the least
recoverable commands. It doesn't follow variables, aliases, scripts or other
tools, so it is not a sandbox and not a security boundary: the real protection
is pushing work before risky steps and running where nothing else can be lost.
Only Claude Code runs hooks.

When to remove: when sessions run in a disposable sandbox or container where
nothing outside the checkout can be lost, and transcripts show these commands
are no longer attempted.

Protocol: reads PreToolUse JSON on stdin; prints a hookSpecificOutput
decision to stdout, or nothing to let the call through. Exits 1 with a
message on stderr when the input can't be read (fails open, loudly).
"""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

CONTROL = {"&&", "||", ";", "|", "&", "(", ")"}
WRAPPERS = {"sudo", "command", "env", "time", "nohup", "exec"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
RM_TARGETS = {"/", "/*", "~", "~/", "~/*", "$HOME", "$HOME/", "$HOME/*", "${HOME}", "${HOME}/", ".", "./", "..", "../",
              "*", "./*", ".git", "./.git", ".git/", "./.git/", "$PWD", "$PWD/", "$PWD/*", "${PWD}", "${PWD}/", "${PWD}/*"}
# Where `find ... -delete` with nothing to narrow it would empty the tree (no path at all means `.`).
FIND_ROOTS = {".", "./", "..", "../", "/", "~", "~/", "$HOME", "$HOME/", "${HOME}", "$PWD", "$PWD/", "${PWD}", ".git", "./.git"}
# Tests that narrow what `find` matches; `-type` and the depth options don't.
FIND_NARROWS = {"-name", "-iname", "-path", "-ipath", "-wholename", "-iwholename", "-regex", "-iregex", "-lname", "-ilname",
                "-newer", "-mtime", "-mmin", "-atime", "-amin", "-ctime", "-cmin", "-size", "-empty", "-user", "-group",
                "-perm", "-samefile", "-inum", "-links"}
# A pathspec that means "everything here" to `git checkout` and `git restore`.
ALL_PATHS = {".", "./", ":/", "*", "./*"}


def segments(command: str) -> list[list[str]]:
    """Split a shell command into simple commands, each a list of words."""
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:  # unbalanced quotes: fall back to plain words
        tokens = command.split()
    out, current = [], []
    for tok in tokens:
        if tok in CONTROL:
            if current:
                out.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        out.append(current)
    return [strip_prefix(seg) for seg in out if seg]


def strip_prefix(words: list[str]) -> list[str]:
    """Drop leading VAR=value assignments and wrappers such as sudo."""
    i = 0
    while i < len(words) and ("=" in words[i] and not words[i].startswith("-") or words[i] in WRAPPERS):
        i += 1
    return words[i:]


SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}


def expand(words: list[str], depth: int = 0) -> list[list[str]]:
    """The simple commands in `words`, looking inside `sh -c '...'` and `eval '...'`."""
    name = Path(words[0]).name if words else ""
    if depth < 4 and name in SHELLS:
        for i, word in enumerate(words[1:], 1):
            if word == "-c" or (word.startswith("-") and not word.startswith("--") and "c" in word[1:]):
                if i + 1 < len(words):
                    return [c for seg in segments(words[i + 1]) for c in expand(seg, depth + 1)]
                break
    if depth < 4 and name == "eval":
        return [c for seg in segments(" ".join(words[1:])) for c in expand(seg, depth + 1)]
    return [words]


def short_flags(args: list[str]) -> str:
    return "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))


def check_rm(args: list[str]) -> str | None:
    recursive = "--recursive" in args or any(c in short_flags(args) for c in "rR")
    if not recursive:
        return None
    for target in (a for a in args if not a.startswith("-")):
        if target in RM_TARGETS:
            return (f"`rm` recursively deletes `{target}`, which can't be undone. "
                    "Instead, delete the specific build or temp directory by name")
    return None


def check_find(args: list[str]) -> str | None:
    if "-delete" not in args or any(a in FIND_NARROWS for a in args):
        return None
    roots = []
    for a in args:
        if a.startswith("-") or a in ("(", "!"):
            break
        roots.append(a)
    if not roots or any(r in FIND_ROOTS for r in roots):
        return ("`find` with `-delete` and nothing to narrow it deletes everything under "
                f"`{roots[0] if roots else '.'}`, the repository's own `.git` included. "
                "Instead, name the directory to empty, or add a test such as `-name '*.pyc'`")
    return None


def check_git(words: list[str]) -> str | None:
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in GIT_OPTS_WITH_VALUE else 1
    if i >= len(words):
        return None
    sub, args = words[i], words[i + 1:]
    if sub == "reset" and "--hard" in args:
        return ("`git reset --hard` throws away uncommitted work. "
                "Instead, use `git stash` to set changes aside, or `git restore <file>` for one file")
    if sub == "checkout" and any(a in ALL_PATHS for a in args):
        return ("`git checkout` of `.` overwrites every changed file with the committed version. "
                "Instead, use `git stash` to set changes aside, or name the one file to restore")
    if sub == "restore" and any(a in ALL_PATHS for a in args):
        flags = short_flags(args)
        staged = "S" in flags or "--staged" in args
        worktree = "W" in flags or "--worktree" in args
        if worktree or not staged:  # with --staged alone it only unstages; the files keep their content
            return ("`git restore` of `.` throws away every uncommitted change in the working tree. "
                    "Instead, use `git stash` to set changes aside, or name the one file to restore")
    if sub == "clean":
        flags = short_flags(args)
        if "n" in flags or "--dry-run" in args:
            return None
        forced = "f" in flags or "--force" in args
        if forced and any(c in flags for c in "dxX"):
            return ("`git clean` with -d or -x deletes untracked and ignored files for good. "
                    "Instead, run `git clean -n` first to list them, and delete specific paths")
    return None


def decide(payload: dict) -> dict | None:
    if payload.get("tool_name") != "Bash":
        return None
    command = (payload.get("tool_input") or {}).get("command") or ""
    for words in (c for seg in segments(command) for c in expand(seg)):
        if not words:
            continue
        program = Path(words[0]).name
        check = {"rm": lambda: check_rm(words[1:]), "find": lambda: check_find(words[1:]),
                 "git": lambda: check_git(words)}.get(program)
        reason = check() if check else None
        if reason:
            return {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked by .claude/hooks/no_destructive.py: {reason}. "
                    "If it really is needed, ask the user to run it themselves."
                ),
            }
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        decision = decide(payload)
    except Exception as exc:  # fail open, but say so
        print(f"no_destructive.py could not check this call: {exc}", file=sys.stderr)
        return 1
    if decision:
        print(json.dumps({"hookSpecificOutput": decision}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
