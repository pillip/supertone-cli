# Review Notes — ISSUE-022

## Code Review
- **Verdict**: Approved
- Clear 3-tier priority in _is_auth_error: isinstance -> status_code -> string fallback
- Removed overly broad "auth" keyword from string heuristic
- String fallback only activates for non-SDK exceptions (no status_code attr)
- SDK exceptions with status_code always use code-based classification
- 4 new tests with real assertions covering typed, status_code, and anti-regression
- All existing tests pass unchanged

## Security Findings
- None. Auth error detection is now more precise, reducing false positives.

## Follow-ups
- None
