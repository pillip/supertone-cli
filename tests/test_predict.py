"""Tests for ISSUE-010: TTS predict subcommand."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from supertone_cli.cli import app
from supertone_cli.models import Prediction

runner = CliRunner()

_MOCK_PREDICTION = Prediction(duration_seconds=3.2, estimated_credits=47)


def test_predict_human_readable():
    """predict displays duration and credits."""
    with patch(
        "supertone_cli.client.predict_duration",
        return_value=_MOCK_PREDICTION,
    ):
        result = runner.invoke(
            app,
            ["tts-predict", "Hello", "--voice", "v1"],
        )
    assert result.exit_code == 0
    assert "3.2" in result.output
    assert "47" in result.output


def test_predict_format_json():
    """--format json produces valid JSON."""
    with patch(
        "supertone_cli.client.predict_duration",
        return_value=_MOCK_PREDICTION,
    ):
        result = runner.invoke(
            app,
            ["tts-predict", "Hello", "--voice", "v1", "--format", "json"],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["duration_seconds"] == 3.2
    assert data["estimated_credits"] == 47


def test_predict_file_input(tmp_path):
    """--input reads file for prediction."""
    txt = tmp_path / "script.txt"
    txt.write_text("Hello from file")
    with patch(
        "supertone_cli.client.predict_duration",
        return_value=_MOCK_PREDICTION,
    ):
        result = runner.invoke(
            app,
            ["tts-predict", "--input", str(txt), "--voice", "v1"],
        )
    assert result.exit_code == 0


def test_predict_no_file_created(tmp_path, monkeypatch):
    """predict does not create any files."""
    monkeypatch.chdir(tmp_path)
    with patch(
        "supertone_cli.client.predict_duration",
        return_value=_MOCK_PREDICTION,
    ):
        result = runner.invoke(
            app,
            ["tts-predict", "Hello", "--voice", "v1"],
        )
    assert result.exit_code == 0
    assert not list(tmp_path.iterdir())
