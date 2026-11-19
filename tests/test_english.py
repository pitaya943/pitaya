"""Every file in the repository is written in English (decision D27).

CJK characters are the practical signal: the project's earlier docs were
bilingual Chinese and English, and none of that should come back.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "node_modules", ".venv"}
CJK_RE = re.compile("[\u3000-\u9fff\uff00-\uffef]")


def text_files() -> list[Path]:
    files = []
    for path in REPO_ROOT.rglob("*"):
        if path.is_file() and not SKIP_DIRS & set(path.relative_to(REPO_ROOT).parts):
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # binary
            files.append(path)
    return files


def test_no_cjk_anywhere():
    offenders = []
    for path in text_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if CJK_RE.search(line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}")
    assert offenders == []


def test_detector_works():
    assert CJK_RE.search("\u4e2d\u6587") and CJK_RE.search("\uff08")
    assert not CJK_RE.search("plain English, with an em dash \u2014 and a middle dot \u00b7")
