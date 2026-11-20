#!/usr/bin/env python3
"""Copy the pitaya plugin into a project's .claude/ folder, for cloud sessions (D51).

Usage::

    python3 vendor_plugin.py --target .            # copy, never overwriting
    python3 vendor_plugin.py --target . --check    # report only
    python3 vendor_plugin.py --target . --upgrade  # also replace copies this script made earlier

Why: Claude Code cloud sessions don't load plugins, only what the repository
commits, such as `.claude/skills/`. So this copies the plugin's `skills/`,
`docs/` and `templates/` into `<target>/.claude/`, keeping their layout:
`.claude/` takes the place of the plugin root, every relative link in the skills
still resolves, and `/setup`'s installer still finds `.claude/templates/`.

Each skill is copied as `pitaya-<name>` (D52): `skills/help/` becomes
`skills/pitaya-help/`, its `name:` becomes `pitaya-help`, links to it are
rewritten, and `/pitaya:<skill>` in the text becomes `/pitaya-<skill>`. So the
copy can't collide with Claude Code's built-in `/help` or a project's own
`build` skill, and the names stay one character away from the plugin's.

Rules, so a re-run is always safe:

* A missing file is created, and its hash recorded in `.claude/pitaya.json`.
* An existing file that matches is `unchanged`.
* An existing file whose hash matches the record is this script's own older
  copy: `stale`, replaced only with --upgrade (`upgraded`).
* Anything else is the project's file, or a copy someone edited: `differs`,
  never touched. Show the diff and let the user decide.
* A file the record lists but the new version no longer ships is `obsolete`;
  --upgrade removes it if it is still unmodified.

Output: a header line, then one line per file, `<status> <path>`, with paths
relative to `.claude/`. Exit 0 on success. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
PARTS = ("skills", "docs", "templates")
MANIFEST = "pitaya.json"
IGNORED = {"__pycache__", ".pytest_cache"}
PREFIX = "pitaya-"
TEXT = {".md", ".json"}  # rewritten for the new names; scripts and workflows are copied byte for byte


def plugin_version() -> str:
    manifest = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        return json.loads(manifest.read_text())["version"]
    vendored = PLUGIN_ROOT / MANIFEST  # vendoring from an already vendored copy
    return json.loads(vendored.read_text())["version"] if vendored.is_file() else "unknown"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def skill_names() -> list[str]:
    """The skills' names as the plugin ships them, without a prefix (also when copying from a copy)."""
    return sorted(p.parent.name.removeprefix(PREFIX) for p in (PLUGIN_ROOT / "skills").glob("*/SKILL.md"))


def destination(rel: str) -> str:
    """skills/<name>/... -> skills/pitaya-<name>/...; everything else keeps its path."""
    parts = rel.split("/")
    if parts[0] == "skills" and len(parts) > 2 and not parts[1].startswith(PREFIX):
        parts[1] = PREFIX + parts[1]
    return "/".join(parts)


def content(rel: str, src: Path, names: list[str]) -> bytes:
    """The file as it goes into the copy: text renamed to the prefixed skills, the rest unchanged."""
    data = src.read_bytes()
    if src.suffix not in TEXT:
        return data
    text = data.decode()
    alternation = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    text = re.sub(rf"(skills/)({alternation})/", rf"\g<1>{PREFIX}\2/", text)  # links and paths
    text = re.sub(rf"(?<![\w-])\.\./({alternation})/", rf"../{PREFIX}\1/", text)  # sibling-skill links
    text = text.replace("/pitaya:", "/" + PREFIX)  # commands as the user types them
    if src.name == "SKILL.md":
        text = re.sub(r"(?m)^name: (?!pitaya-)(\S+)$", rf"name: {PREFIX}\1", text, count=1)
    return text.encode()


def sources() -> dict[str, Path]:
    """Every shipped file, keyed by its path relative to the plugin root."""
    found = {}
    for part in PARTS:
        for path in sorted((PLUGIN_ROOT / part).rglob("*")):
            if path.is_file() and not IGNORED & set(path.relative_to(PLUGIN_ROOT).parts):
                found[path.relative_to(PLUGIN_ROOT).as_posix()] = path
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy the pitaya plugin into a project's .claude/ folder.")
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true", help="report only; write nothing")
    parser.add_argument("--upgrade", action="store_true", help="replace unmodified copies from an earlier run")
    args = parser.parse_args(argv)

    claude = args.target / ".claude"
    record_path = claude / MANIFEST
    record = json.loads(record_path.read_text()) if record_path.is_file() else {"files": {}}
    owned: dict[str, str] = dict(record.get("files", {}))
    version = plugin_version()
    print(f"pitaya {version} -> {claude.resolve()}")

    names = skill_names()
    shipped = {}
    for src_rel, src in sources().items():
        rel = destination(src_rel)
        shipped[rel] = data = content(src_rel, src, names)
        dest = claude / rel
        want = digest(data)
        have = digest(dest.read_bytes()) if dest.exists() else None
        if have is None:
            status = "created"
        elif have == want:
            status = "unchanged"
        elif owned.get(rel) == have:
            status = "upgraded" if args.upgrade else "stale"
        else:
            status = "differs"
        if status in ("created", "upgraded"):
            if not args.check:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                shutil.copymode(src, dest)  # keeps the executable bit on hooks and scripts
            owned[rel] = want
        elif status == "unchanged":
            owned[rel] = want
        elif status == "differs":
            owned.pop(rel, None)  # the project's file now; never claim it
        label = {"created": "would create", "upgraded": "would upgrade"}.get(status, status) if args.check else status
        print(f"{label.ljust(9)} {rel}")

    for rel in sorted(set(owned) - set(shipped)):
        dest = claude / rel
        if dest.exists() and digest(dest.read_bytes()) == owned[rel] and args.upgrade:
            if not args.check:
                dest.unlink()
            owned.pop(rel)
            print(f"{'removed'.ljust(9)} {rel}")
        else:
            print(f"{'obsolete'.ljust(9)} {rel}")

    if not args.check:
        claude.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps({"version": version, "files": dict(sorted(owned.items()))}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
