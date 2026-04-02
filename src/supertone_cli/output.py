"""Output formatting: tables, JSON, progress bars, TTY detection.

Human-readable output goes to stderr (via Rich Console).
Machine-readable data (JSON) goes to stdout.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Sequence

from rich.console import Console
from rich.progress import Progress
from rich.table import Table


def _no_color() -> bool:
    """Check if color output should be suppressed (NO_COLOR convention)."""
    return os.environ.get("NO_COLOR", "") != ""


# Stderr console for human-readable output (tables, progress, errors).
_stderr_console = Console(stderr=True, no_color=_no_color())


def is_pipe() -> bool:
    """Return True if stdout is not connected to a TTY (i.e., piped)."""
    return not sys.stdout.isatty()


def print_json(data: Any) -> None:
    """Write *data* as pretty-printed JSON to stdout."""
    sys.stdout.write(json.dumps(data, indent=2, ensure_ascii=False))
    sys.stdout.write("\n")


def print_error(message: str) -> None:
    """Print an error message to stderr."""
    _stderr_console.print(f"[bold red]Error:[/bold red] {message}")


def print_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    """Render a Rich table to stderr."""
    table = Table(show_header=True, header_style="bold")
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    _stderr_console.print(table)


def create_progress() -> Progress:
    """Create a Rich Progress bar that renders to stderr (TTY only)."""
    return Progress(console=_stderr_console, disable=not sys.stderr.isatty())
