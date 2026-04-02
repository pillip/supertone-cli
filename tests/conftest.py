"""Shared test fixtures for supertone-cli."""

import sys
from pathlib import Path

# Ensure src/ is on sys.path so supertone_cli can be imported without installation
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
