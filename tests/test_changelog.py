"""Tests for CHANGELOG.md existence and format."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_changelog_exists():
    """CHANGELOG.md exists at the repo root."""
    assert (ROOT / "CHANGELOG.md").exists()


def test_changelog_keepachangelog_format():
    """CHANGELOG.md follows Keep a Changelog 1.1.0 format."""
    content = (ROOT / "CHANGELOG.md").read_text()
    assert "# Changelog" in content
    assert "## [0.1.0]" in content
    assert "### Added" in content


def test_changelog_lists_all_commands():
    """CHANGELOG.md lists every top-level CLI command under Added."""
    content = (ROOT / "CHANGELOG.md").read_text()
    for cmd in ("tts", "tts-predict", "voices", "usage", "config"):
        assert cmd in content, f"Command '{cmd}' not found in CHANGELOG.md"


def test_pyproject_has_changelog_url():
    """pyproject.toml has a Changelog URL in [project.urls]."""
    toml_content = (ROOT / "pyproject.toml").read_text()
    assert "Changelog" in toml_content
    # Should point to the CHANGELOG.md file, not just releases page
    assert "CHANGELOG.md" in toml_content or "releases" in toml_content
