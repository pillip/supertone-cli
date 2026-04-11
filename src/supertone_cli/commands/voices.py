"""Voices commands: list, search, clone, get, edit, delete."""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional

import typer

from supertone_cli.client import (
    list_custom_voices,
    list_voices,
    search_voices,
)
from supertone_cli.errors import InputError
from supertone_cli.output import print_json, print_table

SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3"}

voices_app = typer.Typer(
    name="voices",
    help="Voice management commands.",
)


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
        help="Filter: preset or custom.",
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """List available voices."""
    if type == "custom":
        voices = list_custom_voices()
    else:
        voices = list_voices()
        if type == "preset":
            voices = [v for v in voices if v.type == "preset"]
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


@voices_app.command("get")
def get_cmd(
    voice_id: str = typer.Argument(help="Voice ID."),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """Get details of a specific voice."""
    from supertone_cli.client import get_voice

    voice = get_voice(voice_id)

    if format == "json":
        print_json(asdict(voice))
        return

    typer.echo(f"Name:      {voice.name}")
    typer.echo(f"ID:        {voice.id}")
    typer.echo(f"Type:      {voice.type}")
    typer.echo(f"Languages: {', '.join(voice.languages)}")
    if voice.gender:
        typer.echo(f"Gender:    {voice.gender}")
    if voice.age:
        typer.echo(f"Age:       {voice.age}")
    if voice.use_cases:
        typer.echo(f"Use cases: {', '.join(voice.use_cases)}")


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


@voices_app.command("edit")
def edit_cmd(
    voice_id: str = typer.Argument(help="Custom voice ID."),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New name."),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New description."
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """Edit a custom voice's name or description."""
    from supertone_cli.client import edit_custom_voice

    if not name and not description:
        raise InputError("Provide --name or --description to update.")

    result = edit_custom_voice(voice_id, name=name, description=description)

    if format == "json":
        print_json(asdict(result))
        return

    typer.echo(f"Updated voice {result.voice_id}.")


@voices_app.command("delete")
def delete_cmd(
    voice_id: str = typer.Argument(help="Custom voice ID."),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation.",
    ),
) -> None:
    """Delete a custom voice."""
    from supertone_cli.client import delete_custom_voice

    if not yes:
        confirm = typer.confirm(f"Delete custom voice {voice_id}?")
        if not confirm:
            raise typer.Abort()

    delete_custom_voice(voice_id)
    typer.echo(f"Deleted voice {voice_id}.")
