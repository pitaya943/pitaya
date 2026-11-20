"""pitaya in Claude Code cloud sessions (D54).

A cloud session loads the plugins its environment's setup script installs
(tested live: the skills were listed, and the Owner ran /pitaya:help). So the
cloud route is the same install with the commands in a different place, and
the skills keep their `pitaya:` names. Two things differ and are checked here:
the README says where the commands go, and the skills don't depend on `gh`,
which in cloud sessions may only search.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugin"
SKILLS = PLUGIN / "skills"


def test_readme_puts_the_install_in_the_environment_setup_script():
    text = (PLUGIN / "README.md").read_text()
    section = text.split("## Cloud sessions", 1)[1].split("\n## ", 1)[0]
    assert "setup script" in section
    for command in ("claude plugin marketplace add", "claude plugin install pitaya@pitaya"):
        assert command in section, command
    assert "/pitaya:help" in section  # how to check it worked


def test_every_gh_command_names_the_github_tool_alternative():
    for md in SKILLS.rglob("*.md"):
        for n, line in enumerate(md.read_text().splitlines(), 1):
            if re.search(r"`gh ", line):
                assert "GitHub tool" in line, f"{md.relative_to(PLUGIN)}:{n} names gh without the GitHub tool"


def test_one_naming_scheme():
    # The copy-into-.claude route (D51, D52) is gone, and with it the `pitaya-` names.
    assert not (SKILLS / "setup" / "scripts" / "vendor_plugin.py").exists()
    for path in PLUGIN.rglob("*.md"):
        assert "/pitaya-" not in path.read_text(), path
