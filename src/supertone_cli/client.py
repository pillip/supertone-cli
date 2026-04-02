"""SDK client wrapper — the ONLY module that imports supertone.

All SDK calls go through this module. SDK exceptions are translated
into CLI-friendly errors (AuthError, APIError).
"""

from __future__ import annotations

from typing import Any, Iterator

from supertone_cli.config import get_api_key
from supertone_cli.errors import APIError, AuthError
from supertone_cli.models import (
    CloneResult,
    Prediction,
    Usage,
    Voice,
)

_client: Any = None


def _is_auth_error(exc: Exception) -> bool:
    """Heuristic: detect authentication errors from SDK exceptions."""
    msg = str(exc).lower()
    return any(kw in msg for kw in ("auth", "unauthorized", "forbidden", "invalid key"))


def get_client() -> Any:
    """Return the SDK client singleton (lazy-initialized)."""
    global _client  # noqa: PLW0603
    if _client is not None:
        return _client

    key = get_api_key()
    if not key:
        raise AuthError(
            "API key not configured. Run: supertone config set api_key <key>"
        )

    # Lazy import — SDK loaded only when needed (startup perf).
    import supertone  # type: ignore[import-untyped]

    _client = supertone.Client(api_key=key)
    return _client


# ── SDK operation wrappers ───────────────────────────────────────────


def create_speech(
    text: str,
    voice: str,
    model: str,
    lang: str,
    **params: Any,
) -> bytes:
    """Generate speech audio bytes."""
    client = get_client()
    try:
        return client.tts.create(
            text=text,
            voice=voice,
            model=model,
            lang=lang,
            **params,
        )
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def stream_speech(
    text: str,
    voice: str,
    model: str,
    lang: str,
    **params: Any,
) -> Iterator[bytes]:
    """Stream speech audio chunks."""
    client = get_client()
    try:
        yield from client.tts.stream(
            text=text,
            voice=voice,
            model=model,
            lang=lang,
            **params,
        )
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def predict_duration(
    text: str,
    voice: str,
    model: str,
    lang: str,
) -> Prediction:
    """Predict audio duration without generating."""
    client = get_client()
    try:
        data = client.tts.predict(text=text, voice=voice, model=model, lang=lang)
        return Prediction(
            duration_seconds=data["duration_seconds"],
            estimated_credits=data["estimated_credits"],
        )
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def list_voices() -> list[Voice]:
    """List all available voices."""
    client = get_client()
    try:
        raw = client.voices.list()
        return [
            Voice(
                id=v["id"],
                name=v["name"],
                type=v["type"],
                languages=v.get("languages", []),
                gender=v.get("gender"),
                age=v.get("age"),
                use_cases=v.get("use_cases", []),
            )
            for v in raw
        ]
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def search_voices(**filters: Any) -> list[Voice]:
    """Search voices with filters."""
    client = get_client()
    try:
        raw = client.voices.search(**filters)
        return [
            Voice(
                id=v["id"],
                name=v["name"],
                type=v["type"],
                languages=v.get("languages", []),
                gender=v.get("gender"),
                age=v.get("age"),
                use_cases=v.get("use_cases", []),
            )
            for v in raw
        ]
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def clone_voice(name: str, sample_path: str) -> CloneResult:
    """Clone a voice from an audio sample."""
    client = get_client()
    try:
        data = client.voices.clone(name=name, sample=sample_path)
        return CloneResult(
            voice_id=data["voice_id"],
            name=data["name"],
        )
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def get_usage() -> Usage:
    """Get API usage statistics."""
    client = get_client()
    try:
        data = client.usage.get()
        return Usage(
            plan=data["plan"],
            used=data["used"],
            remaining=data["remaining"],
        )
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc
