"""Tests for ISSUE-015: CI pipeline YAML validity."""

from pathlib import Path

import yaml


def test_ci_workflow_exists():
    """CI workflow file exists."""
    wf = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
    assert wf.exists(), "CI workflow file not found"


def test_ci_workflow_valid_yaml():
    """CI workflow is valid YAML."""
    wf = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
    content = wf.read_text()
    data = yaml.safe_load(content)
    assert isinstance(data, dict)
    assert "jobs" in data


def test_ci_workflow_has_test_job():
    """CI workflow has a test job."""
    wf = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
    data = yaml.safe_load(wf.read_text())
    assert "test" in data["jobs"]


def test_ci_workflow_has_python_matrix():
    """CI workflow tests multiple Python versions."""
    wf = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
    data = yaml.safe_load(wf.read_text())
    strategy = data["jobs"]["test"].get("strategy", {})
    matrix = strategy.get("matrix", {})
    python_versions = matrix.get("python-version", [])
    assert len(python_versions) >= 2, "Should test at least 2 Python versions"
