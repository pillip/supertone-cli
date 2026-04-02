"""Error hierarchy for supertone-cli.

Exit codes:
  1 -- general CLI / API error
  2 -- authentication error
  3 -- input validation error
"""

from __future__ import annotations


class CLIError(Exception):
    """Base error for all CLI errors. Exit code 1."""

    exit_code: int = 1

    def __init__(self, message: str, *, exit_code: int | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class AuthError(CLIError):
    """Authentication error. Exit code 2."""

    exit_code: int = 2


class InputError(CLIError):
    """Input validation error. Exit code 3."""

    exit_code: int = 3


class APIError(CLIError):
    """API / network error. Exit code 1."""

    exit_code: int = 1


def sanitize_message(message: str, api_key: str | None) -> str:
    """Strip the API key from an error message to avoid leaking secrets."""
    if not api_key:
        return message
    return message.replace(api_key, "***")
