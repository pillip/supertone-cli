# Test Plan -- Supertone CLI Phase 1

## Strategy

### Testing Pyramid

| Level | Ratio | What it covers | Framework |
|-------|-------|----------------|-----------|
| Unit | 60% | Business logic in each module: input resolution, config resolution, parameter validation, error mapping, output formatting | pytest |
| Integration | 30% | Command-level tests via Typer CliRunner: full command execution with mocked SDK, verifying exit codes + stdout/stderr content | pytest + CliRunner |
| E2E (subprocess) | 10% | Critical happy paths executed as real subprocess calls (`subprocess.run`), verifying binary behavior, pipe compatibility, and exit codes | pytest + subprocess |

**Rationale**: This is a CLI monolith with no database, no server, and one external dependency (Supertone SDK). The SDK is always mocked in unit/integration tests. The real risk surface is argument parsing logic, config resolution order, output routing (stdout vs stderr), and exit code correctness -- all best caught at the integration level. E2E subprocess tests cover pipe behavior and TTY detection that CliRunner cannot simulate.

### Test Framework

- **pytest** with `pytest-cov` (team standard)
- **Typer CliRunner** for integration-level command invocation
- **unittest.mock** for SDK mocking (all tests mock `client.py` functions)
- **tmp_path** fixture for config file and output file isolation

### CI Integration

| Trigger | What runs | Timeout |
|---------|-----------|---------|
| Every PR | `uv run pytest -q --cov=src --cov-report=term-missing` (unit + integration, excludes `-m integration`) | 5 min |
| Every PR | `uv run ruff check .` | 1 min |
| Every PR | Startup latency benchmark: `time supertone --help` < 500ms | 30s |
| Nightly | Full suite including `pytest -m integration` (real API, if key available) | 15 min |
| Nightly | Coverage gate: assert > 80% | -- |

---

## Risk Matrix

| Flow | Likelihood of Bug | Impact if Broken | Risk | Coverage Level |
|------|-------------------|------------------|------|----------------|
| TTS input resolution (3 sources, exactly-one) | High | Critical -- core feature fails | **High** | Unit + Integration + E2E |
| Config & API key resolution (env > file > none) | High | Critical -- all commands fail | **High** | Unit + Integration |
| Batch processing (error continuation, fail-fast) | Medium | High -- data loss, silent failures | **High** | Unit + Integration |
| Exit code consistency (0/1/2/3) | Medium | High -- breaks automation pipelines | **High** | Integration + E2E |
| Parameter-model compatibility validation | Medium | Medium -- confusing errors | **Medium** | Unit + Integration |
| Output routing (stdout vs stderr, TTY detection) | Medium | Medium -- breaks pipes | **Medium** | Integration + E2E |
| API key security (600 perms, no leakage) | Low | Critical -- security incident | **High** | Unit + Integration |
| Voice clone format validation | Low | Low -- clear error | **Low** | Unit |
| Voices list/search display | Low | Low -- cosmetic | **Low** | Integration |
| Usage display | Low | Low -- informational | **Low** | Integration |

---

## Critical Flows (ordered by risk)

### Flow: TTS Input Resolution
- Risk level: **High**
- Related requirements: FR-001, US-1, US-2, US-5

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-001 | API key configured, voice set | `supertone tts "Hello"` | `client.create_speech` called with text="Hello", audio file written, exit 0 | Integration |
| TC-002 | File `script.txt` exists with content "Hello" | `supertone tts --input script.txt` | `create_speech` called with text="Hello", exit 0 | Integration |
| TC-003 | stdin piped with "Hello" | `echo "Hello" \| supertone tts` | `create_speech` called with text="Hello", exit 0 | Integration |
| TC-004 | Both positional and --input provided | `supertone tts "Hello" --input script.txt` | stderr contains "Ambiguous input", exit 3 | Integration |
| TC-005 | Both stdin and positional provided | `echo "X" \| supertone tts "Hello"` | stderr contains "Ambiguous input", exit 3 | E2E (subprocess) |
| TC-006 | stdin is TTY, no text, no --input | `supertone tts` (interactive terminal) | stderr contains "No input provided", exit 3 | Integration |
| TC-007 | --input file does not exist | `supertone tts --input missing.txt` | stderr contains "File not found", exit 3 | Integration |
| TC-008 | --input file is empty | `supertone tts --input empty.txt` (0 bytes) | stderr contains "empty", exit 3 | Integration |
| TC-009 | --input file not readable (perms 000) | `supertone tts --input noperm.txt` | stderr contains "Cannot read", exit 3 | Unit |
| TC-010 | Positional text is empty string | `supertone tts ""` | stderr contains "empty", exit 3 | Integration |

