"""Fixtures for the guardrail recipe tests."""

from pathlib import Path

import pytest

from helpers import Repo


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    return Repo(tmp_path)
