"""Tests for ISSUE-013: streaming TTS playback."""

from unittest.mock import MagicMock, patch

from supertone_cli.cli import app
from supertone_cli.errors import InputError
from typer.testing import CliRunner

runner = CliRunner()


def test_stream_calls_stream_speech():
    """--stream calls client.stream_speech."""
    mock_chunks = [b"chunk1", b"chunk2"]
    mock_sd = MagicMock()

    with (
        patch(
            "supertone_cli.client.stream_speech",
            return_value=iter(mock_chunks),
        ),
        patch.dict("sys.modules", {"sounddevice": mock_sd}),
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "Hello",
                "--voice",
                "v1",
                "--stream",
                "--model",
                "sona_speech_1",
            ],
        )
    assert result.exit_code == 0


def test_stream_missing_sounddevice():
    """Missing sounddevice raises InputError."""
    with patch.dict("sys.modules", {"sounddevice": None}):
        result = runner.invoke(
            app,
            [
                "tts",
                "Hello",
                "--voice",
                "v1",
                "--stream",
                "--model",
                "sona_speech_1",
            ],
        )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


def test_stream_with_file_save(tmp_path):
    """--stream + --output saves to file too."""
    mock_chunks = [b"chunk1", b"chunk2"]
    mock_sd = MagicMock()
    out = tmp_path / "out.wav"

    with (
        patch(
            "supertone_cli.client.stream_speech",
            return_value=iter(mock_chunks),
        ),
        patch.dict("sys.modules", {"sounddevice": mock_sd}),
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "Hello",
                "--voice",
                "v1",
                "--stream",
                "--model",
                "sona_speech_1",
                "--output",
                str(out),
            ],
        )
    assert result.exit_code == 0
    assert out.exists()
    assert out.read_bytes() == b"chunk1chunk2"
