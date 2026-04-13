"""Tests for ISSUE-005: single TTS command."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from supertone_cli.cli import app
from supertone_cli.errors import InputError

runner = CliRunner()


# ── Input resolution tests ───────────────────────────────────────────


def test_tts_positional_text(tmp_path):
    """Positional text arg creates output file."""
    out = tmp_path / "output.wav"
    with patch(
        "supertone_cli.commands.tts.create_speech",
        return_value=b"audio",
    ):
        result = runner.invoke(
            app,
            ["tts", "Hello world", "--voice", "v1", "--output", str(out)],
        )
    assert result.exit_code == 0
    assert out.exists()
    assert out.read_bytes() == b"audio"


def test_tts_file_input(tmp_path):
    """--input reads from text file."""
    txt = tmp_path / "script.txt"
    txt.write_text("Hello from file")
    out = tmp_path / "out.wav"
    with patch(
        "supertone_cli.commands.tts.create_speech",
        return_value=b"audio",
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "--input",
                str(txt),
                "--voice",
                "v1",
                "--output",
                str(out),
            ],
        )
    assert result.exit_code == 0
    assert out.exists()


def test_tts_missing_file_raises_input_error():
    """--input with missing file raises InputError."""
    result = runner.invoke(
        app,
        ["tts", "--input", "/nonexistent.txt", "--voice", "v1"],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)
    assert result.exception.exit_code == 3


def test_tts_empty_file_raises_input_error(tmp_path):
    """--input with empty file raises InputError."""
    txt = tmp_path / "empty.txt"
    txt.write_text("")
    result = runner.invoke(
        app,
        ["tts", "--input", str(txt), "--voice", "v1"],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


def test_tts_ambiguous_input_raises_input_error(tmp_path):
    """Both positional text and --input raises InputError."""
    txt = tmp_path / "script.txt"
    txt.write_text("Hello")
    result = runner.invoke(
        app,
        ["tts", "Hello", "--input", str(txt), "--voice", "v1"],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


def test_tts_no_voice_no_default_raises_input_error():
    """No --voice and no default_voice raises InputError."""
    with patch(
        "supertone_cli.commands.tts.get_default",
        return_value=None,
    ):
        result = runner.invoke(app, ["tts", "Hello"])
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


# ── Output routing tests ────────────────────────────────────────────


def test_tts_default_output_name(tmp_path, monkeypatch):
    """Default output is output.wav in cwd."""
    monkeypatch.chdir(tmp_path)
    with patch(
        "supertone_cli.commands.tts.create_speech",
        return_value=b"audio",
    ):
        result = runner.invoke(app, ["tts", "Hello", "--voice", "v1"])
    assert result.exit_code == 0
    assert (tmp_path / "output.wav").exists()


def test_tts_output_format_mp3(tmp_path, monkeypatch):
    """--output-format mp3 creates output.mp3."""
    monkeypatch.chdir(tmp_path)
    with patch(
        "supertone_cli.commands.tts.create_speech",
        return_value=b"audio",
    ):
        result = runner.invoke(
            app,
            ["tts", "Hello", "--voice", "v1", "--output-format", "mp3"],
        )
    assert result.exit_code == 0
    assert (tmp_path / "output.mp3").exists()


def test_tts_output_stdout():
    """--output - writes to stdout."""
    with patch(
        "supertone_cli.commands.tts.create_speech",
        return_value=b"audio",
    ):
        result = runner.invoke(
            app,
            ["tts", "Hello", "--voice", "v1", "--output", "-"],
        )
    assert result.exit_code == 0
    assert "audio" in result.output


# ── JSON format tests ────────────────────────────────────────────────


def test_tts_format_json(tmp_path):
    """--format json outputs JSON metadata to stdout."""
    out = tmp_path / "hello.wav"
    with patch(
        "supertone_cli.commands.tts.create_speech",
        return_value=b"audio",
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "Hello",
                "--voice",
                "v1",
                "--output",
                str(out),
                "--format",
                "json",
            ],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "output_file" in data
    assert "voice_id" in data


def test_tts_format_json_with_stdout_raises_input_error():
    """--format json + --output - raises InputError."""
    result = runner.invoke(
        app,
        [
            "tts",
            "Hello",
            "--voice",
            "v1",
            "--output",
            "-",
            "--format",
            "json",
        ],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


# ── Voice setting flag passthrough ───────────────────────────────────


def test_tts_voice_setting_flags_forwarded(tmp_path):
    """All voice setting flags reach create_speech as kwargs."""
    out = tmp_path / "out.wav"
    with patch(
        "supertone_cli.commands.tts.create_speech",
        return_value=b"audio",
    ) as mock_create:
        result = runner.invoke(
            app,
            [
                "tts",
                "Hello",
                "--voice",
                "v1",
                "--output",
                str(out),
                "--style",
                "calm",
                "--speed",
                "1.2",
                "--pitch",
                "-1.5",
                "--pitch-variance",
                "0.8",
                "--similarity",
                "0.9",
                "--text-guidance",
                "0.7",
            ],
        )
    assert result.exit_code == 0
    kwargs = mock_create.call_args.kwargs
    assert kwargs["style"] == "calm"
    assert kwargs["speed"] == 1.2
    assert kwargs["pitch_shift"] == -1.5
    assert kwargs["pitch_variance"] == 0.8
    assert kwargs["similarity"] == 0.9
    assert kwargs["text_guidance"] == 0.7


def test_tts_flash_rejects_similarity(tmp_path):
    """sona_speech_2_flash + --similarity raises InputError end-to-end."""
    out = tmp_path / "out.wav"
    result = runner.invoke(
        app,
        [
            "tts",
            "Hello",
            "--voice",
            "v1",
            "--model",
            "sona_speech_2_flash",
            "--similarity",
            "0.8",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


def test_tts_unsupported_output_format_raises():
    """--output-format ogg is rejected at CLI layer."""
    result = runner.invoke(
        app,
        ["tts", "Hello", "--voice", "v1", "--output-format", "ogg"],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)
