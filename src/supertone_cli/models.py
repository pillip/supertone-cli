"""Data models for supertone-cli (frozen dataclasses)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Voice:
    """A voice returned by the API."""

    id: str
    name: str
    type: str  # "preset" or "custom"
    languages: list[str] = field(default_factory=list)
    gender: str | None = None
    age: str | None = None
    use_cases: list[str] | None = None


@dataclass(frozen=True)
class Usage:
    """API usage statistics."""

    plan: str
    used: int
    remaining: int


@dataclass(frozen=True)
class Prediction:
    """TTS duration prediction result."""

    duration_seconds: float
    estimated_credits: int


@dataclass(frozen=True)
class CloneResult:
    """Result from voice cloning."""

    voice_id: str
    name: str


@dataclass(frozen=True)
class TTSResult:
    """Metadata from a TTS generation."""

    output_file: str
    duration_seconds: float
    voice_id: str


@dataclass(frozen=True)
class BatchResult:
    """Summary of a batch TTS run."""

    succeeded: int
    failed: int
    total: int


@dataclass(frozen=True)
class BatchError:
    """Error for a single file in a batch run."""

    file: str
    error: str
