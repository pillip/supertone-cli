# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-11

### Added

- `tts` command for single text-to-speech generation with voice, model, language, and output format options
- `tts --batch` mode for processing multiple texts from a JSONL file
- `tts-predict` command to estimate audio duration without generating speech
- `tts --stream` flag for real-time streaming TTS playback via sounddevice
- `voices list` subcommand to display all available preset and custom voices
- `voices search` subcommand with filters for language, gender, age, and use case
- `voices clone` subcommand to create a custom voice from an audio sample
- `usage` command to check API credit balance and usage analytics
- `config` command to manage API key and default settings via TOML config file
- Rich-formatted table and JSON output modes (`--json` flag)
- Unix pipe-friendly design: stdin input, stdout output, proper exit codes
- Lazy imports for fast CLI startup (~50ms target)
- CI pipeline with GitHub Actions (lint + test + coverage gate at 80%)

[0.1.0]: https://github.com/pillip/supertone-cli/releases/tag/v0.1.0
