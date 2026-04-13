"""Tests for usage commands."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from supertone_cli.cli import app
from supertone_cli.errors import APIError
from supertone_cli.models import Usage

runner = CliRunner()

_MOCK_USAGE = Usage(plan="pro", used=100, remaining=900)


def test_usage_balance_human_readable():
    """usage balance displays Plan, Used, Remaining."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        return_value=_MOCK_USAGE,
    ):
        result = runner.invoke(app, ["usage", "balance"])
    assert result.exit_code == 0
    assert "pro" in result.output
    assert "100" in result.output
    assert "900" in result.output


def test_usage_balance_format_json():
    """--format json produces valid JSON."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        return_value=_MOCK_USAGE,
    ):
        result = runner.invoke(app, ["usage", "balance", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["plan"] == "pro"
    assert data["used"] == 100
    assert data["remaining"] == 900


def test_usage_balance_api_error():
    """API error results in non-zero exit."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        side_effect=APIError("server down"),
    ):
        result = runner.invoke(app, ["usage", "balance"])
    assert result.exit_code != 0


# ── usage analytics ──────────────────────────────────────────────────


_MOCK_ANALYTICS = [
    {
        "period_start": "2026-04-01T00:00:00Z",
        "period_end": "2026-04-02T00:00:00Z",
        "minutes_used": 12.34,
        "voice_id": "v1",
        "voice_name": "Voice1",
        "model": "sona_speech_2",
    }
]


def test_usage_analytics_table():
    """usage analytics renders a table for a date range."""
    with patch(
        "supertone_cli.client.get_usage_analytics",
        return_value=_MOCK_ANALYTICS,
    ):
        result = runner.invoke(
            app,
            ["usage", "analytics", "--start", "2026-04-01", "--end", "2026-04-30"],
        )
    assert result.exit_code == 0


def test_usage_analytics_json():
    """usage analytics --format json returns the raw list."""
    with patch(
        "supertone_cli.client.get_usage_analytics",
        return_value=_MOCK_ANALYTICS,
    ):
        result = runner.invoke(
            app,
            [
                "usage",
                "analytics",
                "--start",
                "2026-04-01",
                "--end",
                "2026-04-30",
                "--format",
                "json",
            ],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["minutes_used"] == 12.34


def test_usage_analytics_empty():
    """usage analytics with no data prints a friendly message."""
    with patch(
        "supertone_cli.client.get_usage_analytics",
        return_value=[],
    ):
        result = runner.invoke(
            app,
            ["usage", "analytics", "--start", "2026-04-01", "--end", "2026-04-02"],
        )
    assert result.exit_code == 0
    assert "No usage data" in result.output


# ── usage voices ─────────────────────────────────────────────────────


_MOCK_VOICE_USAGE = [
    {
        "date": "2026-04-01",
        "voice_id": "v1",
        "name": "Voice1",
        "minutes_used": 5.5,
        "model": "sona_speech_2",
        "language": "ko",
    }
]


def test_usage_voices_table():
    """usage voices renders per-voice breakdown as table."""
    with patch(
        "supertone_cli.client.get_voice_usage",
        return_value=_MOCK_VOICE_USAGE,
    ):
        result = runner.invoke(
            app,
            ["usage", "voices", "--start", "2026-04-01", "--end", "2026-04-30"],
        )
    assert result.exit_code == 0


def test_usage_voices_json():
    """usage voices --format json returns the raw list."""
    with patch(
        "supertone_cli.client.get_voice_usage",
        return_value=_MOCK_VOICE_USAGE,
    ):
        result = runner.invoke(
            app,
            [
                "usage",
                "voices",
                "--start",
                "2026-04-01",
                "--end",
                "2026-04-30",
                "--format",
                "json",
            ],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["voice_id"] == "v1"
