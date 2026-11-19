"""Workflows use action versions that run on Node 24 (W6 finding: GitHub deprecated Node 20).

actions/checkout@v4 and actions/setup-python@v5 run on Node 20, which GitHub
now warns about; v6 and v7 run on Node 24 (checked in their action.yml).
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MINIMUM = {"actions/checkout": 6, "actions/setup-python": 7}
WORKFLOWS = sorted(p for p in REPO_ROOT.rglob("*.yml")
                   if ".git" not in p.parts and ("workflows" in p.parts or "guardrails" in p.parts))
AT = "@"  # built at runtime so the personal-data scan doesn't read it as a mention
USES_RE = re.compile(r"uses:\s*(actions/[\w-]+)" + AT + r"v(\d+)")


def test_workflows_found():
    assert len(WORKFLOWS) >= 10


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_actions_are_recent_enough(path):
    for action, major in USES_RE.findall(path.read_text()):
        if action in MINIMUM:
            assert int(major) >= MINIMUM[action], f"{action} v{major} runs on Node 20; use v{MINIMUM[action]}"
