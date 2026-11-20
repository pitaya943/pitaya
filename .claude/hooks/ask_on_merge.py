#!/usr/bin/env python3
# pitaya template 0.1.10 · .claude/hooks/ask_on_merge.py
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

Two merges it asks about whatever the Autonomy line says, because they use
the Owner's bypass of the rulesets, which no status guards: `gh pr merge
--admin`, and any merge while the harness file's "Machine account" line says
"none" (the session then acts as the account it is signed in with, usually
the Owner's). A harness file with no such line is read as before.

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
MACHINE = re.compile(r"^\s*-\s*Machine account:\s*(.*)$")
NO_ACCOUNT = re.compile(r"none\b(?!-)", re.IGNORECASE)  # the word, not a login that starts with it
FALSE_VALUES = ("0", "f", "false")  # what gh reads as "off" in `--admin=<value>`


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


def is_admin_merge(words: list[str]) -> bool:
    """`gh pr merge --admin`: a merge that doesn't meet the rules, through the Owner's bypass.
    gh takes no shorter spelling of the flag, so matching it by name holds."""
    if not is_merge(words) or gh_args(words)[:2] != ["pr", "merge"]:
        return False
    for word in gh_args(words)[2:]:
        flag, _, value = word.partition("=")
        if flag == "--admin" and value.lower() not in FALSE_VALUES:
            return True
    return False


def harness_lines(cwd: Path) -> list[str]:
    """The harness file's lines, from the project root or the nearest folder above `cwd` that has one."""
    roots = [Path(os.environ["CLAUDE_PROJECT_DIR"])] if os.environ.get("CLAUDE_PROJECT_DIR") else []
    roots += [cwd, *cwd.parents]
    for root in roots:
        path = root / HARNESS
        if path.is_file():
            return path.read_text(errors="replace").splitlines()
    return []


def field(lines: list[str], pattern: re.Pattern) -> str | None:
    """The value of the first line the pattern matches: the field's value, not the whole line,
    because the notes after it may mention the alternative."""
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return None


def agents_may_merge(lines: list[str]) -> bool:
    """True when the harness file's Autonomy line lets agents merge."""
    return (field(lines, AUTONOMY) or "").lower().startswith("agents merge")


def no_machine_account(lines: list[str]) -> bool:
    """True when the harness file has a "Machine account" line whose value is "none" or empty.
    No such line at all is not "none": a harness file written by hand may leave it out."""
    value = field(lines, MACHINE)
    if value is None:
        return False
    value = value.lstrip("\"'`*_ ")
    return not value or bool(NO_ACCOUNT.match(value))


def ask(reason: str) -> dict:
    return {"hookEventName": "PreToolUse", "permissionDecision": "ask",
            "permissionDecisionReason": "Asked by .claude/hooks/ask_on_merge.py: " + reason}


def decide(payload: dict) -> dict | None:
    tool = payload.get("tool_name") or ""
    cwd = Path(payload.get("cwd") or ".")
    admin = False
    if tool == "Bash":
        command = (payload.get("tool_input") or {}).get("command") or ""
        runs = commands(command)
        merging = any(is_merge(c) for c in runs)
        admin = any(is_admin_merge(c) for c in runs)
    else:
        merging = "merge_pull_request" in tool or "auto_merge" in tool
    if not merging:
        return None
    lines = harness_lines(cwd)
    if admin:
        return ask("`gh pr merge --admin` merges a pull request that doesn't meet the rules, through the "
                   "Owner's bypass. That is the Owner's call, never an agent's, whatever the Autonomy line in "
                   "docs/agents/harness.md says. Approve only if the Owner asked for exactly this merge.")
    if no_machine_account(lines):
        return ask("this merges a pull request, and docs/agents/harness.md names no machine account, so this "
                   "session acts as the account it is signed in with, usually the Owner's, whose bypass skips "
                   "the rulesets and their required checks. Approve only if the Owner asked for this merge.")
    if agents_may_merge(lines):
        return None
    return ask("this merges a pull request, and the Autonomy line in docs/agents/harness.md doesn't let "
               "agents merge. Approve only if the Owner asked for this merge; otherwise leave the PR for "
               "the Owner.")


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
