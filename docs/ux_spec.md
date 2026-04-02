# UX Spec — Supertone CLI (Phase 1)

**Version**: 1.0
**Date**: 2026-04-03
**Source**: PRD Digest v1.0, Requirements v1.0
**Confidence**: High — PRD and requirements are detailed; all user stories map to flows below.

---

## Information Architecture

### Command Hierarchy

```
supertone                          # Root — prints help summary
├── tts <text>                     # Text-to-speech generation
│   └── predict <text>             # Duration/credit estimation (no generation)
├── voices                         # Voice management group
│   ├── list                       # List available voices
│   ├── search                     # Filter/search voices
│   └── clone                      # Register a custom voice from audio sample
├── usage                          # API usage summary
├── config                         # Configuration management group
│   ├── init                       # Interactive first-time setup
│   ├── set <key> <value>          # Set a single config value
│   ├── get <key>                  # Read a single config value
│   └── list                       # Print all config key-value pairs
├── --help / -h                    # Global help (also available per subcommand)
└── --version                      # Print version and exit
```

### Config Resolution Order (highest priority first)

1. CLI flags (e.g., `--voice`)
2. Environment variables (`SUPERTONE_API_KEY`)
3. Config file (`~/.config/supertone/config.toml`)
4. Built-in defaults (model: `sona_speech_2`, lang: `ko`, format: `wav`)

---

## Key Flows

### Flow: First-Time Setup

- **Trigger**: User installs the CLI (`pip install supertone-cli`) and runs any command for the first time.
- **Steps**:
  1. User runs `supertone tts "Hello"`.
  2. CLI detects no API key in env var or config file.
  3. CLI prints to stderr: `Error: No API key found. Run "supertone config init" or set SUPERTONE_API_KEY.`
  4. CLI exits with code 2.
  5. User runs `supertone config init`.
  6. CLI prompts interactively for `api_key` (required), `default_voice` (optional), `default_model` (optional, shows choices), `default_lang` (optional, default: ko).
  7. CLI writes `~/.config/supertone/config.toml` with permissions 600.
  8. CLI prints to stderr: `Configuration saved to ~/.config/supertone/config.toml`
- **Success**: Config file exists with valid API key. User can now run TTS commands.
- **Error paths**:
  - User presses Ctrl+C during init: CLI exits cleanly with no partial config file written. Exit code 1.
  - User enters an empty API key: CLI repeats the prompt with message `API key is required.`
  - Config directory `~/.config/supertone/` cannot be created (permission denied): Exit code 1 with message `Error: Cannot create config directory ~/.config/supertone/ — check file system permissions.`
- **Edge cases**:
  - Config file already exists: `config init` pre-fills existing values; pressing Enter without typing retains the existing value.
  - stdin is not a TTY (piped): `config init` exits with code 3 and message `Error: "config init" requires an interactive terminal. Use "supertone config set <key> <value>" instead.`

---

### Flow: Single Text-to-Speech Generation

- **Trigger**: User runs `supertone tts "Hello world" --voice <id>`.
- **Steps**:
  1. CLI parses arguments and resolves voice/model/lang from flags, then config, then defaults.
  2. CLI validates that exactly one input source is active (positional arg in this case).
  3. CLI validates parameter compatibility with selected model (e.g., `--similarity` not allowed on `sona_speech_2_flash`).
  4. CLI sends request to Supertone TTS API.
  5. While waiting: if stdout is a TTY, a spinner with `Generating...` is displayed on stderr.
  6. API returns audio data.
  7. CLI writes audio to `output.wav` (or `--output <path>`).
  8. CLI prints to stderr: `Saved: output.wav (3.2s, 47 credits)`
  9. CLI exits with code 0.
- **Success**: Audio file written to disk; metadata summary on stderr.
- **Error paths**:
  - No voice specified and no default configured: Exit code 3. Message: `Error: No voice specified. Use --voice <id> or set a default with "supertone config set default_voice <id>".`
  - Invalid API key: Exit code 2. Message: `Error: Authentication failed — check your API key. Run "supertone config set api_key <key>" or verify SUPERTONE_API_KEY.`
  - API returns error (rate limit, server error): Exit code 1. Message: `Error: API request failed (429 Too Many Requests). Try again later.`
  - Network unreachable: Exit code 1. Message: `Error: Cannot reach the Supertone API. Check your network connection.`
  - Output path is not writable: Exit code 1. Message: `Error: Cannot write to "path/output.wav" — check directory permissions.`
  - Incompatible model/parameter combination: Exit code 3. Message: `Error: --similarity is not supported by model sona_speech_2_flash. Remove the flag or use a different model.`
  - Ambiguous input (both positional text and `--input` provided): Exit code 3. Message: `Error: Ambiguous input — provide text as a positional argument, --input file, or stdin, but not more than one.`
