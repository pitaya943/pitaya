#!/usr/bin/env python3
# pitaya template 0.1.7 · .claude/hooks/ask_on_rule_files.py
"""PreToolUse hook: ask the user before an agent changes the harness's own rules.

What it guards against: an agent loosening its own rules to get past them,
for example editing AGENTS.md, the harness config, the hooks or the CI
workflow, without anyone noticing.

How it decides: file tools (Edit, Write, MultiEdit, NotebookEdit) that touch a
rule file, and shell commands that write to one (redirects, `sed -i`, `mv`,
`rm`, `cp`, `tee`, `truncate`, `touch`, `ln`), get an "ask" decision: the user
sees a confirmation prompt with the reason. Reads are let through.

Rule files: any AGENTS.md or CLAUDE.md, docs/agents/harness.md, everything
under .claude/, and everything under .github/ (workflows, guardrail scripts,
CODEOWNERS). Also the files another tool, git or a dev container loads or runs
by itself: .mcp.json, .gitmodules, any .gitattributes or GEMINI.md, and
everything under .githooks/, .devcontainer/, .cursor/ and .codex/. A pull
request that adds .mcp.json makes later sessions offer to start the server it
names. Test configuration (conftest.py, package.json and the like) isn't on
the list: sessions edit it all the time, and the read-only-paths check guards
it in ticket PRs.

Limits: it asks rather than denies, because maintaining the rules is normal
work. Shell detection covers common write forms, not every possible one, and
tools other than the file tools and Bash aren't checked: it prevents
accidents, and is not a security boundary. Only Claude Code runs hooks.

When to remove: when rule files sit behind a CODEOWNERS review that agents
can't satisfy, so CI enforces the same thing at merge time.

Protocol: reads PreToolUse JSON on stdin; prints a hookSpecificOutput
decision to stdout, or nothing to let the call through. Exits 1 with a
message on stderr when the input can't be read (fails open, loudly).
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path

# The harness's own rules, then the files another tool, git or a dev container loads or runs by itself.
RULE_NAMES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", ".gitattributes"}
RULE_FILES = {"docs/agents/harness.md", ".mcp.json", ".gitmodules"}
RULE_DIRS = (".claude/", ".github/", ".githooks/", ".devcontainer/", ".cursor/", ".codex/")
RULE_MARKERS = tuple(sorted(RULE_NAMES | RULE_FILES)) + RULE_DIRS
INTERPRETERS = {"python", "python3", "node", "perl", "ruby", "deno", "bun"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
FILE_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
WRITE_PROGRAMS = {"mv", "rm", "cp", "tee", "truncate", "touch", "ln", "install"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>", "1>", "2>"}
CONTROL = {"&&", "||", ";", "|", "&", "(", ")"}


def project_root(payload: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()


def rule_path(path: str, root: Path, cwd: Path) -> str | None:
    """Return the path relative to the project root if it's a rule file, else None."""
    full = Path(path)
    full = (full if full.is_absolute() else cwd / full).resolve()
    try:
        rel = full.relative_to(root).as_posix()
    except ValueError:
        return None  # outside the project
    if full.name in RULE_NAMES or rel in RULE_FILES or rel.startswith(RULE_DIRS):
        return rel
    return None


def segments(command: str) -> list[list[str]]:
    """Split a shell command into simple commands, keeping redirect operators as words."""
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
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
    return out


def expand(words: list[str], depth: int = 0) -> list[list[str]]:
    """The simple commands in `words`, looking inside `sh -c '...'` and `eval '...'`."""
    name = Path(words[0]).name if words else ""
    if depth < 4 and name in SHELLS and "-c" in words[1:-1]:
        return [c for seg in segments(words[words.index("-c") + 1]) for c in expand(seg, depth + 1)]
    if depth < 4 and name == "eval":
        return [c for seg in segments(" ".join(words[1:])) for c in expand(seg, depth + 1)]
    return [words]


def inline_script_marker(words: list[str]) -> str | None:
    """A rule path named in inline code (`python3 -c`, `node -e`), which could write anywhere."""
    if not words or Path(words[0]).name not in INTERPRETERS:
        return None
    for i, word in enumerate(words[1:-1], 1):
        if word in ("-c", "-e", "--eval"):
            return next((m for m in RULE_MARKERS if m in words[i + 1]), None)
    return None


def written_paths(words: list[str]) -> list[str]:
    """The paths a simple command writes to, as far as we can tell."""
    paths = [words[i + 1] for i, w in enumerate(words[:-1]) if w in REDIRECTS]
    program = Path(words[0]).name if words else ""
    in_place = program == "sed" and any(w.startswith("-i") or w == "--in-place" for w in words[1:])
    if program in WRITE_PROGRAMS or in_place:
        paths += [w for w in words[1:] if not w.startswith("-") and w not in REDIRECTS]
    return paths


def ask(rel: str, how: str) -> dict:
    return {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            f"{how} {rel}, a rule file: one of the harness's own, or one a tool loads or runs by itself "
            "(.claude/hooks/ask_on_rule_files.py). Rule files change only with the user's agreement. "
            "Approve if you asked for this change."
        ),
    }


def decide(payload: dict) -> dict | None:
    root = project_root(payload)
    cwd = Path(payload.get("cwd") or root)
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if tool in FILE_TOOLS:
        path = tool_input.get(FILE_TOOLS[tool])
        rel = rule_path(path, root, cwd) if path else None
        return ask(rel, f"{tool} changes") if rel else None
    if tool == "Bash":
        for words in (c for seg in segments(tool_input.get("command") or "") for c in expand(seg)):
            marker = inline_script_marker(words)
            if marker:
                return ask(marker, "This inline script names")
            for path in written_paths(words):
                rel = rule_path(path, root, cwd)
                if rel:
                    return ask(rel, "This shell command writes to")
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        decision = decide(payload)
    except Exception as exc:  # fail open, but say so
        print(f"ask_on_rule_files.py could not check this call: {exc}", file=sys.stderr)
        return 1
    if decision:
        print(json.dumps({"hookSpecificOutput": decision}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
