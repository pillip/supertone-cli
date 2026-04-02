"""Smoke tests for ISSUE-001: project scaffold."""

import os
import subprocess
import sys
from pathlib import Path

from supertone_cli import __version__
from supertone_cli.cli import app
from typer.testing import CliRunner

runner = CliRunner()

# src/ path for subprocess PYTHONPATH
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")


def test_import_supertone_cli():
    """Importing supertone_cli must succeed."""
    import supertone_cli

    assert supertone_cli is not None


def test_cli_help_exits_zero():
    """supertone --help must exit with code 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "supertone" in result.output.lower() or "usage" in result.output.lower()


def test_cli_version_prints_string():
    """supertone --version must print a version string and exit 0."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_help_subprocess():
    """supertone --help via subprocess also works (with PYTHONPATH)."""
    env = {**os.environ, "PYTHONPATH": _SRC_DIR}
    result = subprocess.run(
        [sys.executable, "-m", "supertone_cli.cli", "--help"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0


def test_cli_version_subprocess():
    """supertone --version via subprocess also works."""
    env = {**os.environ, "PYTHONPATH": _SRC_DIR}
    result = subprocess.run(
        [sys.executable, "-m", "supertone_cli.cli", "--version"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert any(c.isdigit() for c in output), f"No version number in output: {output}"
