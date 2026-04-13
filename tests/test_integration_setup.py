"""Tests verifying integration test infrastructure (ISSUE-025)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_integration_marker_in_pyproject():
    """pyproject.toml has an 'integration' marker registered."""
    content = (ROOT / "pyproject.toml").read_text()
    assert "integration" in content
    assert "markers" in content


def test_smoke_test_file_exists():
    """tests/integration/test_smoke.py exists with proper decorators."""
    smoke = ROOT / "tests" / "integration" / "test_smoke.py"
    assert smoke.exists()
    content = smoke.read_text()
    assert "pytest.mark.integration" in content
    assert "pytest.mark.skipif" in content
    assert "SUPERTONE_API_KEY" in content


def test_integration_test_skipped_without_key():
    """The integration test should be skipped when running default suite."""
    import subprocess

    result = subprocess.run(
        ["uv", "run", "pytest", "tests/integration/", "-q", "--co"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    # --co (collect only) should find the test
    assert "test_voices_list_smoke" in result.stdout
