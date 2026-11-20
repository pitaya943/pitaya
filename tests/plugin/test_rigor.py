"""P1 of the Level Max plan (D46): cheap rigor adapted from pstack's skills.

- /plan sharpens the brief and explores how and why before cutting work.
- PRs carry a decision log, failures included, for whoever merges.
- /verify proves the one fact a wide change's safety rests on (blast radius).
- /retro fixes repeated mistakes at the highest level that works (the correct
  ladder) and keeps only lessons that will still hold.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "plugin" / "skills"


def read(rel: str) -> str:
    return (SKILLS / rel).read_text()


def test_plan_sharpens_and_explores_first():
    skill = read("plan/SKILL.md")
    assert "sharpen.md" in skill
    sharpen = read("plan/sharpen.md")
    for idea in ("deeper", "top professional", "verif", "how", "why"):
        assert idea in sharpen.lower(), idea


def test_pr_template_has_an_append_only_decision_log():
    text = read("build/pr-template.md")
    assert "## Decision log" in text
    assert "| When | Decision | Options | Why this one | Evidence | Result |" in text
    assert "failed" in text.lower()


def test_builders_keep_the_decision_log_as_they_go():
    text = read("build/SKILL.md")
    assert "Decision log" in text and "dead end" in text.lower()


def test_verifier_reads_the_log_and_checks_blast_radius():
    text = read("verify/checklist.md")
    assert "Blast radius" in text and "one fact" in text
    assert "Decision log" in text


def test_retro_uses_the_correct_ladder_in_order():
    text = read("retro/SKILL.md")
    order = [text.index(step) for step in ("Architecture", "Types, lint or CI", "Tests", "Docs or skills")]
    assert order == sorted(order)
    assert "real past mistake" in text
    assert "six months" in text
    assert "Decision log" in text


def test_report_draws_on_decision_logs():
    assert "decision log" in read("report/SKILL.md").lower()


def test_verdict_template_has_a_row_per_checklist_item():
    checklist = read("verify/checklist.md")
    items = re.findall(r"^(\d+)\. \*\*(.+?)\.\*\*", checklist, re.M)
    template = read("verify/verdict-template.md")
    rows = re.findall(r"^\| (\d+) \| ([^|]+?) \|", template, re.M)
    assert [n for n, _ in items] == [n for n, _ in rows]
    for (number, name), (_, short) in zip(items, rows):
        assert short.split()[0].lower() in name.lower(), (number, name, short)
