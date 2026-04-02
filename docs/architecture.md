# Architecture

## Overview

**Architecture style**: Single-process Python CLI application (monolith).

**Justification**: Supertone CLI is a thin wrapper around an external SDK. There is no server, no database, no multi-user state, and no background processing beyond sequential or concurrent API calls. A single Python package with a clear module layout is the simplest architecture that meets every requirement. There is nothing to distribute, orchestrate, or scale independently.

**Key constraints driving the decision**:
- CLI startup must be < 500ms -- rules out heavy frameworks and demands lazy imports.
- Dependencies must be minimal (`supertone`, `typer`, `rich`) -- no room for infrastructure components.
- Distribution via PyPI as a single `pip install` -- must be a self-contained Python package.
- The entire data model is transient (config file + API calls); there is no application database.

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | PRD requirement; target user base |
| Package manager | uv | Team standard (claude.md) |
| CLI framework | Typer 0.x (latest stable) | PRD decision; Click-based, type hints, Rich integration |
| Rich output | Rich (via Typer) | Tables, progress bars, styled error messages |
| TTS engine | `supertone` Python SDK | Core dependency; pin minor version in pyproject.toml |
| Config format | TOML (stdlib `tomllib` read + `tomli_w` write) | PRD specifies TOML; `tomllib` is stdlib since 3.11, `tomli_w` is the lightweight write companion |
| Audio playback | `sounddevice` (optional dep) | Needed only for `--stream`; declared as optional extra |
| Testing | pytest + pytest-cov | Team standard; coverage > 80% target |
| Distribution | PyPI (`supertone-cli`) | PRD requirement |

**Version pinning rationale**: Pin `supertone` SDK to a compatible release range (e.g., `>=1.1.0,<2.0`) since the SDK API surface may change (Risk R-1). Pin Typer to `>=0.9,<1.0` for API stability. All other deps use standard compatible-release specifiers.

---

## Modules

### Module: `cli` (`src/supertone_cli/cli.py`)

- **Responsibility**: Top-level Typer app assembly; registers command groups, global options (`--version`), and the top-level exception handler.
- **Dependencies**: `commands/*` (lazy-imported)
- **Key interfaces**: `app` (Typer instance), `main()` entry point registered in `[project.scripts]`

### Module: `commands/tts` (`src/supertone_cli/commands/tts.py`)

- **Responsibility**: `supertone tts` and `supertone tts predict` commands. Handles input resolution (positional / `--input` / stdin), parameter validation, batch detection, and output routing.
- **Dependencies**: `client`, `config`, `output`
- **Key interfaces**:
  - `tts(text, input, output, voice, model, lang, ...)` -- single or batch TTS
  - `predict(text, input, voice, model, lang, format)` -- duration prediction

### Module: `commands/voices` (`src/supertone_cli/commands/voices.py`)

- **Responsibility**: `supertone voices list`, `search`, and `clone` subcommands.
- **Dependencies**: `client`, `output`
- **Key interfaces**:
  - `list_voices(type, format)`
  - `search_voices(lang, gender, age, use_case, query, format)`
  - `clone_voice(name, sample, format)`

### Module: `commands/usage` (`src/supertone_cli/commands/usage.py`)

- **Responsibility**: `supertone usage` command.
- **Dependencies**: `client`, `output`
- **Key interfaces**: `usage(format)`

### Module: `commands/config_cmd` (`src/supertone_cli/commands/config_cmd.py`)

- **Responsibility**: `supertone config init/set/get/list` subcommands. Named `config_cmd` to avoid shadowing the `config` module.
- **Dependencies**: `config`
- **Key interfaces**: `init()`, `set_value(key, value)`, `get_value(key)`, `list_values()`

### Module: `config` (`src/supertone_cli/config.py`)

- **Responsibility**: Read/write `~/.config/supertone/config.toml`, enforce 600 permissions, resolve values with env var override (`SUPERTONE_API_KEY` > config file > None).
- **Dependencies**: stdlib (`tomllib`, `pathlib`, `os`), `tomli_w`
- **Key interfaces**:
  - `load_config() -> dict` -- reads and returns config, merging env vars
  - `save_config(data: dict) -> None` -- writes TOML, sets permissions 600
  - `get_api_key() -> str | None` -- env var first, then config file
  - `get_default(key: str) -> str | None` -- returns default_voice, default_model, etc.
  - `CONFIG_PATH: Path` -- `~/.config/supertone/config.toml`

### Module: `client` (`src/supertone_cli/client.py`)