- **Edge cases**:
  - Empty text string `""`: Exit code 3. Message: `Error: Text input is empty. Provide non-empty text.`
  - Very long text: CLI passes as-is; API enforces limits and CLI propagates the error.

---

### Flow: File Input TTS

- **Trigger**: User runs `supertone tts --input script.txt --output narration.mp3 --output-format mp3`.
- **Steps**:
  1. CLI reads `script.txt` contents.
  2. CLI sends text to TTS API with format=mp3.
  3. CLI writes audio to `narration.mp3`.
  4. CLI prints to stderr: `Saved: narration.mp3 (12.5s, 180 credits)`
- **Success**: MP3 file written.
- **Error paths**:
  - File does not exist: Exit code 3. Message: `Error: File not found: "script.txt".`
  - File is empty: Exit code 3. Message: `Error: File "script.txt" is empty.`
  - File is not readable: Exit code 3. Message: `Error: Cannot read file "script.txt" — check file permissions.`

---

### Flow: Piped Input / Stdout Output (Pipeline Mode)

- **Trigger**: `echo "Hello" | supertone tts --output - | ffmpeg -i pipe:0 -f mp3 out.mp3`
- **Steps**:
  1. CLI detects stdin is not a TTY; reads piped text.
  2. CLI detects `--output -`; all human-readable output goes to stderr only.
  3. Progress indicators and ANSI colors are suppressed (stdout is piped).
  4. API returns audio; CLI writes raw audio bytes to stdout.
  5. CLI prints nothing to stdout except audio bytes. Metadata summary goes to stderr.
  6. Exit code 0.
- **Success**: Audio bytes flow through the pipe to the next process.
- **Error paths**:
  - Both stdin text and positional argument provided: Exit code 3. Message on stderr: `Error: Ambiguous input — provide text as a positional argument, --input file, or stdin, but not more than one.`
  - stdin is a TTY and no text/file argument: Exit code 3. Message on stderr: `Error: No input provided. Pass text as an argument, use --input <file>, or pipe text via stdin.`
  - `--format json` combined with `--output -`: Exit code 3. Message on stderr: `Error: Cannot use --format json with --output - (both write to stdout). Use --output <file> with --format json.`

---

### Flow: Batch Processing

- **Trigger**: `supertone tts --input ./scripts/ --outdir ./audio/ --voice <id>`
- **Steps**:
  1. CLI resolves input: directory `./scripts/` -- collects all top-level `.txt` files.
  2. CLI creates `--outdir` if it does not exist.
  3. CLI displays progress bar on stderr (if TTY): `Processing: [====      ] 3/10 files`
  4. For each file, CLI calls TTS API and writes output to `./audio/<filename>.<format>`.
  5. If a file fails, error is logged to stderr and processing continues (unless `--fail-fast`).
  6. After all files: summary on stderr: `Batch complete: 9 succeeded, 1 failed.`
  7. Exit code 0 if all succeed; exit code 1 if any file failed.
- **Success**: All output files written; summary printed.
- **Error paths**:
  - Input directory does not exist: Exit code 3. Message: `Error: Directory not found: "./scripts/".`
  - No `.txt` files found in directory: Exit code 3. Message: `Error: No .txt files found in "./scripts/".`
  - Glob pattern matches no files: Exit code 3. Message: `Error: No files match pattern "scripts/*.md".`
  - `--fail-fast` and a file fails: Processing stops immediately. Message: `Error: Failed on "script3.txt" (API error). Stopping — 2 succeeded, 1 failed. Use without --fail-fast to continue on errors.`
  - `--outdir` cannot be created: Exit code 1. Message: `Error: Cannot create output directory "./audio/" — check permissions.`
- **Edge cases**:
  - Unquoted glob expanded by shell: CLI receives multiple `--input` values. Exit code 3 with message: `Error: Multiple --input values received. If using a glob pattern, quote it: --input "scripts/*.txt".`
  - Stdout is not TTY: Progress bar suppressed; only the final summary line is written to stderr.

---

### Flow: Streaming TTS Playback

- **Trigger**: `supertone tts "Hello world" --stream --model sona_speech_1`
- **Steps**:
  1. CLI validates `--stream` is used with `sona_speech_1`.
  2. CLI opens streaming connection to API.
  3. Audio chunks are played to system audio output in real time.
  4. If `--output <file>` is also provided, audio is simultaneously written to the file.
  5. Playback completes. CLI prints to stderr: `Streamed: 3.2s`
  6. Exit code 0.
