#!/usr/bin/env python3
# pitaya template 0.1.9 · .claude/hooks/ask_on_merge.py
"""PreToolUse hook: ask a person before an agent merges a pull request.

What it guards against: an agent merging its own PR while the project's
policy is that only the Owner merges. With "Required approvals: 0" a
machine account with Write access can merge a green PR, so the policy needs
something that acts before the merge.

How it decides: it asks when a Bash command runs `gh pr merge` (also inside
`sh -c` or `eval`, and after gh's `-R` flag), calls the merge API
(`gh api .../pulls/<n>/merge`, or the GraphQL merge and auto-merge
mutations), and when a GitHub tool that merges or enables auto-merge is
called. It lets the call through when the
"Autonomy" line in docs/agents/harness.md says agents merge (Level 3 with
the agent-merge recipe), because then the `verdict` status guards the merge.

Limits: only Claude Code runs hooks, and a determined script can still reach
the API another way. The ruleset's required approval on `main` is
the guarantee; this hook stops the usual attempts early and explains why.

When to remove: when the ruleset requires an approval the agents can't give
themselves and transcripts show agents no longer try to merge.

Protocol: reads PreToolUse JSON on stdin; prints a hookSpecificOutput
decision to stdout, or nothing to let the call through. Exits 1 with a
message on stderr when the input can't be read or shell_words.py, the parser
the hooks share, isn't next to this file (fails open, loudly).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # importing the shared parser must not leave __pycache__ in .claude/hooks/
sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared parser sits next to this file
try:
    from shell_words import commands
except ImportError:  # fail open, but say so
    print("ask_on_merge.py could not check this call: .claude/hooks/shell_words.py, which the pitaya hooks share, "
          "is missing. Re-run /setup, or copy it from the pitaya templates.", file=sys.stderr)
    sys.exit(1)

MERGE_API = re.compile(r"(^|/)pulls/\d+/merge$")
HARNESS = Path("docs") / "agents" / "harness.md"
MERGE_MUTATIONS = ("mergePullRequest", "enablePullRequestAutoMerge")
AUTONOMY = re.compile(r"^\s*-\s*Autonomy:\s*(.*)$")


def gh_args(words: list[str]) -> list[str]:
    """gh's arguments after its global flags, such as `-R owner/repo`."""
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in ("-R", "--repo") else 1
    return words[i:]


def is_merge(words: list[str]) -> bool:
    if not words or Path(words[0]).name != "gh":
        return False
    args = gh_args(words)
    if args[:2] == ["pr", "merge"]:
        return True
    if args[:1] == ["api"]:
        rest = args[1:]
        return any(MERGE_API.search(w.split("?")[0]) or any(m in w for m in MERGE_MUTATIONS) for w in rest)
    return False


def agents_may_merge(cwd: Path) -> bool:
    """True when the harness file's Autonomy line lets agents merge."""
    roots = [Path(os.environ["CLAUDE_PROJECT_DIR"])] if os.environ.get("CLAUDE_PROJECT_DIR") else []
    roots += [cwd, *cwd.parents]
    for root in roots:
        path = root / HARNESS
        if path.is_file():
            for line in path.read_text(errors="replace").splitlines():
                match = AUTONOMY.match(line)
                if match:  # the field's value, not the whole line: notes may mention the alternative
                    return match.group(1).strip().lower().startswith("agents merge")
            return False
    return False


def decide(payload: dict) -> dict | None:
    tool = payload.get("tool_name") or ""
    cwd = Path(payload.get("cwd") or ".")
    if tool == "Bash":
        command = (payload.get("tool_input") or {}).get("command") or ""
        merging = any(is_merge(c) for c in commands(command))
    else:
        merging = "merge_pull_request" in tool or "auto_merge" in tool
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
