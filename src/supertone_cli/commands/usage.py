"""Usage commands: credit balance, analytics, voice usage."""

from __future__ import annotations

from dataclasses import asdict

import typer

from supertone_cli.client import get_usage
from supertone_cli.output import print_json, print_table

usage_app = typer.Typer(name="usage", help="API usage commands.")


@usage_app.command("balance")
def balance_cmd(
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """Display API credit balance."""
    usage = get_usage()

    if format == "json":
        print_json(asdict(usage))
        return

    if usage.plan:
        typer.echo(f"Plan:    {usage.plan}")
    if usage.used:
        typer.echo(f"Used:    {usage.used}")
    typer.echo(f"Credits: {usage.remaining}")


@usage_app.command("analytics")
def analytics_cmd(
    start: str = typer.Option(..., "--start", help="Start time (YYYY-MM-DD)."),
    end: str = typer.Option(..., "--end", help="End time (YYYY-MM-DD)."),
    bucket: str = typer.Option(
        "day",
        "--bucket",
        help="Bucket width: day or hour.",
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """Show usage analytics for a date range."""
    from supertone_cli.client import get_usage_analytics

    results = get_usage_analytics(start, end, bucket)

    if format == "json":
        print_json(results)
        return

    if not results:
        typer.echo("No usage data for this period.")
        return

    rows = [
        [
            r["period_start"],
            r["period_end"],
            f"{r['minutes_used']:.2f}",
            r.get("voice_name") or r.get("voice_id") or "-",
            r.get("model") or "-",
        ]
        for r in results
    ]
    print_table(
        ["Start", "End", "Minutes", "Voice", "Model"],
        rows,
    )


@usage_app.command("voices")
def voice_usage_cmd(
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)."),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)."),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json.",
    ),
) -> None:
    """Show per-voice usage for a date range."""
    from supertone_cli.client import get_voice_usage

    results = get_voice_usage(start, end)

    if format == "json":
        print_json(results)
        return

    if not results:
        typer.echo("No voice usage data for this period.")
        return

    rows = [
        [
            r["date"],
            r.get("name") or r["voice_id"],
            f"{r['minutes_used']:.2f}",
            r.get("model") or "-",
            r.get("language") or "-",
        ]
        for r in results
    ]
    print_table(
        ["Date", "Voice", "Minutes", "Model", "Language"],
        rows,
    )