- **Error paths**:
  - Model is not `sona_speech_1`: Exit code 3. Message: `Error: Streaming is only supported with model sona_speech_1. Current model: sona_speech_2.`
  - Audio playback device unavailable: Exit code 1. Message: `Error: No audio output device found. Check your system audio settings.`
  - Network interruption during streaming: Exit code 1. Message: `Error: Stream interrupted — network connection lost.`

---

### Flow: TTS Duration Prediction

- **Trigger**: `supertone tts predict "Hello world" --voice <id>`
- **Steps**:
  1. CLI parses text input (same sources as `tts`: positional, `--input`, stdin).
  2. CLI calls Predict Duration API.
  3. CLI prints to stdout (human-readable): `Duration: 3.2s | Estimated credits: 47`
  4. Exit code 0.
- **Success**: Duration and credit estimate displayed; no credits consumed.
- **Error paths**:
  - Same input errors as TTS (missing text, file not found, ambiguous input).
  - API error: Exit code 1 with error message on stderr.
- **Edge cases**:
  - `--format json`: Output is `{"duration_seconds": 3.2, "estimated_credits": 47}` on stdout.

---

### Flow: List Voices

- **Trigger**: `supertone voices list`
- **Steps**:
  1. CLI calls Voices API.
  2. CLI renders table on stdout:
     ```
     Name              ID                  Type     Languages
     ──────────────────────────────────────────────────────────
     Aria              voice_abc123        preset   en, ko, ja
     My Narrator       voice_xyz789        custom   ko
     ```
  3. Exit code 0.
- **Success**: Table of voices displayed.
- **Error paths**:
  - Authentication failure: Exit code 2.
  - API error: Exit code 1.
- **Edge cases**:
  - No voices available: Empty table with headers only is printed. Exit code 0.
  - `--type preset`: Only preset voices shown.
  - `--type custom`: Only custom voices shown. If none exist, empty table with message on stderr: `No custom voices found. Create one with "supertone voices clone".`
  - `--format json`: JSON array on stdout. Empty array `[]` if no results.

---

### Flow: Search Voices

- **Trigger**: `supertone voices search --lang ko --gender female --use-case narration`
- **Steps**:
  1. CLI sends filter parameters to Voices API (AND logic for all filters).
  2. CLI renders filtered table on stdout (same format as `voices list`).
  3. Exit code 0.
- **Success**: Filtered voice results displayed.
- **Error paths**:
  - No filters provided: Exit code 3. Message: `Error: Provide at least one filter (--lang, --gender, --age, --use-case, or --query).`
  - Authentication/API errors: Same as `voices list`.
- **Edge cases**:
  - No matching voices: Empty table printed. Helpful message on stderr: `No voices match the given filters. Try broadening your search.`
  - `--format json`: JSON array on stdout.

---

### Flow: Clone Voice

- **Trigger**: `supertone voices clone --name "my-narrator" --sample ./voice_sample.wav`
- **Steps**:
  1. CLI validates `--sample` file exists and format is supported.
  2. CLI uploads sample to Voice Cloning API. Progress on stderr: `Uploading voice sample...`
  3. API returns `voice_id`.
  4. CLI prints to stdout: `voice_xyz789`
  5. CLI prints to stderr: `Voice "my-narrator" created. Use it with: supertone tts --voice voice_xyz789`
  6. Exit code 0.
- **Success**: Voice registered; voice_id printed to stdout for capture by scripts.
- **Error paths**:
  - Sample file not found: Exit code 3. Message: `Error: File not found: "./voice_sample.wav".`
  - Unsupported audio format: Exit code 3. Message: `Error: Unsupported audio format ".aac". Supported formats: wav, mp3, ogg, flac.`
  - Upload failure (API error): Exit code 1. Message on stderr.
  - `--name` not provided: Exit code 3. Message: `Error: --name is required. Provide a name for your custom voice.`
- **Edge cases**:
  - `--format json`: Output is `{"voice_id": "voice_xyz789", "name": "my-narrator"}` on stdout.

---

### Flow: Check Usage

- **Trigger**: `supertone usage`
- **Steps**:
  1. CLI calls Usage API.
  2. CLI prints to stdout:
     ```
     Plan:       Pro
     Used:       12,450 credits
     Remaining:  37,550 credits
     ```
  3. Exit code 0.
- **Success**: Usage summary displayed.
- **Error paths**:
  - Authentication failure: Exit code 2.
  - API error: Exit code 1.
