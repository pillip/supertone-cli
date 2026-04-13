"""Tests for ISSUE-023 _attr helper refactoring.

The refactor should be behavior-preserving. This test verifies:
1. The _attr helper exists
2. The hasattr count in client.py dropped by at least 20
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_attr_helper_exists():
    """client.py defines a private _attr helper function."""
    content = (ROOT / "src" / "supertone_cli" / "client.py").read_text()
    assert "def _attr(" in content


def test_hasattr_count_reduced():
    """hasattr usage in client.py is reduced by at least 20 from baseline of 47."""
    content = (ROOT / "src" / "supertone_cli" / "client.py").read_text()
    count = len(re.findall(r"hasattr\(", content))
    assert count <= 27, f"hasattr count is {count}, expected <= 27 (baseline 47, need -20)"
