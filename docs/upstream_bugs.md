# Upstream SDK Bugs

Tracking known bugs in the `supertone` SDK that require workarounds in `supertone-cli`.

---

## list_custom_voices Pydantic ValidationError

- **SDK Version**: supertone==0.2.0
- **Observed**: 2026-04-03
- **Status**: Open (workaround in place)
- **Tracker**: ISSUE-024

### Description

The SDK's `custom_voices.list_custom_voices()` method fails with a Pydantic `ValidationError` because the response model requires a `description` field that the live API (`GET /v1/custom-voices`) does not return.

### Minimal Repro

```python
from supertone import Supertone

client = Supertone(api_key="<valid_key>")
# This raises pydantic.ValidationError:
# "1 validation error for CustomVoice
#  description
#    field required (type=value_error.missing)"
voices = client.custom_voices.list_custom_voices()
```

### Workaround

`supertone-cli` bypasses the SDK and calls the REST API directly via `httpx`:

```python
import httpx
resp = httpx.get(
    f"{base_url}/v1/custom-voices",
    headers={"x-sup-api-key": api_key},
)
```

See `src/supertone_cli/client.py:list_custom_voices()` — marked with `WORKAROUND(ISSUE-024)`.

### Resolution

Remove the workaround when the upstream SDK ships a fix (expected in supertone > 0.2.x). The fix should either make the `description` field optional in the Pydantic model or ensure the API always returns it.