- **Edge cases**:
  - `--format json`: Output is `{"plan": "Pro", "used": 12450, "remaining": 37550}` on stdout.

---

### Flow: Config Management (set/get/list)

- **Trigger**: `supertone config set default_voice voice_abc123`
- **Steps**:
  1. CLI writes key-value to `~/.config/supertone/config.toml`.
  2. CLI sets file permissions to 600.
  3. CLI prints to stderr: `Set default_voice = voice_abc123`
  4. Exit code 0.
- **Success**: Config value persisted.
- **Error paths**:
  - Invalid key: Exit code 3. Message: `Error: Unknown config key "foo". Valid keys: api_key, default_voice, default_model, default_lang.`
  - Cannot write config file: Exit code 1. Message: `Error: Cannot write to ~/.config/supertone/config.toml — check permissions.`

**`config get <key>`**:
- Key exists: Prints value to stdout. Exit code 0.
- Key not set: Exit code 3. Message: `Error: Key "default_voice" is not set. Use "supertone config set default_voice <value>".`

**`config list`**:
- Prints all key-value pairs to stdout:
  ```
  api_key = sk-...redacted
  default_voice = voice_abc123
  default_model = sona_speech_2
  default_lang = ko
  ```
- No config file: Prints nothing. Exit code 0.
- PRD note: `config get api_key` returns the unmasked key. `config list` displays it masked for casual viewing safety. Assumption: masking only in `list`, not in `get`. (See Assumption A-3 in requirements.)

---

## Terminal Output States

Every command output has the following possible states. These replace the concept of "screen states" in a GUI context.

### Default (Success)

The command completes normally. Structured data on stdout, human summary on stderr.

### Loading / In-Progress

- **Single TTS**: Spinner on stderr: `Generating...` (only when stdout is TTY).
- **Batch TTS**: Progress bar on stderr: `Processing: [====      ] 3/10 files` (only when stdout is TTY).
- **Voice Clone Upload**: Indeterminate spinner on stderr: `Uploading voice sample...`
- **Non-TTY**: All progress indicators suppressed. Only final summary appears on stderr.

### Empty

- `voices list` with no results: Table headers with no rows. Exit code 0.
- `voices search` with no matches: Empty table. Stderr hint: `No voices match the given filters. Try broadening your search.`
- `config list` with no config file: No output. Exit code 0.
- Batch with no matching files: Exit code 3. Error message.

### Error

All errors follow this pattern on stderr:
```
Error: <what went wrong>. <how to fix it>.
```

Exit codes:
| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success | Command completed normally |
| 1 | General error | API error, network failure, file write failure |
| 2 | Authentication error | Missing or invalid API key |
| 3 | Input/usage error | Bad arguments, missing required flags, incompatible parameters |

### Piped / Non-TTY Mode

When stdout is not a TTY:
- ANSI color codes are disabled.
- Progress bars and spinners are disabled.
- Table formatting may be simplified (no box-drawing characters).
- Only structured data (audio bytes, JSON, plain text values) flows to stdout.
- All human-readable messages remain on stderr.

---

## Copy Guidelines

### Tone

Technical but approachable. Direct and concise. The user is comfortable with a terminal. No filler words. Every message is actionable.

### Command Help Text Pattern

Each command's `--help` follows this structure:
```
<one-line description>

Usage: supertone <command> [OPTIONS] [ARGS]

Arguments:
  <arg>    Description

Options:
  --flag   Description [default: value]

Examples:
  supertone tts "Hello world"
  supertone tts --input script.txt --output narration.wav
  echo "Hello" | supertone tts --output -
```

### Error Message Pattern

```
Error: <cause>. <fix>.
```

Examples:
- `Error: No API key found. Run "supertone config init" or set SUPERTONE_API_KEY.`
- `Error: File not found: "script.txt".`
- `Error: --similarity is not supported by model sona_speech_2_flash. Remove the flag or use a different model.`
- `Error: Ambiguous input — provide text as a positional argument, --input file, or stdin, but not more than one.`
- `Error: Authentication failed — check your API key. Run "supertone config set api_key <key>" or verify SUPERTONE_API_KEY.`
- `Error: Cannot reach the Supertone API. Check your network connection.`
- `Error: Streaming is only supported with model sona_speech_1. Current model: sona_speech_2.`
- `Error: Unknown config key "foo". Valid keys: api_key, default_voice, default_model, default_lang.`

### Success Message Pattern (stderr)