---

### Flow: Config and API Key Resolution
- Risk level: **High**
- Related requirements: FR-008, FR-009, NFR-003, US-13, US-14

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-011 | No config file, no env var | `supertone tts "Hello"` | stderr contains "No API key found", exit 2 | Integration |
| TC-012 | `SUPERTONE_API_KEY=sk-test` set, no config | `supertone tts "Hello"` | SDK receives api_key="sk-test" | Unit |
| TC-013 | Config has `api_key=sk-file`, env has `SUPERTONE_API_KEY=sk-env` | `get_api_key()` | Returns "sk-env" (env wins) | Unit |
| TC-014 | Config has `api_key=sk-file`, no env | `get_api_key()` | Returns "sk-file" | Unit |
| TC-015 | None | `config set api_key sk-new` | File written, permissions are 0o600 | Unit |
| TC-016 | Config exists | `config set api_key sk-new` | File updated, permissions remain 0o600 | Unit |
| TC-017 | Config has api_key, default_voice | `config list` | All key-values printed, api_key masked | Integration |
| TC-018 | Config has api_key | `config get api_key` | Full unmasked key printed to stdout | Integration |
| TC-019 | Key "foo" not a valid config key | `config set foo bar` | stderr contains "Unknown config key", exit 3 | Integration |
| TC-020 | No config file | `config get default_voice` | stderr contains "not set", exit 3 | Integration |
| TC-021 | No config file | `config list` | No output, exit 0 | Integration |
| TC-022 | Config dir cannot be created | `config set api_key X` | stderr contains "Cannot create", exit 1 | Unit |

---

### Flow: API Key Security
- Risk level: **High**
- Related requirements: NFR-003

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-023 | API key = "sk-secret-12345" | Trigger every error path (auth fail, API error, input error, network error) | String "sk-secret-12345" does NOT appear in any stderr output | Integration |
| TC-024 | Config written | Check file permissions | `stat` shows 0o600 | Unit |
| TC-025 | Config written, then re-written | Check file permissions after second write | Still 0o600 | Unit |
| TC-026 | SDK raises exception containing API key in message | Top-level handler catches it | API key stripped from stderr output | Unit |

---

### Flow: Batch Processing
- Risk level: **High**
- Related requirements: FR-004, US-7

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-027 | Dir with 3 .txt files, all valid | `tts --input ./scripts/ --outdir ./audio/` | 3 output files created, stderr shows "3 succeeded, 0 failed", exit 0 | Integration |
| TC-028 | Dir with 3 files, 2nd file triggers API error | Same command | Files 1 and 3 succeed, stderr shows "2 succeeded, 1 failed", exit 1 | Integration |
| TC-029 | Same as TC-028 but with `--fail-fast` | Same + `--fail-fast` | Only file 1 succeeds, processing stops at file 2, stderr shows "Stopping", exit 1 | Integration |
| TC-030 | Glob pattern `"scripts/*.txt"` matching 2 files | `tts --input "scripts/*.txt" --outdir ./out/` | 2 output files, exit 0 | Integration |
| TC-031 | --input points to nonexistent directory | `tts --input ./nope/ --outdir ./out/` | stderr contains "Directory not found", exit 3 | Integration |
| TC-032 | Directory exists but has no .txt files | `tts --input ./empty_dir/ --outdir ./out/` | stderr contains "No .txt files found", exit 3 | Integration |
| TC-033 | Glob pattern matches nothing | `tts --input "*.xyz" --outdir ./out/` | stderr contains "No files match", exit 3 | Integration |
| TC-034 | --outdir does not exist | `tts --input ./scripts/ --outdir ./newdir/` | Directory created, files written | Integration |
| TC-035 | --outdir cannot be created (parent perms) | Same with restricted parent | stderr contains "Cannot create output directory", exit 1 | Unit |
| TC-036 | Batch with stdout not TTY | Redirect stdout | Progress bar not in stderr (or only summary), no ANSI in stdout | Integration |

