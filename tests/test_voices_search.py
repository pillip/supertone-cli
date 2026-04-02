"""Tests for ISSUE-009: voices search command."""

import json
from unittest.mock import patch

from supertone_cli.cli import app
from supertone_cli.errors import InputError
from supertone_cli.models import Voice
from typer.testing import CliRunner

runner = CliRunner()

_MOCK_VOICES = [
    Voice(
        id="v1",
        name="Voice1",
        type="preset",
        languages=["ko"],
        gender="female",
        age="young",
        use_cases=["narration"],
    ),
]


def test_search_with_lang():
    """--lang ko returns results."""
    with patch(
        "supertone_cli.commands.voices.search_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(app, ["voices", "search", "--lang", "ko"])
    assert result.exit_code == 0


def test_search_multiple_filters():
    """Multiple filters are passed."""
    with patch(
        "supertone_cli.commands.voices.search_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(
            app,
            ["voices", "search", "--lang", "ko", "--gender", "female"],
        )
    assert result.exit_code == 0


def test_search_no_filters_raises():
    """No filters raises InputError."""
    result = runner.invoke(app, ["voices", "search"])
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


def test_search_format_json():
    """--format json produces valid JSON."""
    with patch(
        "supertone_cli.commands.voices.search_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(
            app,
            ["voices", "search", "--lang", "ko", "--format", "json"],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_search_empty_result():
    """Empty result returns exit code 0."""
    with patch(
        "supertone_cli.commands.voices.search_voices",
        return_value=[],
    ):
        result = runner.invoke(app, ["voices", "search", "--lang", "xx"])
    assert result.exit_code == 0
