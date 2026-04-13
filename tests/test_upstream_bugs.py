"""Tests for ISSUE-024 upstream bug tracking documentation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_todo_marker_in_client():
    """client.py has a TODO(ISSUE-024) marker near list_custom_voices."""
    content = (ROOT / "src" / "supertone_cli" / "client.py").read_text()
    assert "WORKAROUND(ISSUE-024)" in content or "TODO(ISSUE-024)" in content


def test_upstream_bugs_doc_exists():
    """docs/upstream_bugs.md exists with repro details."""
    upstream = ROOT / "docs" / "upstream_bugs.md"
    assert upstream.exists(), "docs/upstream_bugs.md should exist"
    content = upstream.read_text()
    assert "list_custom_voices" in content
    assert "supertone" in content.lower()
    assert "0.2" in content  # SDK version reference
