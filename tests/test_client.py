"""Tests for SDK client wrapper and data models."""

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, patch

import pytest

from supertone_cli.errors import APIError, AuthError

# ── Data model tests ─────────────────────────────────────────────────


def test_voice_is_frozen_dataclass():
    from supertone_cli.models import Voice

    v = Voice(
        id="v1",
        name="Test Voice",
        type="preset",
        languages=["ko", "en"],
        gender="female",
        age="young",
        use_cases=["narration"],
    )
    assert v.id == "v1"
    assert v.type == "preset"
    with pytest.raises(FrozenInstanceError):
        v.id = "v2"


def test_usage_is_frozen_dataclass():
    from supertone_cli.models import Usage

    u = Usage(plan="pro", used=100, remaining=900)
    assert u.plan == "pro"
    with pytest.raises(FrozenInstanceError):
        u.plan = "free"


def test_prediction_dataclass():
    from supertone_cli.models import Prediction

    p = Prediction(duration_seconds=3.2, estimated_credits=47)
    assert p.duration_seconds == 3.2


def test_clone_result_dataclass():
    from supertone_cli.models import CloneResult

    c = CloneResult(voice_id="clone-1", name="my-voice")
    assert c.voice_id == "clone-1"


def test_tts_result_dataclass():
    from supertone_cli.models import TTSResult

    t = TTSResult(
        output_file="out.wav",
        duration_seconds=2.5,
        voice_id="v1",
    )
    assert t.output_file == "out.wav"


def test_batch_result_dataclass():
    from supertone_cli.models import BatchResult

    b = BatchResult(succeeded=3, failed=1, total=4)
    assert b.total == 4


def test_batch_error_dataclass():
    from supertone_cli.models import BatchError

    e = BatchError(file="a.txt", error="API timeout")
    assert e.file == "a.txt"


# ── Client tests ─────────────────────────────────────────────────────


def test_get_client_with_no_api_key_raises_auth_error():
    from supertone_cli.client import get_client

    with (
        patch("supertone_cli.client._client", None),
        patch(
            "supertone_cli.client.get_api_key",
            return_value=None,
        ),
    ):
        with pytest.raises(AuthError):
            get_client()


def test_get_client_with_api_key_returns_client():
    from supertone_cli.client import get_client

    mock_sdk = MagicMock()
    mock_client = MagicMock()
    mock_sdk.Supertone.return_value = mock_client

    with (
        patch("supertone_cli.client._client", None),
        patch(
            "supertone_cli.client.get_api_key",
            return_value="sk-test",
        ),
        patch.dict("sys.modules", {"supertone": mock_sdk}),
    ):
        client = get_client()
        assert client is mock_client


def test_create_speech_returns_bytes():
    from supertone_cli.client import create_speech

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.result = b"audio-bytes"
    mock_client.text_to_speech.create_speech.return_value = mock_response

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        result = create_speech("Hello", "v1", "sona_speech_2", "ko")
        assert result == b"audio-bytes"


def test_create_speech_auth_error():
    from supertone_cli.client import create_speech

    mock_client = MagicMock()
    mock_client.text_to_speech.create_speech.side_effect = Exception("unauthorized")

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        with pytest.raises(AuthError):
            create_speech("Hello", "v1", "sona_speech_2", "ko")


def test_create_speech_api_error():
    from supertone_cli.client import create_speech

    mock_client = MagicMock()
    mock_client.text_to_speech.create_speech.side_effect = Exception("server error")

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        with pytest.raises(APIError):
            create_speech("Hello", "v1", "sona_speech_2", "ko")


def test_list_voices_returns_voice_list():
    from supertone_cli.client import list_voices
    from supertone_cli.models import Voice

    mock_client = MagicMock()
    mock_voice = MagicMock()
    mock_voice.voice_id = "v1"
    mock_voice.name = "Voice1"
    mock_voice.language = "ko"
    mock_voice.gender = "male"
    mock_voice.age = None
    mock_voice.use_cases = []

    mock_response = MagicMock()
    mock_response.items = [mock_voice]
    mock_client.voices.list_voices.return_value = mock_response

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        voices = list_voices()
        assert len(voices) == 1
        assert isinstance(voices[0], Voice)
        assert voices[0].id == "v1"


def test_predict_duration_returns_prediction():
    from supertone_cli.client import predict_duration
    from supertone_cli.models import Prediction

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.duration = 3.2
    mock_client.text_to_speech.predict_duration.return_value = mock_response

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        pred = predict_duration("Hello", "v1", "sona_speech_2", "ko")
        assert isinstance(pred, Prediction)
        assert pred.duration_seconds == 3.2


def test_clone_voice_returns_clone_result():
    import tempfile

    from supertone_cli.client import clone_voice
    from supertone_cli.models import CloneResult

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.voice_id = "clone-1"
    mock_client.custom_voices.create_cloned_voice.return_value = mock_response

    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        f.write(b"fake-audio")
        f.flush()

        with patch(
            "supertone_cli.client.get_client",
            return_value=mock_client,
        ):
            result = clone_voice("my-voice", f.name)
            assert isinstance(result, CloneResult)
            assert result.voice_id == "clone-1"


def test_get_usage_returns_usage():
    from supertone_cli.client import get_usage
    from supertone_cli.models import Usage

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.balance = 900
    mock_client.usage.get_credit_balance.return_value = mock_response

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        usage = get_usage()
        assert isinstance(usage, Usage)
        assert usage.remaining == 900
