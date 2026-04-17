"""Tests for ISSUE-003: config module and config commands."""

import os
import stat
import sys
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from supertone_cli.cli import app

runner = CliRunner()


# ── config.py unit tests ────────────────────────────────────────────


def test_save_config_creates_toml(tmp_path):
    from supertone_cli.config import save_config

    config_file = tmp_path / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        save_config({"api_key": "sk-test123"})

    assert config_file.exists()
    content = config_file.read_text()
    assert 'api_key = "sk-test123"' in content


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows NTFS does not honor POSIX mode bits; chmod(0o600) is a no-op.",
)
def test_save_config_sets_600_permissions(tmp_path):
    from supertone_cli.config import save_config

    config_file = tmp_path / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        save_config({"api_key": "test"})

    mode = stat.S_IMODE(config_file.stat().st_mode)
    assert mode == 0o600


def test_load_config_returns_dict(tmp_path):
    from supertone_cli.config import load_config, save_config

    config_file = tmp_path / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        save_config({"api_key": "sk-test", "default_voice": "v1"})
        data = load_config()

    assert data["api_key"] == "sk-test"
    assert data["default_voice"] == "v1"


def test_load_config_returns_empty_when_no_file(tmp_path):
    from supertone_cli.config import load_config

    config_file = tmp_path / "nonexistent" / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        data = load_config()

    assert data == {}


def test_get_api_key_returns_env_var():
    from supertone_cli.config import get_api_key

    with patch.dict(os.environ, {"SUPERTONE_API_KEY": "sk-env"}):
        assert get_api_key() == "sk-env"


def test_get_api_key_returns_config_value(tmp_path):
    from supertone_cli.config import get_api_key, save_config

    config_file = tmp_path / "config.toml"
    with (
        patch("supertone_cli.config.CONFIG_PATH", config_file),
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("SUPERTONE_API_KEY", None)
        save_config({"api_key": "sk-cfg"})
        result = get_api_key()

    assert result == "sk-cfg"


def test_get_api_key_returns_none_when_nothing_set(tmp_path):
    from supertone_cli.config import get_api_key

    config_file = tmp_path / "nonexistent" / "config.toml"
    with (
        patch("supertone_cli.config.CONFIG_PATH", config_file),
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("SUPERTONE_API_KEY", None)
        result = get_api_key()

    assert result is None


# ── CLI command tests ────────────────────────────────────────────────


def test_config_set_and_get_roundtrip(tmp_path):
    config_file = tmp_path / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        result = runner.invoke(app, ["config", "set", "api_key", "sk-test123"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["config", "get", "api_key"])
        assert result.exit_code == 0
        assert "sk-test123" in result.output


def test_config_set_invalid_key(tmp_path):
    config_file = tmp_path / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        result = runner.invoke(app, ["config", "set", "invalid_key", "value"])
        assert result.exit_code != 0


def test_config_set_empty_api_key(tmp_path):
    config_file = tmp_path / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        result = runner.invoke(app, ["config", "set", "api_key", ""])
        assert result.exit_code != 0


def test_config_list_no_file(tmp_path):
    config_file = tmp_path / "nonexistent" / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        result = runner.invoke(app, ["config", "list"])
        assert result.exit_code == 0


def test_config_get_unset_key(tmp_path):
    config_file = tmp_path / "nonexistent" / "config.toml"
    with patch("supertone_cli.config.CONFIG_PATH", config_file):
        result = runner.invoke(app, ["config", "get", "default_voice"])
        assert result.exit_code != 0