- **Responsibility**: Thin abstraction over the Supertone Python SDK. All SDK calls go through this module. Translates SDK exceptions into CLI-friendly errors with exit codes. This is the **only module that imports `supertone`**.
- **Dependencies**: `supertone` SDK, `config` (for API key)
- **Key interfaces**:
  - `get_client() -> Supertone` -- lazy singleton, initialized with API key
  - `create_speech(text, voice, model, lang, **params) -> bytes`
  - `stream_speech(text, voice, model, lang, **params) -> Iterator[bytes]`
  - `predict_duration(text, voice, model, lang) -> dict`
  - `list_voices() -> list[dict]`
  - `search_voices(**filters) -> list[dict]`
  - `clone_voice(name, sample_path) -> dict`
  - `get_usage() -> dict`

### Module: `output` (`src/supertone_cli/output.py`)

- **Responsibility**: Formatting layer. Renders tables (Rich), JSON, and progress bars. Detects TTY vs pipe and adjusts output accordingly. Routes human-readable output to stderr, data to stdout.
- **Dependencies**: `rich`, `json` (stdlib)
- **Key interfaces**:
  - `print_table(headers, rows, file=stderr)`
  - `print_json(data, file=stdout)`
  - `print_error(message, hint=None)` -- styled error to stderr
  - `create_progress() -> Progress` -- Rich progress bar on stderr
  - `is_pipe() -> bool` -- checks if stdout is a TTY

### Module: `errors` (`src/supertone_cli/errors.py`)

- **Responsibility**: Custom exception hierarchy mapping to exit codes. Top-level handler in `cli.py` catches these and calls `sys.exit()` with the correct code.
- **Dependencies**: none
- **Key interfaces**:
  - `CLIError(message, exit_code=1)` -- base
  - `AuthError(message)` -- exit code 2
  - `InputError(message)` -- exit code 3
  - `APIError(message)` -- exit code 1

---

## Data Model

This application has no database. All persistent state is a single TOML config file. All other data flows through the Supertone API as request/response.

### Entity: Config (`~/.config/supertone/config.toml`)

```toml
api_key = "sk-..."
default_voice = "voice-id-123"
default_model = "sona_speech_2"
default_lang = "ko"
```

- **Storage**: Local filesystem, single flat TOML file.
- **Constraints**: File permissions 600. Owner read/write only.
- **Migration strategy**: Not applicable for Phase 1. If config schema changes in Phase 2, add a `version` key and migrate on read.

### Entity: Voice (API response, not persisted locally)

Fields: `id` (string), `name` (string), `type` (enum: preset/custom), `languages` (list of strings), `gender` (string), `age` (string), `use_cases` (list of strings).

### Entity: Usage (API response, not persisted locally)

Fields: `used` (number), `remaining` (number), `plan` (string).

### Entity: Prediction (API response, not persisted locally)

Fields: `duration_seconds` (number), `estimated_credits` (number).

---

## API Design

This is a CLI, not a web service. The "API" is the command-line interface itself. Below are the commands mapped to functional requirements.

### Command: `supertone tts`

**Maps to**: FR-001, FR-002, FR-004

```
supertone tts [TEXT] [OPTIONS]

Arguments:
  TEXT                    Inline text to convert (optional)

Options:
  --input, -i PATH       Input file or directory or glob pattern
  --output, -o PATH      Output file path (use "-" for stdout)
  --outdir PATH          Output directory (batch mode)
  --voice TEXT            Voice ID
  --model TEXT            Model name [default: sona_speech_2]
  --lang TEXT             Language code [default: ko]
  --style TEXT            Style identifier
  --output-format TEXT    Audio format: wav|mp3|ogg|flac|aiff [default: wav]
  --speed FLOAT           Speaking speed
  --pitch FLOAT           Pitch adjustment
  --pitch-variance FLOAT  Pitch variance
  --similarity FLOAT      Similarity (not sona_speech_2_flash)
  --text-guidance FLOAT   Text guidance (not sona_speech_2_flash)
  --stream                Stream and play audio (sona_speech_1 only)
  --include-phonemes      Include phoneme data
  --fail-fast             Stop batch on first error
  --format TEXT           Output metadata format: text|json [default: text]
```

**Input resolution priority**: Exactly one of (TEXT arg, --input, stdin). Multiple sources -> exit 3.

**Batch detection**: If `--input` is a directory or glob pattern AND `--outdir` is provided, batch mode activates.

### Command: `supertone tts predict`

**Maps to**: FR-003

```
supertone tts predict [TEXT] [OPTIONS]

Arguments:
  TEXT                    Text to estimate

Options:
  --input, -i PATH       Input file
  --voice TEXT            Voice ID
  --model TEXT            Model name
  --lang TEXT             Language code
  --format TEXT           Output format: text|json
```

