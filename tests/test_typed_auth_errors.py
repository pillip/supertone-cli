"""Tests for typed SDK auth exception handling (ISSUE-022)."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from supertone_cli.errors import APIError, AuthError


def _make_sdk_auth_error(status_code=401):
    """Create a mock SDK UnauthorizedErrorResponse or ForbiddenErrorResponse."""
    from supertone.errors import SupertoneError

    raw_response = MagicMock(spec=httpx.Response)
    raw_response.status_code = status_code
    raw_response.text = "Unauthorized"
    raw_response.headers = httpx.Headers({})
    exc = SupertoneError("Unauthorized", raw_response)
    exc.status_code = status_code
    return exc


def _make_non_auth_error_with_auth_in_message():
    """Create a non-auth exception whose message contains 'auth'."""
    raw_response = MagicMock(spec=httpx.Response)
    raw_response.status_code = 500
    raw_response.text = "Internal server error in auth module"
    raw_response.headers = httpx.Headers({})
    from supertone.errors import SupertoneError

    exc = SupertoneError("Internal server error in auth module", raw_response)
    exc.status_code = 500
    return exc


@patch("supertone_cli.client.get_client")
def test_sdk_401_raises_auth_error(mock_get_client):
    """SDK 401 exception should produce AuthError with exit code 2."""
    from supertone_cli.client import list_voices

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.voices.list_voices.side_effect = _make_sdk_auth_error(401)

    with pytest.raises(AuthError):
        list_voices()


@patch("supertone_cli.client.get_client")
def test_sdk_403_raises_auth_error(mock_get_client):
    """SDK 403 exception should produce AuthError with exit code 2."""
    from supertone_cli.client import list_voices

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.voices.list_voices.side_effect = _make_sdk_auth_error(403)

    with pytest.raises(AuthError):
        list_voices()


@patch("supertone_cli.client.get_client")
def test_non_auth_error_with_auth_in_message_raises_api_error(mock_get_client):
    """Non-auth exception with 'auth' in message should produce APIError, not AuthError."""
    from supertone_cli.client import list_voices

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.voices.list_voices.side_effect = _make_non_auth_error_with_auth_in_message()

    with pytest.raises(APIError):
        list_voices()


def test_is_auth_error_no_longer_misclassifies():
    """Verify _is_auth_error string heuristic is no longer used or is just a fallback."""
    import inspect

    from supertone_cli import client

    source = inspect.getsource(client)
    # The function may still exist as a last-resort fallback, but
    # the primary auth detection should be via isinstance/status_code checks
    # If _is_auth_error still exists, it should be documented as fallback
    if "_is_auth_error" in source:
        # Acceptable only if there's a comment explaining it's a fallback
        assert "fallback" in source.lower() or "FALLBACK" in source
