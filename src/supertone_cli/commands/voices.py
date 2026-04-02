"""Voices commands: list, search, clone."""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional

import typer

from supertone_cli.client import list_voices, search_voices
from supertone_cli.errors import InputError
from supertone_cli.output import print_json, print_table

SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".ogg", ".flac"}

voices_app = typer.Typer(name="voices", help="Voice management commands.")


def _render_voices(voices: list, format: str) -> None:
    """Render a list of Voice objects as table or JSON."""
    if format == "json":
        print_json([asdict(v) for v in voices])
        return

    if not voices:
        print_table(["Name", "ID", "Type", "Languages"], [])
        return

    rows = [[v.name, v.id, v.type, ", ".join(v.languages)] for v in voices]
    print_table(["Name", "ID", "Type", "Languages"], rows)


@voices_app.command("list")
def list_cmd(
    type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by voice type: preset or custom.",
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """List available voices."""
    voices = list_voices()
    if type:
        voices = [v for v in voices if v.type == type]
    _render_voices(voices, format)
    if type == "custom" and not voices:
        typer.echo(
            "No custom voices found. Use 'supertone voices clone' to create one.",
            err=True,
        )


@voices_app.command("search")
def search_cmd(
    lang: Optional[str] = typer.Option(None, "--lang", help="Language code."),
    gender: Optional[str] = typer.Option(None, "--gender", help="Voice gender."),
    age: Optional[str] = typer.Option(None, "--age", help="Voice age."),
    use_case: Optional[str] = typer.Option(None, "--use-case", help="Use case."),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Keyword search."),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """Search voices with filters."""
    filters = {}
    if lang:
        filters["lang"] = lang
    if gender:
        filters["gender"] = gender
    if age:
        filters["age"] = age
    if use_case:
        filters["use_case"] = use_case
    if query:
        filters["query"] = query

    if not filters:
        raise InputError(
            "At least one filter is required. "
            "Use --lang, --gender, --age, --use-case, or --query."
        )

    voices = search_voices(**filters)
    _render_voices(voices, format)

    if not voices:
        typer.echo(
            "No voices match the given filters.",
            err=True,
        )


@voices_app.command("clone")
def clone_cmd(
    name: str = typer.Option(..., "--name", "-n", help="Name for the cloned voice."),
    sample: str = typer.Option(
        ..., "--sample", "-s", help="Path to audio sample file."
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """Clone a voice from an audio sample."""
    from pathlib import Path

    from supertone_cli.client import clone_voice

    p = Path(sample)
    if not p.exists():
        raise InputError(f"File not found: {sample}")

    suffix = p.suffix.lower()
    if suffix not in SUPPORTED_AUDIO_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_AUDIO_FORMATS))
        raise InputError(f"Unsupported audio format: {suffix}. Supported: {supported}")

    result = clone_voice(name, str(p))

    if format == "json":
        print_json(asdict(result))
        return

    typer.echo(result.voice_id)
    typer.echo(
        f"Voice '{name}' created. "
        f'Use: supertone tts --voice {result.voice_id} "text"',
        err=True,
    )