### Command: `supertone voices list`

**Maps to**: FR-005

```
supertone voices list [OPTIONS]

Options:
  --type TEXT             Filter: preset|custom
  --format TEXT           Output format: text|json
```

### Command: `supertone voices search`

**Maps to**: FR-006

```
supertone voices search [OPTIONS]

Options:
  --lang TEXT             Language filter
  --gender TEXT           Gender filter
  --age TEXT              Age filter
  --use-case TEXT         Use case filter
  --query TEXT            Keyword search
  --format TEXT           Output format: text|json
```

### Command: `supertone voices clone`

**Maps to**: FR-007

```
supertone voices clone [OPTIONS]

Options:
  --name TEXT             Voice name (required)
  --sample PATH           Audio sample file (required)
  --format TEXT           Output format: text|json
```

### Command: `supertone usage`

**Maps to**: FR-010

```
supertone usage [OPTIONS]

Options:
  --format TEXT           Output format: text|json
```

### Command: `supertone config`

**Maps to**: FR-008

```
supertone config init                    # Interactive setup
supertone config set <KEY> <VALUE>       # Set one key
supertone config get <KEY>               # Read one key
supertone config list                    # Show all keys
```

### Authentication scheme

- API key resolved by `config.get_api_key()`: env var `SUPERTONE_API_KEY` > config file `api_key` > None.
- If None, commands requiring auth exit with code 2 and a message instructing the user to set the key.
- The key is passed to the SDK client constructor. All API communication uses HTTPS (enforced by the SDK).

### Rate limiting / pagination

- Not applicable at the CLI layer. The Supertone API enforces rate limits; the CLI propagates HTTP 429 errors as exit code 1 with a retry message.
- Voice list endpoints are not expected to paginate for typical users. If the API returns paginated results, the `client.py` wrapper will iterate all pages transparently.

---

## Background Jobs

None. The CLI is a synchronous, single-invocation tool. Batch processing uses a sequential loop (not background workers). No daemon, no queue, no scheduler.

For batch mode, files are processed sequentially in a for-loop with a Rich progress bar. Concurrent batch processing (e.g., `asyncio.gather` or `ThreadPoolExecutor`) is deferred -- it adds complexity and the API may rate-limit parallel requests anyway.

---

## Observability

### Logging strategy

- **No application logging in Phase 1**. The CLI is a short-lived process; structured logging to a file adds operational burden with little benefit.
- All user-facing messages go to stderr via `output.print_error()`.
- Debug-level SDK logging can be enabled via the `SUPERTONE_LOG_LEVEL` environment variable if the SDK supports it.
- If debugging is needed, Python's standard `-v` / `PYTHONVERBOSE` or SDK-specific env vars are sufficient.

### Metrics

- **No runtime metrics collection**. The CLI is not a long-running service.
- Success metrics (install time, startup latency, coverage) are measured in CI and user testing as defined in the PRD.

### Alerting

- Not applicable. There is no server to alert on.

---

## Security

### Auth scheme

- API key stored in `~/.config/supertone/config.toml` with file permissions `0o600`.
- Environment variable `SUPERTONE_API_KEY` overrides config file (NFR-003).
- Key is passed to the SDK which transmits it over HTTPS only.

### Input validation strategy

- **Input source ambiguity**: Exactly one input source enforced at argument parsing. Ambiguity -> exit 3.
- **Model-parameter compatibility**: Validate that `--similarity` and `--text-guidance` are not used with `sona_speech_2_flash`, and `--stream` only with `sona_speech_1`. Validated before any API call.
- **File existence**: `--input` file checked before API call. `--sample` file checked before upload.
- **Audio format**: `--output-format` validated against the allowed enum. `--sample` format validated against SDK-supported formats before upload.
- **Glob/directory**: Validated that at least one file matches; empty match -> exit 3 with a message.

### Secrets management

- API key never appears in error messages, exception tracebacks, or log output.
- The `errors.py` exception handler strips any occurrence of the API key from messages before printing (defense in depth).
- Config file permissions are set to 600 on every write (not just creation).

### OWASP Top 10 mitigations (applicable subset for a CLI)

| Threat | Mitigation |
|--------|-----------|
| Sensitive data exposure | Config file permissions 600; key never logged; HTTPS only |
| Injection | No shell execution; file paths are resolved via `pathlib`; text input is passed as-is to the API (the API is responsible for sanitization) |
| Broken authentication | Clear error (exit 2) when key is missing/invalid; no key caching in memory beyond process lifetime |

