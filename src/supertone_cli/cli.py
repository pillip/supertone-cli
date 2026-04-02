"""Top-level Typer app and entry point."""

from __future__ import annotations

import os
import sys

import typer

from supertone_cli import __version__
from supertone_cli.commands.config_cmd import config_app
from supertone_cli.commands.tts import register_predict_command, register_tts_command
from supertone_cli.commands.usage import register_usage_command
from supertone_cli.commands.voices import voices_app
from supertone_cli.errors import CLIError, sanitize_message
from supertone_cli.output import print_error

app = typer.Typer(
    name="supertone",
    help="Supertone TTS CLI — generate speech from the terminal.",
    no_args_is_help=True,
)
app.add_typer(config_app)
app.add_typer(voices_app)
register_tts_command(app)
register_predict_command(app)
register_usage_command(app)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"supertone {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Supertone TTS CLI — generate speech from the terminal."""


def main() -> None:
    """Entry point registered in pyproject.toml [project.scripts]."""
    try:
        app()
    except CLIError as exc:
        api_key = os.environ.get("SUPERTONE_API_KEY", "")
        msg = sanitize_message(str(exc), api_key)
        print_error(msg)
        sys.exit(exc.exit_code)
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        # Silently handle broken pipes (e.g., `supertone ... | head`)
        sys.stderr.close()
        sys.exit(0)
    except Exception as exc:
        api_key = os.environ.get("SUPERTONE_API_KEY", "")
        msg = sanitize_message(str(exc), api_key)
        print_error(f"Unexpected error: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