---

### Flow: Exit Code Consistency
- Risk level: **High**
- Related requirements: FR-009, NFR-005

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-037 | Successful TTS | `supertone tts "Hello"` | Exit code 0 | Integration |
| TC-038 | API returns 500 | `supertone tts "Hello"` | Exit code 1 | Integration |
| TC-039 | Invalid API key (401) | `supertone tts "Hello"` | Exit code 2 | Integration |
| TC-040 | Missing required --voice, no default | `supertone tts "Hello"` | Exit code 3 | Integration |
| TC-041 | Unhandled exception in command | Mock raises RuntimeError | Exit code 1 (never 0) | Integration |
| TC-042 | All subcommands success path | Run each: tts, voices list, voices search, voices clone, usage, config set/get/list | All exit 0 | Integration |
| TC-043 | Network unreachable | Mock raises ConnectionError | Exit code 1 | Integration |
| TC-044 | Real subprocess exit codes | `subprocess.run(["supertone", "tts", "hello"])` with no config | Exit code 2 | E2E |

---

### Flow: Parameter-Model Compatibility Validation
- Risk level: **Medium**
- Related requirements: FR-002

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-045 | None | `tts "X" --model sona_speech_2_flash --similarity 0.5` | stderr contains "not supported by model sona_speech_2_flash", exit 3 | Integration |
| TC-046 | None | `tts "X" --model sona_speech_2_flash --text-guidance 0.5` | Same pattern, exit 3 | Integration |
| TC-047 | None | `tts "X" --stream --model sona_speech_2` | stderr contains "only supported with model sona_speech_1", exit 3 | Integration |
| TC-048 | None | `tts "X" --model sona_speech_1 --stream` (sounddevice missing) | stderr contains "pip install supertone-cli[stream]", exit 3 | Unit |
| TC-049 | Valid params for sona_speech_2 | `tts "X" --model sona_speech_2 --speed 1.2 --pitch 0.5` | Parameters forwarded to SDK, exit 0 | Integration |

---

### Flow: Output Routing (stdout vs stderr, TTY detection)
- Risk level: **Medium**
- Related requirements: FR-009, US-6, US-8

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-050 | None | `tts "X" --output -` | Only audio bytes on stdout, metadata on stderr | Integration |
| TC-051 | None | `tts "X" --output - --format json` | stderr contains "Cannot use --format json with --output -", exit 3 | Integration |
| TC-052 | None | `voices list --format json` | stdout is valid JSON array, no table formatting mixed in | Integration |
| TC-053 | None | `usage --format json` | stdout is valid JSON with used/remaining/plan fields | Integration |
| TC-054 | stdout is not TTY | `tts "X"` (piped) | No ANSI codes in output, no progress spinner | E2E (subprocess) |
| TC-055 | None | `voices list` (empty result) | Table headers printed, exit 0 | Integration |
| TC-056 | None | `tts predict "Hello" --format json` | stdout is valid JSON with duration_seconds and estimated_credits | Integration |

---

### Flow: Voice Clone
- Risk level: **Medium**
- Related requirements: FR-007, US-11

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-057 | Valid wav file exists | `voices clone --name "test" --sample ./s.wav` | voice_id printed to stdout, exit 0 | Integration |
| TC-058 | Sample file is .aac (unsupported) | `voices clone --name "test" --sample ./s.aac` | stderr lists supported formats, exit 3, no upload attempted | Integration |
| TC-059 | Sample file does not exist | `voices clone --name "test" --sample ./nope.wav` | stderr "File not found", exit 3 | Integration |
| TC-060 | --name omitted | `voices clone --sample ./s.wav` | stderr "--name is required", exit 3 | Integration |
| TC-061 | API clone fails | Mock returns error | Exit 1, error on stderr | Integration |
| TC-062 | --format json | `voices clone --name "test" --sample ./s.wav --format json` | stdout is JSON with voice_id and name | Integration |