---

## Deployment & Rollback

### Deployment target

PyPI package. No container, no server, no cloud deployment. Users install via `pip install supertone-cli` or `uv add supertone-cli`.

### Build and publish

```
# Build
uv build

# Publish (CI or manual)
uv publish --token $PYPI_TOKEN
```

### CI/CD pipeline outline

1. **Trigger**: Push to `main` or PR.
2. **Matrix**: Python 3.11, 3.12, 3.13 on Ubuntu and macOS.
3. **Steps**:
   - `uv sync`
   - `uv run ruff check .`
   - `uv run pytest --cov=src --cov-report=term-missing`
   - Assert coverage > 80%
   - (On tag) `uv build && uv publish`

### Rollback procedure

- PyPI supports yanking a release. Publish a new patch version with the fix.
- Users roll back with `pip install supertone-cli==<previous-version>`.
- No database migrations to roll back.

### Database migration rollback

Not applicable. There is no database.

---

## Startup Latency Strategy (NFR-002)

The 500ms startup target requires careful import management.

**Approach**: Lazy imports for all heavy modules.

1. `cli.py` imports only `typer` at module level. Command modules are registered via `app.add_typer()` with callbacks, but the command module bodies are imported only when the specific command is invoked.
2. The `supertone` SDK is imported only inside `client.py` functions, not at module level. This is the heaviest import.
3. `rich` is imported only when output formatting is needed (inside `output.py` functions), not at module level of `cli.py`.
4. Typer's lazy command group loading (via `typer.Typer(invoke_without_command=True)` pattern) ensures only the invoked path is loaded.

**Verification**: CI runs `time supertone --help` as a benchmark step, asserting < 500ms.

---

## Streaming Audio Playback (Risk R-3)

`--stream` requires an audio playback library not in the core dependency list.

**Approach**: `sounddevice` is declared as an optional dependency extra.

```toml
[project.optional-dependencies]
stream = ["sounddevice>=0.4"]
```

- Install: `pip install supertone-cli[stream]`
- When `--stream` is used and `sounddevice` is not installed, exit with code 3 and a message: `Streaming requires the 'stream' extra: pip install supertone-cli[stream]`
- `sounddevice` uses PortAudio (bundled on most platforms via the `sounddevice` wheel). No separate system dependency on macOS/Linux.

---

## What Changes at 10x Scale

The PRD does not indicate multi-user or server deployment, but if usage grows:

| Trigger | Change needed |
|---------|--------------|
| Batch jobs with 1000+ files | Add `--concurrency N` with a `ThreadPoolExecutor` in `commands/tts.py`. Requires API rate limit awareness. |
| Multiple config profiles | Add `--profile` flag and `[profiles.<name>]` sections in config.toml (already scoped for Phase 2). |
| SDK adds new models/params | `client.py` abstraction layer isolates changes. Add new params to the wrapper; CLI flags follow. |
| Streaming to file + playback simultaneously | Already designed (A-8). Implementation writes chunks to both a file handle and the audio device. |

---

## Tradeoffs

| Decision | Chosen | Rejected | Rationale |
|----------|--------|----------|-----------|
| Architecture | Single-process CLI monolith | Plugin architecture with entry points | No extensibility requirement in Phase 1. A plugin system adds discovery overhead and complicates startup latency. Easy to add later via `importlib.metadata` entry points if Phase 2 needs it. |
| CLI framework | Typer | Click (direct), argparse | PRD mandates Typer. Typer provides type-hint-driven API, automatic `--help`, Rich integration. Click is the underlying engine so we get its maturity. argparse would require significantly more boilerplate. |
| Config format | TOML (stdlib `tomllib` + `tomli_w`) | JSON, YAML, INI | PRD specifies TOML. `tomllib` is stdlib in 3.11+ (zero extra deps for reading). `tomli_w` is tiny (single file, no transitive deps). JSON lacks comments; YAML requires `pyyaml`; INI lacks nested structure. |
| SDK abstraction | Thin wrapper in `client.py` | Direct SDK calls in command modules | Isolates SDK surface changes (Risk R-1). All 7 SDK methods are wrapped. Adds one indirection layer but makes mocking trivial for tests and protects commands from SDK API churn. |
| Audio playback dep | Optional extra (`sounddevice`) | Required dependency, or no streaming support | `sounddevice` adds ~5MB to install and requires PortAudio. Most users will not use `--stream`. Optional extra keeps base install minimal (NFR-001). |
| Batch concurrency | Sequential loop (Phase 1) | ThreadPoolExecutor / asyncio | Sequential is simpler, debuggable, and predictable. API rate limits are unknown. Adding concurrency later is straightforward (the batch loop is isolated in one function). |
| TOML write library | `tomli_w` | `tomlkit` (preserves comments/formatting) | `tomli_w` is simpler and has no dependencies. The config file is machine-managed; comment preservation is not needed. `tomlkit` is heavier. |
| Logging | None (stderr messages only) | `logging` module with file handler | CLI is short-lived. Log files add maintenance burden. Users can redirect stderr. Adding `--verbose` with `logging.DEBUG` is a low-effort Phase 2 addition if needed. |
| Config file naming | `config_cmd.py` for the command module | Rename `config.py` to `settings.py` | Keeping `config.py` as the config logic module matches its purpose. The command module gets the suffix to avoid shadowing. This is a minor naming inconvenience but avoids renaming a conceptually clear module. |

