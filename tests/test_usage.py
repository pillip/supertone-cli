"""Tests for ISSUE-012: usage command."""

import json
from unittest.mock import patch

from supertone_cli.cli import app
from supertone_cli.errors import APIError
from supertone_cli.models import Usage
from typer.testing import CliRunner

runner = CliRunner()

_MOCK_USAGE = Usage(plan="pro", used=100, remaining=900)


def test_usage_human_readable():
    """usage displays Plan, Used, Remaining."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        return_value=_MOCK_USAGE,
    ):
        result = runner.invoke(app, ["usage"])
    assert result.exit_code == 0
    assert "pro" in result.output
    assert "100" in result.output
    assert "900" in result.output


def test_usage_format_json():
    """--format json produces valid JSON."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        return_value=_MOCK_USAGE,
    ):
        result = runner.invoke(app, ["usage", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["plan"] == "pro"
    assert data["used"] == 100
    assert data["remaining"] == 900


def test_usage_api_error():
    """API error results in non-zero exit."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        side_effect=APIError("server down"),
    ):
        result = runner.invoke(app, ["usage"])
    assert result.exit_code != 0
