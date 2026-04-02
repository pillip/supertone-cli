"""Tests for ISSUE-014: startup latency and lazy imports."""

import os
import subprocess
import sys
import time
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")


def test_startup_under_500ms():
    """supertone --help subprocess completes in < 500ms (10-run median)."""
    env = {**os.environ, "PYTHONPATH": _SRC_DIR}
    times = []
    for _ in range(10):
        start = time.perf_counter()
        subprocess.run(
            [sys.executable, "-m", "supertone_cli.cli", "--help"],
            capture_output=True,
            env=env,
        )
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    times.sort()
    median = times[len(times) // 2]
    assert median < 0.5, f"Median startup time {median:.3f}s exceeds 500ms"


def test_cli_no_module_level_command_imports():
    """cli.py should not import command modules at module level."""
    cli_path = (
        Path(__file__).resolve().parent.parent / "src" / "supertone_cli" / "cli.py"
    )
    content = cli_path.read_text()

    # SDK must not be imported in cli.py at all
    assert "import supertone" not in content

    # Command modules should not be imported at top level
    # (they should be registered lazily)
    lines = content.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Check for module-level imports of heavy modules
        if stripped.startswith("from supertone_cli.commands."):
            # This line must be indented (inside a function)
            assert line.startswith(" "), (
                f"Line {i + 1}: command import at module level: {stripped}"
            )


def test_client_lazy_sdk_import():
    """client.py should only import supertone inside function bodies."""
    client_path = (
        Path(__file__).resolve().parent.parent / "src" / "supertone_cli" / "client.py"
    )
    content = client_path.read_text()
    lines = content.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import supertone") or stripped.startswith(
            "from supertone "
        ):
            # Must be indented (inside a function), not at top level
            assert line.startswith(" "), (
                f"Line {i + 1}: SDK import at module level: {stripped}"
            )