---

### Flow: Voice Search
- Risk level: **Low**
- Related requirements: FR-006, US-10

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-063 | Voices exist matching filters | `voices search --lang ko --gender female` | Filtered results displayed, exit 0 | Integration |
| TC-064 | No filters provided | `voices search` | stderr "Provide at least one filter", exit 3 | Integration |
| TC-065 | No voices match | `voices search --lang xx` | Empty table, stderr hint, exit 0 | Integration |
| TC-066 | Multiple filters (AND) | `voices search --lang ko --age young --use-case narration` | Only voices matching ALL filters returned | Unit |

---

### Flow: Usage Display
- Risk level: **Low**
- Related requirements: FR-010, US-15

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-067 | Valid API key | `supertone usage` | Human-readable plan/used/remaining on stdout, exit 0 | Integration |
| TC-068 | Valid API key | `supertone usage --format json` | Valid JSON with used, remaining, plan fields | Integration |
| TC-069 | API fails | Mock raises API error | Exit 1, error on stderr | Integration |

---

### Flow: TTS Predict
- Risk level: **Low**
- Related requirements: FR-003, US-4

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-070 | Valid API key, voice set | `tts predict "Hello"` | Duration and credit estimate on stdout, exit 0 | Integration |
| TC-071 | None | `tts predict "Hello" --format json` | Valid JSON with duration_seconds and estimated_credits | Integration |
| TC-072 | None | `tts predict --input script.txt` | File contents used for prediction | Integration |
| TC-073 | No input provided | `tts predict` | Same "No input" error as tts command, exit 3 | Integration |

---

### Flow: Config Init (Interactive)
- Risk level: **Medium**
- Related requirements: FR-008, US-13

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-074 | No config file, stdin is TTY | `config init`, provide api_key via mock input | Config file created at correct path with 600 perms | Integration |
| TC-075 | Config file exists with values | `config init`, press Enter on all prompts | Existing values retained | Integration |
| TC-076 | stdin is not TTY (piped) | `echo "" \| supertone config init` | stderr "requires an interactive terminal", exit 3 | Integration |
| TC-077 | User provides empty API key | `config init`, empty input for api_key | Prompt repeats with "API key is required" | Unit |

---

### Flow: Streaming TTS Playback
- Risk level: **Low** (Could priority, optional dep)
- Related requirements: US-3 streaming

#### Test Cases

| ID | Precondition | Action | Expected Result | Type |
|----|-------------|--------|-----------------|------|
| TC-078 | sounddevice installed, model sona_speech_1 | `tts "X" --stream --model sona_speech_1` | Audio chunks played, exit 0 | Integration |
| TC-079 | Model is not sona_speech_1 | `tts "X" --stream --model sona_speech_2` | Exit 3, "only supported with model sona_speech_1" | Integration |
| TC-080 | sounddevice not installed | `tts "X" --stream` | Exit 3, install instruction in stderr | Unit |
| TC-081 | No audio device | Mock sounddevice raises PortAudioError | Exit 1, "No audio output device" | Unit |

---

## E2E Testing Strategy

### Platform Detection

- **Detected platform**: CLI application (Python/Typer)
- **Source**: `docs/architecture.md` -- single-process Python CLI monolith, no web frontend, no mobile app
- **E2E approach**: Subprocess-based testing (`subprocess.run`) to test the installed CLI binary

### CLI E2E

- **Framework**: pytest + `subprocess.run` for true subprocess tests; `typer.testing.CliRunner` for fast integration tests
- **Test location**: `tests/` directory
  - `tests/unit/` -- pure function tests (config, errors, output formatting, validation logic)
  - `tests/integration/` -- CliRunner-based command tests with mocked SDK
  - `tests/e2e/` -- subprocess-based tests against the installed binary
- **CI**: CliRunner integration tests on every PR; subprocess E2E tests on every PR (fast, <10 tests); real-API integration tests nightly
- **Matrix**: Python 3.11, 3.12, 3.13 on Ubuntu + macOS (per architecture CI spec)

