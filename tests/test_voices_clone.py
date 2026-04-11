"""Tests for ISSUE-011: voices clone command."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from supertone_cli.cli import app
from supertone_cli.errors import InputError
from supertone_cli.models import CloneResult

runner = CliRunner()


def test_clone_success(tmp_path):
    """Clone with valid file prints voice_id."""
    sample = tmp_path / "sample.wav"
    sample.write_bytes(b"fake audio")
    mock_result = CloneResult(voice_id="clone-1", name="my-voice")
    with patch(
        "supertone_cli.client.clone_voice",
        return_value=mock_result,
    ):
        result = runner.invoke(
            app,
            ["voices", "clone", "--name", "my-voice", "--sample", str(sample)],
        )
    assert result.exit_code == 0
    assert "clone-1" in result.output


def test_clone_format_json(tmp_path):
    """--format json produces valid JSON."""
    sample = tmp_path / "sample.wav"
    sample.write_bytes(b"fake audio")
    mock_result = CloneResult(voice_id="clone-1", name="my-voice")
    with patch(
        "supertone_cli.client.clone_voice",
        return_value=mock_result,
    ):
        result = runner.invoke(
            app,
            [
                "voices",
                "clone",
                "--name",
                "my-voice",
                "--sample",
                str(sample),
                "--format",
                "json",
            ],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["voice_id"] == "clone-1"


def test_clone_missing_file():
    """Missing sample file raises InputError."""
    result = runner.invoke(
        app,
        ["voices", "clone", "--name", "test", "--sample", "/missing.wav"],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


def test_clone_unsupported_format(tmp_path):
    """Unsupported format raises InputError."""
    sample = tmp_path / "sample.aac"
    sample.write_bytes(b"fake")
    result = runner.invoke(
        app,
        ["voices", "clone", "--name", "test", "--sample", str(sample)],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)
