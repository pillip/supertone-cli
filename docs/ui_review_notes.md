# UI Review Notes — ISSUE-002

## State Coverage

**Verdict**: Adequate

- Error states: All error types (Auth, Input, API, unhandled) produce distinct exit codes and stderr messages.
- Empty states: Not applicable (no UI rendering beyond error messages).
- Loading states: `create_progress()` provides Rich progress bar for long operations.
- TTY detection: `is_pipe()` correctly distinguishes interactive vs piped output.

## Copy Compliance

**Verdict**: Compliant

- Error format follows pattern: `Error: <cause>` on stderr.
- JSON output uses `ensure_ascii=False` for proper unicode/Korean text support.
- NO_COLOR env var support follows the [no-color.org](https://no-color.org) convention.
- Table rendering uses Rich with bold headers — consistent with CLI conventions.

## Token Usage

Not applicable — no design tokens for CLI output formatting.

## Accessibility

- stderr/stdout separation ensures screen readers and pipe consumers get clean data.
- NO_COLOR support aids users who need plain text output.
