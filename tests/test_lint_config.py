"""Tests for lint configuration consolidation (ISSUE-026)."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_no_ruff_toml_at_root():
    """No ruff.toml file or symlink exists at the repo root."""
    ruff_toml = ROOT / "ruff.toml"
    assert not ruff_toml.exists() and not ruff_toml.is_symlink(), (
        "ruff.toml should not exist at the repo root"
    )


def test_no_prettierrc_at_root():
    """No .prettierrc.json symlink exists at the repo root."""
    prettierrc = ROOT / ".prettierrc.json"
    assert not prettierrc.exists() and not prettierrc.is_symlink(), (
        ".prettierrc.json should not exist at the repo root"
    )


def test_pyproject_has_extend_exclude():
    """pyproject.toml has extend-exclude with .claude-kit and .venv."""
    content = (ROOT / "pyproject.toml").read_text()
    assert "extend-exclude" in content
    assert ".claude-kit" in content
    assert ".venv" in content


def test_ruff_check_exits_clean():
    """uv run ruff check . exits 0 (no errors from .claude-kit or .venv)."""
    result = subprocess.run(
        ["uv", "run", "ruff", "check", "."],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, (
        f"ruff check failed:\n{result.stdout}\n{result.stderr}"
    )
