"""Voices commands: list, search, clone."""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional

import typer

from supertone_cli.client import list_voices
from supertone_cli.output import print_json, print_table

voices_app = typer.Typer(name="voices", help="Voice management commands.")


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

    # Filter by type if requested
    if type:
        voices = [v for v in voices if v.type == type]

    if format == "json":
        print_json([asdict(v) for v in voices])
        return

    # Table output
    if not voices:
        # Print empty table with headers
        print_table(
            ["Name", "ID", "Type", "Languages"],
            [],
        )
        return

    rows = [[v.name, v.id, v.type, ", ".join(v.languages)] for v in voices]
    print_table(["Name", "ID", "Type", "Languages"], rows)

    # Hint for custom filter with no results
    if type == "custom" and not voices:
        typer.echo(
            "No custom voices found. Use 'supertone voices clone' to create one.",
            err=True,
        )