### Web E2E / Mobile E2E

Not applicable. This is a CLI-only project.

---

## Backend Robustness

### API Contract Tests

Since Supertone CLI wraps an external SDK (not our own API), contract tests focus on the `client.py` wrapper layer:

- Verify `client.py` functions return expected dict shapes (voice_id, name, duration_seconds, etc.)
- Mock SDK responses with fixture data matching documented response schemas
- If Supertone publishes an OpenAPI spec, use schemathesis against it in nightly runs
- Run on every PR via mocked unit tests; real API validation in nightly integration tests

### Load and Performance

| Scenario | Target | Tool |
|----------|--------|------|
| CLI startup (`supertone --help`) | < 500ms wall-clock p95 | Shell script in CI: 10 runs, assert max < 500ms |
| Batch 100 files (mocked API) | < 30s total, no memory leak | pytest benchmark with mocked `create_speech` |

Load testing of the Supertone API itself is out of scope (external service). The CLI adds negligible overhead.

### Dependency Failure Scenarios

| Dependency | Failure Mode | Expected Behavior |
|------------|-------------|-------------------|
| Supertone API | Connection timeout | Exit 1, message: "Cannot reach the Supertone API. Check your network connection." |
| Supertone API | HTTP 401 Unauthorized | Exit 2, message: "Authentication failed -- check your API key." |
| Supertone API | HTTP 429 Rate Limited | Exit 1, message: "API request failed (429 Too Many Requests). Try again later." |
| Supertone API | HTTP 500 Server Error | Exit 1, message: "API request failed (500). Try again later." |
| Config file | Missing | Commands requiring auth exit 2 with setup instructions; `config list` exits 0 with no output |
| Config file | Corrupted TOML | Exit 1, message: "Cannot parse config file. Run supertone config init to recreate." |
| Config directory | Permission denied | Exit 1, message: "Cannot create config directory -- check permissions." |
| sounddevice | Not installed | Exit 3, message: "Streaming requires the 'stream' extra: pip install supertone-cli[stream]" |
| sounddevice | No audio device | Exit 1, message: "No audio output device found." |
| Filesystem | Output path not writable | Exit 1, message: "Cannot write to <path> -- check directory permissions." |

---

## Edge Cases and Boundary Tests

### Input Boundaries

