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
The skills then run without the `pitaya:` prefix (`/build`, not `/pitaya:build`).

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
import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
PARTS = ("skills", "docs", "templates")
MANIFEST = "pitaya.json"
IGNORED = {"__pycache__", ".pytest_cache"}


def plugin_version() -> str:
    manifest = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        return json.loads(manifest.read_text())["version"]
    vendored = PLUGIN_ROOT / MANIFEST  # vendoring from an already vendored copy
    return json.loads(vendored.read_text())["version"] if vendored.is_file() else "unknown"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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

    shipped = sources()
    for rel, src in shipped.items():
        dest = claude / rel
        want = digest(src)
        if not dest.exists():
            status = "created"
        elif digest(dest) == want:
            status = "unchanged"
        elif owned.get(rel) == digest(dest):
            status = "upgraded" if args.upgrade else "stale"
        else:
            status = "differs"
        if status in ("created", "upgraded"):
            if not args.check:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)  # keeps the executable bit on hooks and scripts
            owned[rel] = want
        elif status == "unchanged":
            owned[rel] = want
        elif status == "differs":
            owned.pop(rel, None)  # the project's file now; never claim it
        label = {"created": "would create", "upgraded": "would upgrade"}.get(status, status) if args.check else status
        print(f"{label.ljust(9)} {rel}")

    for rel in sorted(set(owned) - set(shipped)):
        dest = claude / rel
        if dest.exists() and digest(dest) == owned[rel] and args.upgrade:
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
