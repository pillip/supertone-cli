"""TTS command: text-to-speech generation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from supertone_cli.client import create_speech
from supertone_cli.config import get_default
from supertone_cli.errors import InputError
from supertone_cli.output import print_json

tts_app = typer.Typer(
    name="tts",
    help="Text-to-speech commands.",
)

VALID_MODELS = {
    "sona_speech_1",
    "supertonic_api_1",
    "sona_speech_2",
    "sona_speech_2_flash",
}

# Model-parameter compatibility matrix
_FLASH_DISALLOWED = {"similarity", "text_guidance"}
_SUPERTONIC_ALLOWED = {"speed"}
_STREAM_MODELS = {"sona_speech_1"}


def validate_params(model: str, **kwargs: object) -> None:
    """Validate model-parameter compatibility."""
    if model not in VALID_MODELS:
        valid = ", ".join(sorted(VALID_MODELS))
        raise InputError(f"Unknown model: {model}. Valid models: {valid}")

    # Filter to only provided (non-None) params
    params = {k: v for k, v in kwargs.items() if v is not None}

    if model == "sona_speech_2_flash":
        bad = set(params) & _FLASH_DISALLOWED
        if bad:
            raise InputError(
                f"Parameters not supported by {model}: {', '.join(sorted(bad))}"
            )

    if model == "supertonic_api_1":
        bad = set(params) - _SUPERTONIC_ALLOWED - {"stream"}
        if bad:
            raise InputError(
                f"Parameters not supported by {model}: "
                f"{', '.join(sorted(bad))}. "
                f"Only speed is supported."
            )

    if params.get("stream") and model not in _STREAM_MODELS:
        raise InputError(f"Streaming requires sona_speech_1, but model is {model}.")


def _resolve_text(
    text: str | None,
    input_path: str | None,
) -> str:
    """Resolve input text from positional arg, file, or stdin."""
    sources = []
    if text:
        sources.append("positional")
    if input_path:
        sources.append("--input")

    stdin_has_data = not sys.stdin.isatty()

    if stdin_has_data and not sources:
        content = sys.stdin.read().strip()
        if not content:
            raise InputError("stdin is empty.")
        return content

    if len(sources) > 1:
        raise InputError("Ambiguous input: provide text OR --input, not both.")

    if not sources and not stdin_has_data:
        raise InputError(
            "No input provided. Pass text as argument, "
            "use --input <file>, or pipe via stdin."
        )

    if text:
        return text

    p = Path(input_path)  # type: ignore[arg-type]
    if not p.exists():
        raise InputError(f"File not found: {input_path}")
    content = p.read_text(encoding="utf-8").strip()
    if not content:
        raise InputError(f"File is empty: {input_path}")
    return content


def _run_tts(
    text: str | None,
    input: str | None,
    output: str | None,
    output_format: str,
    voice: str | None,
    model: str | None,
    lang: str | None,
    format: str,
) -> None:
    """Core TTS logic shared by the command."""
    resolved_voice = voice or get_default("default_voice")
    if not resolved_voice:
        raise InputError(
            "No voice specified. Use --voice <id> or "
            "set a default: supertone config set default_voice <id>"
        )

    resolved_model = model or get_default("default_model") or "sona_speech_2"
    resolved_lang = lang or get_default("default_lang") or "ko"

    if format == "json" and output == "-":
        raise InputError(
            "Cannot use --format json with --output -: both write to stdout."
        )

    resolved_text = _resolve_text(text, input)

    if output == "-":
        out_path = None
    elif output:
        out_path = Path(output)
    else:
        out_path = Path(f"output.{output_format}")

    audio_bytes = create_speech(
        text=resolved_text,
        voice=resolved_voice,
        model=resolved_model,
        lang=resolved_lang,
        output_format=output_format,
    )

    if out_path is None:
        sys.stdout.buffer.write(audio_bytes)
    else:
        out_path.write_bytes(audio_bytes)

    if format == "json":
        print_json(
            {
                "output_file": str(out_path) if out_path else "-",
                "voice_id": resolved_voice,
                "model": resolved_model,
                "lang": resolved_lang,
                "output_format": output_format,
            }
        )


def register_tts_command(app: typer.Typer) -> None:
    """Register TTS command directly on the main app."""

    @app.command("tts")
    def tts_cmd(
        text: Optional[str] = typer.Argument(None, help="Text to synthesize."),
        input: Optional[str] = typer.Option(
            None, "--input", "-i", help="Path to text file."
        ),
        output: Optional[str] = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file path. Use '-' for stdout.",
        ),
        output_format: str = typer.Option(
            "wav",
            "--output-format",
            help="Audio format (wav, mp3, ogg, flac).",
        ),
        voice: Optional[str] = typer.Option(None, "--voice", "-v", help="Voice ID."),
        model: Optional[str] = typer.Option(None, "--model", "-m", help="TTS model."),
        lang: Optional[str] = typer.Option(None, "--lang", "-l", help="Language code."),
        format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: text or json.",
        ),
    ) -> None:
        """Generate speech from text."""
        _run_tts(
            text,
            input,
            output,
            output_format,
            voice,
            model,
            lang,
            format,
        )


def register_predict_command(app: typer.Typer) -> None:
    """Register TTS predict command on the main app."""
    from dataclasses import asdict

    @app.command("tts-predict")
    def predict_cmd(
        text: Optional[str] = typer.Argument(
            None, help="Text to predict duration for."
        ),
        input: Optional[str] = typer.Option(
            None, "--input", "-i", help="Path to text file."
        ),
        voice: Optional[str] = typer.Option(None, "--voice", "-v", help="Voice ID."),
        model: Optional[str] = typer.Option(None, "--model", "-m", help="TTS model."),
        lang: Optional[str] = typer.Option(None, "--lang", "-l", help="Language code."),
        format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: text or json.",
        ),
    ) -> None:
        """Predict audio duration without generating."""
        import supertone_cli.client as _client

        resolved_voice = voice or get_default("default_voice")
        if not resolved_voice:
            raise InputError(
                "No voice specified. Use --voice <id> or "
                "set a default: supertone config set default_voice <id>"
            )

        resolved_model = model or get_default("default_model") or "sona_speech_2"
        resolved_lang = lang or get_default("default_lang") or "ko"

        resolved_text = _resolve_text(text, input)

        prediction = _client.predict_duration(
            resolved_text,
            resolved_voice,
            resolved_model,
            resolved_lang,
        )

        if format == "json":
            print_json(asdict(prediction))
            return

        typer.echo(
            f"Duration: {prediction.duration_seconds}s | "
            f"Estimated credits: {prediction.estimated_credits}"
        )
