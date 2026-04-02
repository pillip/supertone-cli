"""Usage command: display API usage statistics."""

from __future__ import annotations

from dataclasses import asdict

import typer

from supertone_cli.client import get_usage
from supertone_cli.output import print_json


def register_usage_command(app: typer.Typer) -> None:
    """Register usage command on the main app."""

    @app.command("usage")
    def usage_cmd(
        format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: text or json.",
        ),
    ) -> None:
        """Display API usage statistics."""
        usage = get_usage()

        if format == "json":
            print_json(asdict(usage))
            return

        typer.echo(f"Plan:      {usage.plan}")
        typer.echo(f"Used:      {usage.used}")
        typer.echo(f"Remaining: {usage.remaining}")
