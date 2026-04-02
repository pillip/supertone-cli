# Review Notes — ISSUE-005

## Code Review

**Verdict**: Approved

### Findings
- **Severity: Info** — _resolve_text properly enforces exactly-one-source rule.
- **Severity: Info** — register_tts_command pattern avoids Typer sub-group issues with positional args.
- **Severity: Info** — Output routing correctly handles file, stdout, and default paths.
- **Severity: Info** — JSON metadata output goes to stdout only when --format json is set.

### Changes Made
None required.

### Follow-ups
- ISSUE-010 will add `tts predict` subcommand (may need refactoring to group).

## Security Findings

**Verdict**: No issues

- File input reads text only, no code execution risk.
- Output writes to user-specified paths only.
- No secrets in command output.