---

## Self-Review

### Alternative re-evaluation

1. **Architecture (plugin system instead of monolith)**: A plugin architecture would allow third-party extensions. However, Phase 1 has exactly 4 command groups with fixed functionality. The overhead of entry point discovery, API contracts for plugins, and documentation is not justified. The monolith can be split into a plugin system later without breaking users.

2. **Config format (JSON instead of TOML)**: JSON would eliminate the `tomli_w` dependency entirely (stdlib `json`). However, JSON does not support comments, is less human-readable for config files, and the PRD explicitly specifies TOML. The `tomli_w` cost is minimal (single-file package, no transitive deps).

3. **SDK abstraction (direct calls instead of wrapper)**: Removing `client.py` would eliminate one layer and ~100 lines of code. However, tests would need to mock the SDK at import boundaries scattered across 4 command modules. The wrapper centralizes mocking to one module and isolates Risk R-1. The small code cost is worth the testability and change-isolation benefits.

### NFR coverage check

| NFR | Addressed by |
|-----|-------------|
| NFR-001: Installability | PyPI distribution, minimal deps (supertone, typer, rich, tomli_w), optional extras for stream |
| NFR-002: Startup < 500ms | Lazy import strategy in cli.py; SDK imported only on use; CI benchmark step |
| NFR-003: API key security | Config module enforces 600 perms; env var override; key stripped from error output |
| NFR-004: Test coverage > 80% | pytest + pytest-cov; client.py wrapper enables clean mocking; integration tests separated with `-m integration` |
| NFR-005: Exit code consistency | `errors.py` hierarchy with codes 0/1/2/3; top-level handler in `cli.py` |

No gaps identified.

### Failure mode analysis

| Component | Failure mode | Handling |
|-----------|-------------|----------|
| `config.py` (read) | Config file missing or corrupted TOML | Return empty dict; commands that need config values fall through to error messages with setup instructions |
| `config.py` (write) | Permission denied on `~/.config/supertone/` | Catch `OSError`, exit 1 with message including the path and permission fix |
| `client.py` (API call) | Network timeout / connection refused | Catch `supertone` SDK exceptions, map to `APIError` (exit 1) with message and retry suggestion |
| `client.py` (auth) | Invalid or expired API key | SDK raises auth error, mapped to `AuthError` (exit 2) with message to check key |
| `commands/tts.py` (batch) | One file in batch fails | Default: log error to stderr, continue. `--fail-fast`: stop immediately, exit 1. Summary printed at end. |
| `commands/tts.py` (stream) | `sounddevice` not installed | `ImportError` caught, exit 3 with install instruction |
| `commands/tts.py` (stream) | No audio device available | `sounddevice` raises `PortAudioError`, caught and exit 1 with message |
| `output.py` | Broken pipe (downstream consumer closes) | Catch `BrokenPipeError` in top-level handler, exit 0 silently (Unix convention) |

### Simplicity test

- Could `output.py` be removed? No -- output routing (stderr vs stdout, TTY detection, JSON vs table) is used by every command. Inlining it would duplicate logic.
- Could `errors.py` be removed? Technically yes (use plain `SystemExit`), but the exception hierarchy makes the top-level handler clean and exit codes testable. Keep it.
- Could `client.py` be removed? The system would still work with direct SDK calls, but testability and change isolation would suffer significantly. Keep it (see tradeoff above).
- All modules are load-bearing. Nothing can be removed without violating requirements.

### Confidence rating

**High**. The architecture is a standard CLI application pattern with well-understood components. The tech stack is specified by the PRD. The only uncertainty is the exact Supertone SDK API surface (method signatures, error classes), which is mitigated by the `client.py` wrapper. No architectural decision depends on unknown information.
