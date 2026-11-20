#!/usr/bin/env python3
# pitaya template 0.1.0 · .claude/hooks/ask_on_merge.py
"""PreToolUse hook: ask a person before an agent merges a pull request.

What it guards against: an agent merging its own PR while the project's
policy is that only the Owner merges. With "Required approvals: 0" a
machine account with Write access can merge a green PR, so the policy needs
something that acts before the merge.

How it decides: it asks when a Bash command runs `gh pr merge` or calls the
merge API (`gh api ... /pulls/<n>/merge`), and when the GitHub tool
`merge_pull_request` is called. It lets the call through when the
"Autonomy" line in docs/agents/harness.md says agents merge (Level 3 with
the agent-merge recipe), because then the `verdict` status guards the merge.

Limits: only Claude Code runs hooks. The ruleset's required approval is the
guarantee; this hook stops the attempt early and explains why.

When to remove: when the ruleset requires an approval the agents can't give
themselves and transcripts show agents no longer try to merge.

Protocol: reads PreToolUse JSON on stdin; prints a hookSpecificOutput
decision to stdout, or nothing to let the call through. Exits 1 with a
message on stderr when the input can't be read (fails open, loudly).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

CONTROL = {"&&", "||", ";", "|", "&", "(", ")"}
WRAPPERS = {"sudo", "command", "env", "time", "nohup", "exec"}
MERGE_API = re.compile(r"(^|/)pulls/\d+/merge$")
HARNESS = Path("docs") / "agents" / "harness.md"


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


def is_merge(words: list[str]) -> bool:
    if not words or Path(words[0]).name != "gh":
        return False
    if words[1:3] == ["pr", "merge"]:
        return True
    return len(words) > 1 and words[1] == "api" and any(MERGE_API.search(w.split("?")[0]) for w in words[2:])


def agents_may_merge(cwd: Path) -> bool:
    """True when the harness file's Autonomy line lets agents merge."""
    roots = [Path(os.environ["CLAUDE_PROJECT_DIR"])] if os.environ.get("CLAUDE_PROJECT_DIR") else []
    roots += [cwd, *cwd.parents]
    for root in roots:
        path = root / HARNESS
        if path.is_file():
            for line in path.read_text(errors="replace").splitlines():
                if "Autonomy:" in line:
                    return "agents merge" in line.lower()
            return False
    return False


def decide(payload: dict) -> dict | None:
    tool = payload.get("tool_name") or ""
    cwd = Path(payload.get("cwd") or ".")
    if tool == "Bash":
        command = (payload.get("tool_input") or {}).get("command") or ""
        merging = any(is_merge(words) for words in segments(command))
    else:
        merging = tool.endswith("merge_pull_request")
    if not merging or agents_may_merge(cwd):
        return None
    return {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            "Asked by .claude/hooks/ask_on_merge.py: this merges a pull request, and the "
            "Autonomy line in docs/agents/harness.md doesn't let agents merge. "
            "Approve only if the Owner asked for this merge; otherwise leave the PR for the Owner."
        ),
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        decision = decide(payload)
    except Exception as exc:  # fail open, but say so
        print(f"ask_on_merge.py could not check this call: {exc}", file=sys.stderr)
        return 1
    if decision:
        print(json.dumps({"hookSpecificOutput": decision}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
