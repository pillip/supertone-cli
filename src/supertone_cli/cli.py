"""Top-level Typer app and entry point."""

from __future__ import annotations

import typer

from supertone_cli import __version__

app = typer.Typer(
    name="supertone",
    help="Supertone TTS CLI — generate speech from the terminal.",
    no_args_is_help=True,
)


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
    app()


if __name__ == "__main__":
    main()
