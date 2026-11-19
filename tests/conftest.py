"""Make the helper modules in tests/ (pii_scan) importable from every test."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
