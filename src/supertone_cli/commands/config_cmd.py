"""Config commands: init, set, get, list."""

from __future__ import annotations

import sys

import typer

from supertone_cli.config import (
    VALID_CONFIG_KEYS,
    load_config,
    save_config,
)
from supertone_cli.errors import InputError

config_app = typer.Typer(name="config", help="Manage CLI configuration.")


@config_app.command("set")
def set_value(key: str, value: str) -> None:
    """Set a configuration value."""
    if key not in VALID_CONFIG_KEYS:
        valid = ", ".join(sorted(VALID_CONFIG_KEYS))
        raise InputError(f"Unknown config key: {key}. Valid keys: {valid}")
    if key == "api_key" and not value.strip():
        raise InputError("api_key cannot be empty.")

    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
    typer.echo(f"Set {key}.")


@config_app.command("get")
def get_value(key: str) -> None:
    """Get a configuration value."""
    if key not in VALID_CONFIG_KEYS:
        valid = ", ".join(sorted(VALID_CONFIG_KEYS))
        raise InputError(f"Unknown config key: {key}. Valid keys: {valid}")
    cfg = load_config()
    val = cfg.get(key)
    if val is None:
        raise InputError(f"{key} is not set. Use: supertone config set {key} <value>")
    typer.echo(val)


@config_app.command("list")
def list_values() -> None:
    """List all configuration values."""
    cfg = load_config()
    if not cfg:
        return
    for k, v in sorted(cfg.items()):
        display = "***" if k == "api_key" and v else v
        typer.echo(f"{k} = {display}")


@config_app.command("init")
def init() -> None:
    """Interactive configuration setup (TTY only)."""
    if not sys.stdin.isatty():
        raise InputError(
            "config init requires an interactive terminal. Use 'config set' instead."
        )

    api_key = typer.prompt("API key", default="")
    default_voice = typer.prompt("Default voice ID (leave empty to skip)", default="")
    default_model = typer.prompt("Default model", default="sona_speech_2")
    default_lang = typer.prompt("Default language", default="ko")

    cfg: dict[str, str] = {}
    if api_key:
        cfg["api_key"] = api_key
    if default_voice:
        cfg["default_voice"] = default_voice
    if default_model:
        cfg["default_model"] = default_model
    if default_lang:
        cfg["default_lang"] = default_lang

    save_config(cfg)
    typer.echo("Configuration saved.")
