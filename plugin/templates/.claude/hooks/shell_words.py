#!/usr/bin/env python3
# pitaya template 0.1.9 · .claude/hooks/shell_words.py
"""Shared by the four pitaya hooks: split a Bash command into the simple commands it runs.

What it is for: every hook has to answer "which programs does this command
line run, with which words?" before it can decide anything. The four hooks
used to carry a copy each, and the copies drifted: one of them missed
`bash -lc '...'` and commands behind `sudo` or `env`. One module means a fix
to the parsing lands in every hook at once.

What it does: `segments` splits on `&&`, `||`, `;`, `|`, `&`, parentheses and
newlines, and drops leading `VAR=value` assignments and wrappers such as
`sudo`. `expand` looks inside `sh -c '...'` (also `-lc`, `-ec`) and `eval`.
Redirect operators stay in the words, for the hook that looks for writes.

Limits: it reads words, it doesn't run a shell. A variable, a command
substitution, an alias, `xargs` or a script file hides the command from it.
The hooks prevent accidents; they are not a security boundary.

Not a hook: `.claude/settings.json` doesn't run this file, the hooks import
it. Keep it next to them; a hook that can't find it lets the call through and
says so on stderr.

When to remove: together with the last hook that imports it.
"""

from __future__ import annotations

import shlex
from pathlib import Path

CONTROL = {"&&", "||", ";", "|", "&", "(", ")"}
WRAPPERS = {"sudo", "command", "env", "time", "nohup", "exec"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
MAX_DEPTH = 4  # how many `sh -c` or `eval` layers `expand` opens


def strip_prefix(words: list[str]) -> list[str]:
    """Drop leading VAR=value assignments and wrappers such as sudo."""
    i = 0
    while i < len(words) and ("=" in words[i] and not words[i].startswith("-") or words[i] in WRAPPERS):
        i += 1
    return words[i:]


def segments(command: str) -> list[list[str]]:
    """Split a shell command into simple commands, each a list of words (redirect operators included)."""
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


def expand(words: list[str], depth: int = 0) -> list[list[str]]:
    """The simple commands in `words`, looking inside `sh -c '...'` and `eval '...'`."""
    name = Path(words[0]).name if words else ""
    if depth < MAX_DEPTH and name in SHELLS:
        for i, word in enumerate(words[1:], 1):
            if word == "-c" or (word.startswith("-") and not word.startswith("--") and "c" in word[1:]):
                if i + 1 < len(words):
                    return [c for seg in segments(words[i + 1]) for c in expand(seg, depth + 1)]
                break
    if depth < MAX_DEPTH and name == "eval":
        return [c for seg in segments(" ".join(words[1:])) for c in expand(seg, depth + 1)]
    return [words]


def commands(command: str) -> list[list[str]]:
    """Every simple command a Bash command line runs, as far as words can tell."""
    return [c for seg in segments(command) for c in expand(seg)]
