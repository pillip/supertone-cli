# Review Notes — ISSUE-025

## Code Review
- **Verdict**: Approved
- Integration marker properly registered in pyproject.toml
- test_smoke.py correctly gated with both pytest.mark.integration and pytest.mark.skipif
- Read-only smoke test (voices list) -- no destructive API calls
- CliRunner + JSON output parsing is correct
- Meta-tests verify infrastructure setup
- Integration test properly skipped in default runs (150 passed, 1 skipped)

## Security Findings
- None. API key is read from environment, not hardcoded.

## Follow-ups
- None