| Case | Input | Expected |
|------|-------|----------|
| Empty string | `tts ""` | Exit 3, "Text input is empty" |
| Single character | `tts "A"` | Success (API handles it) |
| Very long text (>100KB) | `tts --input huge.txt` | Pass to API; propagate API limit error if any |
| Unicode / Korean | `tts "안녕하세요"` | Success, text passed correctly |
| Special shell characters | `tts "hello & goodbye"` | Text received correctly (shell quoting is user's job) |
| Null bytes in file | `tts --input binary.bin` | API error propagated, or text read handles gracefully |

### Config Boundaries

| Case | Expected |
|------|----------|
| Config value with spaces | `config set default_voice "voice with spaces"` -- stored and retrieved correctly |
| Config value empty string | `config set default_voice ""` -- value set to empty; tts treats as no voice set |
| Very long API key | Stored and retrieved correctly |
| Config file manually edited with extra keys | Extra keys preserved on read; ignored by CLI |

### Batch Boundaries

| Case | Expected |
|------|----------|
| Single file in batch dir | Processes 1 file, summary "1 succeeded, 0 failed" |
| 0 files matching glob | Exit 3 |
| All files fail | Exit 1, summary "0 succeeded, N failed" |
| Output filename collision (same name, different input dirs) | Last one wins or error (define behavior) |

### Concurrent Access

| Case | Expected |
|------|----------|
| Two CLI instances writing config simultaneously | Last write wins; file is valid TOML (atomic write with tmp + rename) |
| Batch processing interrupted (Ctrl+C) | Clean exit, partial output files may exist, no garbled terminal |

### Permission Boundaries

| Case | Expected |
|------|----------|
| Valid API key | All authenticated commands succeed |
| Missing API key | Exit 2 on any authenticated command |
| Invalid API key | Exit 2, "Authentication failed" |
| Expired API key | Exit 2, "Authentication failed" |

---

## Test Data and Fixtures

### Seed Data

| Fixture | Description | Location |
|---------|-------------|----------|
| `sample_config` | Valid config.toml with test api_key, default_voice, default_model, default_lang | `tests/fixtures/config.toml` |
| `sample_text_file` | 3-line English text for TTS input | `tests/fixtures/script.txt` |
| `sample_text_korean` | Korean text for language testing | `tests/fixtures/script_ko.txt` |
| `empty_file` | 0-byte file | Created in-test via `tmp_path` |
| `sample_audio_wav` | Minimal valid WAV header (44 bytes + silence) for clone testing | `tests/fixtures/sample.wav` |
| `sample_audio_unsupported` | A .aac file for format rejection test | `tests/fixtures/sample.aac` |
| `batch_scripts_dir` | Directory with 3 .txt files for batch testing | Created in-test via `tmp_path` |

### Mock Responses

| Mock | Returns |
|------|---------|
| `client.create_speech` | `b'\x00' * 1000` (fake audio bytes) |
| `client.predict_duration` | `{"duration_seconds": 3.2, "estimated_credits": 47}` |
| `client.list_voices` | List of 3 Voice dicts (1 custom, 2 preset, mixed languages) |
| `client.search_voices` | Filtered subset of list_voices based on args |
| `client.clone_voice` | `{"voice_id": "voice_test_123", "name": "test-voice"}` |
| `client.get_usage` | `{"used": 12450, "remaining": 37550, "plan": "Pro"}` |

### Factory Pattern

```python
# tests/conftest.py
@pytest.fixture
def mock_client(monkeypatch):
    """Patches all client.py functions with safe defaults."""
    ...

@pytest.fixture
def config_dir(tmp_path):
    """Creates a temporary config directory with 600 permissions."""
    ...

@pytest.fixture
def cli_runner():
    """Returns a Typer CliRunner instance."""
    return CliRunner()
```

### Sensitive Data Handling

- Test API key is always a dummy: `"sk-test-dummy-key-00000"`
- No real Supertone API keys in test code, fixtures, or CI config
- Real API key for nightly integration tests is injected via CI secret `SUPERTONE_API_KEY`
- TC-023 specifically asserts the dummy key string never appears in any output

---

## Automation Candidates

### CI (every PR)

- Unit tests (`tests/unit/`)
- Integration tests (`tests/integration/`) -- all mocked
- Linting: `ruff check .`
- Coverage gate: > 80%
- Startup latency: `time supertone --help` < 500ms
- E2E subprocess tests (`tests/e2e/`) -- fast, <10 tests

### Nightly

- Integration tests with real API: `pytest -m integration`
- Python version matrix: 3.11, 3.12, 3.13
- OS matrix: Ubuntu + macOS

### Manual Verification

- First-time setup flow (install from PyPI on clean machine, run config init)
- Streaming playback quality (`--stream` with real audio device)
- Accessibility: screen reader compatibility with table output
- Shell compatibility: test glob quoting on zsh vs bash

---

## Visual Regression

Not applicable. This is a CLI tool with no graphical interface. Output formatting consistency is covered by integration test assertions on stdout/stderr content.

---

## Release Checklist (Smoke)

Execute manually in under 5 minutes on a clean environment:

- [ ] `pip install supertone-cli` succeeds on Python 3.11+
- [ ] `supertone --help` displays help and exits in under 1 second
- [ ] `supertone --version` prints the correct version
- [ ] `supertone config set api_key <valid-key>` writes config; `ls -la ~/.config/supertone/config.toml` shows 600 permissions
- [ ] `supertone voices list` displays a table of voices
- [ ] `supertone tts "Hello world" --output /tmp/test.wav` produces an audio file
- [ ] `echo "Piped text" | supertone tts --output -` writes audio bytes to stdout (verify with `| ffprobe -i pipe:0`)
- [ ] `supertone tts "test" --model sona_speech_2_flash --similarity 0.5` exits with code 3 and a clear error
- [ ] `supertone usage` displays credit information
- [ ] Running any command without API key configured exits with code 2 and a helpful message
