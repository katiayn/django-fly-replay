import json
import os
import urllib.error
import urllib.request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django_fly_replay.exceptions import FlyApiError

_BASE_URL = "https://api.machines.dev/v1"


def _get_setting(name: str, default: str | None = None) -> str:
    value = getattr(settings, name, None) or os.environ.get(name) or default
    if value is None:
        raise ImproperlyConfigured(
            f"Set {name} in Django settings or as an environment variable."
        )
    return value


def _get_app_name() -> str:
    return _get_setting("FLY_APP_NAME")


def _get_api_token() -> str:
    return _get_setting("FLY_API_TOKEN")


def _get_timeout() -> int:
    return int(_get_setting("FLY_API_TIMEOUT", default="10"))


def _api_request(
    method: str, path: str, body: dict | None = None, timeout: int | None = None
) -> dict | list | None:
    app_name = _get_app_name()
    token = _get_api_token()
    timeout = timeout if timeout is not None else _get_timeout()

    url = f"{_BASE_URL}/apps/{app_name}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None

    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            if not raw:
                return None
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise FlyApiError(exc.code, url, body_text) from exc
