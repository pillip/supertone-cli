"""Config module: read/write ~/.config/supertone/config.toml.

Resolution order: CLI flags > env vars > config file > built-in defaults.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

import tomli_w

CONFIG_PATH: Path = Path.home() / ".config" / "supertone" / "config.toml"

VALID_CONFIG_KEYS: set[str] = {
    "api_key",
    "default_voice",
    "default_model",
    "default_lang",
}


def load_config() -> dict[str, str]:
    """Read and return the config file as a dict. Returns {} if file missing."""
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def save_config(data: dict[str, str]) -> None:
    """Write config to TOML file, creating parent dirs and setting 0o600 perms."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("wb") as f:
        tomli_w.dump(data, f)
    CONFIG_PATH.chmod(0o600)


def get_api_key() -> str | None:
    """Return API key: env var first, then config file, else None."""
    env_key = os.environ.get("SUPERTONE_API_KEY")
    if env_key:
        return env_key
    cfg = load_config()
    return cfg.get("api_key") or None


def get_default(key: str) -> str | None:
    """Return a default value from config (e.g., default_voice)."""
    cfg = load_config()
    return cfg.get(key) or None
