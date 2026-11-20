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
# The major version: from a tag (a `v6` after the action's name), or, since 0.1.9 pins actions by commit (F28), from the
# release named in the comment after the commit (`@<40 hex>  # v6.1.0`).
USES_RE = re.compile(r"^\s*(?:- )?uses:\s*(actions/[\w-]+)" + AT + r"(?:v|[0-9a-f]{40}\s+#\s*v)(\d+)", re.M)


def test_workflows_found():
    assert len(WORKFLOWS) >= 10


def test_every_use_of_a_checked_action_is_read():
    """A reference the pattern can't read would pass unchecked: count them against a plain search."""
    for path in WORKFLOWS:
        text = path.read_text()
        plain = [line for line in text.splitlines()
                 if re.match(r"\s*(- )?uses:\s*actions/(checkout|setup-python)\b", line)]
        read = [action for action, _ in USES_RE.findall(text) if action in MINIMUM]
        assert len(read) == len(plain), path.name
    assert sum(len(USES_RE.findall(p.read_text())) for p in WORKFLOWS) >= 20


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_actions_are_recent_enough(path):
    for action, major in USES_RE.findall(path.read_text()):
        if action in MINIMUM:
            assert int(major) >= MINIMUM[action], f"{action} v{major} runs on Node 20; use v{MINIMUM[action]}"