- `Saved: output.wav (3.2s, 47 credits)`
- `Batch complete: 9 succeeded, 1 failed.`
- `Voice "my-narrator" created. Use it with: supertone tts --voice voice_xyz789`
- `Set default_voice = voice_abc123`
- `Configuration saved to ~/.config/supertone/config.toml`
- `Streamed: 3.2s`

### Interactive Prompt Pattern (config init)

```
Supertone CLI Setup

API Key: ****
Default Voice ID (press Enter to skip):
Default Model [sona_speech_2]:
Default Language [ko]:

Configuration saved to ~/.config/supertone/config.toml
```

### Prediction Output (human-readable)

```
Duration: 3.2s | Estimated credits: 47
```

### Usage Output (human-readable)

```
Plan:       Pro
Used:       12,450 credits
Remaining:  37,550 credits
```

### Table Output (voices list/search)

```
Name              ID                  Type     Languages
──────────────────────────────────────────────────────────
Aria              voice_abc123        preset   en, ko, ja
Bright Narrator   voice_def456        preset   ko, en
My Narrator       voice_xyz789        custom   ko
```

---

## Accessibility

### General Terminal Accessibility

- All meaningful output uses plain text, not relying solely on ANSI color or box-drawing characters to convey information.
- Color is used for enhancement only; information is conveyed by text content and structure.
- Error messages always include the word "Error:" as a text prefix, not just red coloring.
- Progress status includes numeric counts (e.g., `3/10 files`) in addition to any visual bar.

### Screen Reader Considerations

- Table output uses consistent column alignment and headers so screen readers can parse rows.
- No decorative ASCII art in output.
- `--format json` provides a fully machine-parseable alternative to all tabular output, which screen readers handle well through JSON-aware tools.
- Interactive prompts (`config init`) use clear label text before each input field.

### Keyboard / Terminal Navigation

- Ctrl+C cleanly interrupts any running command and prints no partial/garbled output.
- Interactive `config init` supports standard readline key bindings (arrow keys, Ctrl+A/E for line navigation).
- No command requires a mouse or graphical terminal.

### Non-TTY / Automation Accessibility

- When stdout is not a TTY, all formatting that could interfere with screen readers or piped processing is stripped.
- Exit codes are the primary machine-readable success/failure signal.
- `--format json` is available on every data-returning command for programmatic consumption.

### Contrast and Readability

- The CLI uses the terminal's default foreground/background colors. It does not set background colors.
- Bold and dim text styles are used sparingly. Key information (file paths, voice IDs, error causes) uses bold.
- The `NO_COLOR` environment variable convention is respected: if `NO_COLOR` is set, all ANSI styling is disabled regardless of TTY detection.

---

## User Story Coverage Matrix

| User Story | Flow(s) | Covered |
|------------|---------|---------|
| US-1 (single TTS) | Single Text-to-Speech Generation | Yes |
| US-2 (file input) | File Input TTS | Yes |
| US-3 (voice/model params) | Single TTS (parameter validation) | Yes |
| US-3 streaming (streaming) | Streaming TTS Playback | Yes |
| US-4 (predict duration) | TTS Duration Prediction | Yes |
| US-5 (piped input) | Piped Input / Stdout Output | Yes |
| US-6 (stdout output) | Piped Input / Stdout Output | Yes |
| US-7 (batch) | Batch Processing | Yes |
| US-8 (JSON output) | All flows via `--format json` | Yes |
| US-9 (list voices) | List Voices | Yes |
| US-10 (search voices) | Search Voices | Yes |
| US-11 (clone voice) | Clone Voice | Yes |
| US-12 (preset vs custom) | List Voices (`--type` flag) | Yes |
| US-13 (API key setup) | First-Time Setup, Config Management | Yes |
| US-14 (default settings) | Config Management | Yes |
| US-15 (usage) | Check Usage | Yes |

---

## Assumptions Made in This Spec

1. **PRD does not specify the root command behavior**: Assumed `supertone` with no subcommand prints the help summary (same as `supertone --help`).
2. **PRD does not specify `--version` flag**: Assumed standard `--version` flag is present on the root command.
3. **PRD does not specify `config list` masking behavior**: Assumed `config list` masks the API key for casual safety, while `config get api_key` returns the full unmasked value. (See requirements Assumption A-3.)
4. **PRD does not specify `voices search` behavior with zero filters**: Assumed exit code 3 requiring at least one filter, to distinguish from `voices list`.
5. **PRD does not specify `NO_COLOR` support**: Assumed the CLI respects the `NO_COLOR` environment variable convention (see https://no-color.org/).
6. **PRD does not specify error message language**: Assumed English for all CLI output (error messages, help text, labels). The TTS content itself supports multiple languages; the CLI interface is English-only.
