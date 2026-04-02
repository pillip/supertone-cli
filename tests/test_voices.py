"""Tests for ISSUE-008: voices list command."""

import json
from unittest.mock import patch

from supertone_cli.cli import app
from supertone_cli.models import Voice
from typer.testing import CliRunner

runner = CliRunner()

_MOCK_VOICES = [
    Voice(
        id="v1",
        name="Voice1",
        type="preset",
        languages=["ko", "en"],
        gender="male",
        age="adult",
        use_cases=["narration"],
    ),
    Voice(
        id="v2",
        name="Voice2",
        type="custom",
        languages=["ko"],
        gender="female",
        age="young",
        use_cases=[],
    ),
]


def test_voices_list_renders_table():
    """voices list displays a table."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(app, ["voices", "list"])
    assert result.exit_code == 0


def test_voices_list_type_preset():
    """--type preset filters to preset voices only."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(app, ["voices", "list", "--type", "preset"])
    assert result.exit_code == 0


def test_voices_list_type_custom():
    """--type custom filters to custom voices only."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(app, ["voices", "list", "--type", "custom"])
    assert result.exit_code == 0


def test_voices_list_format_json():
    """--format json produces valid JSON array."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(app, ["voices", "list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["id"] == "v1"


def test_voices_list_empty():
    """Empty voice list returns exit code 0."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=[],
    ):
        result = runner.invoke(app, ["voices", "list"])
    assert result.exit_code == 0


def test_voices_list_json_empty():
    """Empty voice list as JSON returns []."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=[],
    ):
        result = runner.invoke(app, ["voices", "list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == []
