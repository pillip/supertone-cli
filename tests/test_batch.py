"""Tests for ISSUE-007: batch TTS processing."""

from unittest.mock import patch

from supertone_cli.cli import app
from supertone_cli.errors import InputError
from typer.testing import CliRunner

runner = CliRunner()


def _mock_create_speech(*args, **kwargs):
    return b"audio-bytes"


def _mock_create_speech_fail(*args, **kwargs):
    raise Exception("API timeout")


def test_batch_directory(tmp_path):
    """Batch processes .txt files from directory."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "a.txt").write_text("Hello A")
    (scripts_dir / "b.txt").write_text("Hello B")
    outdir = tmp_path / "audio"

    with patch(
        "supertone_cli.commands.tts.create_speech",
        side_effect=_mock_create_speech,
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "--input",
                str(scripts_dir),
                "--outdir",
                str(outdir),
                "--voice",
                "v1",
            ],
        )
    assert result.exit_code == 0
    assert (outdir / "a.wav").exists()
    assert (outdir / "b.wav").exists()


def test_batch_creates_outdir(tmp_path):
    """--outdir is created if it doesn't exist."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "a.txt").write_text("Hello")
    outdir = tmp_path / "new_dir"

    with patch(
        "supertone_cli.commands.tts.create_speech",
        side_effect=_mock_create_speech,
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "--input",
                str(scripts_dir),
                "--outdir",
                str(outdir),
                "--voice",
                "v1",
            ],
        )
    assert result.exit_code == 0
    assert outdir.exists()


def test_batch_empty_dir_raises(tmp_path):
    """Empty directory raises InputError."""
    scripts_dir = tmp_path / "empty"
    scripts_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "tts",
            "--input",
            str(scripts_dir),
            "--outdir",
            str(tmp_path / "out"),
            "--voice",
            "v1",
        ],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


def test_batch_partial_failure(tmp_path):
    """Per-file error continues processing."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "a.txt").write_text("Hello A")
    (scripts_dir / "b.txt").write_text("Hello B")
    outdir = tmp_path / "audio"

    call_count = 0

    def _fail_first(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("API error")
        return b"audio"

    with patch(
        "supertone_cli.commands.tts.create_speech",
        side_effect=_fail_first,
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "--input",
                str(scripts_dir),
                "--outdir",
                str(outdir),
                "--voice",
                "v1",
            ],
        )
    # Exit code 1 because some files failed
    assert result.exit_code != 0


def test_batch_fail_fast(tmp_path):
    """--fail-fast stops on first error."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "a.txt").write_text("Hello A")
    (scripts_dir / "b.txt").write_text("Hello B")
    outdir = tmp_path / "audio"

    with patch(
        "supertone_cli.commands.tts.create_speech",
        side_effect=_mock_create_speech_fail,
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "--input",
                str(scripts_dir),
                "--outdir",
                str(outdir),
                "--voice",
                "v1",
                "--fail-fast",
            ],
        )
    assert result.exit_code != 0
